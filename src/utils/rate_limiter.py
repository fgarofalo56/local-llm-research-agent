"""
Rate Limiter

Implements token bucket rate limiting for LLM API calls.
Helps prevent overloading local LLM providers and manage resource usage.
"""

import asyncio
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from functools import wraps
from typing import Any, TypeVar

from src.utils.config import settings
from src.utils.logger import get_logger

logger = get_logger(__name__)

T = TypeVar("T")


@dataclass
class RateLimitStats:
    """Statistics for rate limiting."""

    total_requests: int = 0
    throttled_requests: int = 0
    total_wait_time_ms: float = 0
    max_wait_time_ms: float = 0
    window_start: float = field(default_factory=time.time)

    def record_throttle(self, wait_time_ms: float) -> None:
        """Record a throttled request."""
        self.throttled_requests += 1
        self.total_wait_time_ms += wait_time_ms
        self.max_wait_time_ms = max(self.max_wait_time_ms, wait_time_ms)

    def record_request(self) -> None:
        """Record a request."""
        self.total_requests += 1

    def reset(self) -> None:
        """Reset statistics."""
        self.total_requests = 0
        self.throttled_requests = 0
        self.total_wait_time_ms = 0
        self.max_wait_time_ms = 0
        self.window_start = time.time()

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        avg_wait = (
            self.total_wait_time_ms / self.throttled_requests
            if self.throttled_requests > 0
            else 0
        )
        throttle_rate = (
            (self.throttled_requests / self.total_requests * 100)
            if self.total_requests > 0
            else 0
        )
        return {
            "total_requests": self.total_requests,
            "throttled_requests": self.throttled_requests,
            "throttle_rate": f"{throttle_rate:.1f}%",
            "avg_wait_time_ms": round(avg_wait, 2),
            "max_wait_time_ms": round(self.max_wait_time_ms, 2),
            "window_duration_s": round(time.time() - self.window_start, 2),
        }


class TokenBucketRateLimiter:
    """
    Token bucket rate limiter for controlling request rates.

    The token bucket algorithm allows for bursts while maintaining
    an average rate limit over time.

    Attributes:
        max_tokens: Maximum tokens in the bucket (burst capacity)
        refill_rate: Tokens added per second
        tokens: Current available tokens
    """

    def __init__(
        self,
        requests_per_minute: int = 60,
        burst_capacity: int | None = None,
        enabled: bool = True,
    ):
        """
        Initialize the rate limiter.

        Args:
            requests_per_minute: Target requests per minute
            burst_capacity: Maximum burst size (defaults to rpm / 6)
            enabled: Whether rate limiting is active
        """
        self.enabled = enabled
        self.requests_per_minute = requests_per_minute

        # Calculate token bucket parameters
        self.refill_rate = requests_per_minute / 60.0  # tokens per second
        self.max_tokens = burst_capacity or max(1, requests_per_minute // 6)
        self.tokens = float(self.max_tokens)

        self._last_refill = time.monotonic()
        self._lock = asyncio.Lock()
        self._stats = RateLimitStats()

        logger.info(
            "rate_limiter_initialized",
            rpm=requests_per_minute,
            burst=self.max_tokens,
            enabled=enabled,
        )

    def _refill(self) -> None:
        """Refill tokens based on elapsed time."""
        now = time.monotonic()
        elapsed = now - self._last_refill
        self._last_refill = now

        self.tokens = min(self.max_tokens, self.tokens + elapsed * self.refill_rate)

    async def acquire(self, timeout: float | None = None) -> bool:
        """
        Acquire permission to make a request.

        Args:
            timeout: Maximum time to wait (None = wait indefinitely)

        Returns:
            True if permission granted, False if timeout exceeded
        """
        if not self.enabled:
            self._stats.record_request()
            return True

        start_time = time.monotonic()

        async with self._lock:
            while True:
                self._refill()

                if self.tokens >= 1:
                    self.tokens -= 1
                    self._stats.record_request()
                    return True

                # Calculate wait time for next token
                wait_time = (1 - self.tokens) / self.refill_rate

                # Check timeout
                if timeout is not None:
                    elapsed = time.monotonic() - start_time
                    if elapsed + wait_time > timeout:
                        return False

                # Wait for token
                wait_ms = wait_time * 1000
                self._stats.record_throttle(wait_ms)

                logger.debug(
                    "rate_limit_throttle",
                    wait_time_ms=round(wait_ms, 2),
                    tokens=round(self.tokens, 2),
                )

                await asyncio.sleep(wait_time)

    def try_acquire(self) -> bool:
        """
        Try to acquire permission without waiting.

        Returns:
            True if permission granted immediately
        """
        if not self.enabled:
            self._stats.record_request()
            return True

        self._refill()

        if self.tokens >= 1:
            self.tokens -= 1
            self._stats.record_request()
            return True

        return False

    @property
    def available_tokens(self) -> float:
        """Get current available tokens."""
        self._refill()
        return self.tokens

    def get_stats(self) -> RateLimitStats:
        """Get rate limiting statistics."""
        return self._stats

    def reset_stats(self) -> None:
        """Reset statistics."""
        self._stats.reset()


# Global rate limiter instance
_rate_limiter: TokenBucketRateLimiter | None = None


def get_rate_limiter(
    requests_per_minute: int | None = None,
    enabled: bool | None = None,
) -> TokenBucketRateLimiter:
    """
    Get or create the global rate limiter.

    Args:
        requests_per_minute: Requests per minute limit
        enabled: Whether rate limiting is enabled

    Returns:
        TokenBucketRateLimiter instance
    """
    global _rate_limiter

    if _rate_limiter is None:
        rpm = requests_per_minute or getattr(settings, "rate_limit_rpm", 60)
        is_enabled = enabled if enabled is not None else getattr(
            settings, "rate_limit_enabled", False
        )
        _rate_limiter = TokenBucketRateLimiter(
            requests_per_minute=rpm,
            enabled=is_enabled,
        )

    return _rate_limiter


def rate_limited(
    func: Callable[..., T] | None = None,
    timeout: float | None = None,
) -> Callable[..., T]:
    """
    Decorator to apply rate limiting to async functions.

    Args:
        func: Function to decorate
        timeout: Maximum wait time for rate limit

    Returns:
        Decorated function

    Example:
        @rate_limited
        async def call_llm(message: str) -> str:
            ...

        @rate_limited(timeout=5.0)
        async def call_llm_with_timeout(message: str) -> str:
            ...
    """
    def decorator(fn: Callable[..., T]) -> Callable[..., T]:
        @wraps(fn)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            limiter = get_rate_limiter()
            await limiter.acquire(timeout=timeout)
            return await fn(*args, **kwargs)
        return wrapper

    if func is not None:
        return decorator(func)
    return decorator


class RateLimitExceededError(Exception):
    """Raised when rate limit is exceeded and timeout expires."""

    pass


async def with_rate_limit(
    coro: Any,
    timeout: float | None = None,
    raise_on_timeout: bool = False,
) -> Any:
    """
    Execute a coroutine with rate limiting.

    Args:
        coro: Coroutine to execute
        timeout: Maximum wait time
        raise_on_timeout: Raise exception if timeout exceeded

    Returns:
        Result of the coroutine

    Raises:
        RateLimitExceededError: If timeout exceeded and raise_on_timeout is True
    """
    limiter = get_rate_limiter()

    acquired = await limiter.acquire(timeout=timeout)
    if not acquired:
        if raise_on_timeout:
            raise RateLimitExceededError("Rate limit timeout exceeded")
        # Still execute if not raising
        logger.warning("rate_limit_timeout_exceeded")

    return await coro
