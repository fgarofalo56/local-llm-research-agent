"""
Retry Utilities with Exponential Backoff

Provides retry mechanisms for handling transient failures in agent operations
and provider communications. Includes circuit breaker pattern to prevent
cascading failures.
"""

import asyncio
import random
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from functools import wraps
from typing import Any, TypeVar

import httpx

from src.utils.logger import get_logger

logger = get_logger(__name__)

T = TypeVar("T")


class CircuitState(str, Enum):
    """Circuit breaker states."""

    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if service recovered


@dataclass
class RetryConfig:
    """Configuration for retry behavior."""

    max_retries: int = 3
    initial_delay: float = 1.0
    max_delay: float = 30.0
    multiplier: float = 2.0
    jitter: float = 0.1

    def __post_init__(self):
        """Validate configuration."""
        if self.max_retries < 0:
            raise ValueError("max_retries must be non-negative")
        if self.initial_delay <= 0:
            raise ValueError("initial_delay must be positive")
        if self.max_delay < self.initial_delay:
            raise ValueError("max_delay must be >= initial_delay")
        if self.multiplier < 1:
            raise ValueError("multiplier must be >= 1")
        if self.jitter < 0 or self.jitter > 1:
            raise ValueError("jitter must be between 0 and 1")


@dataclass
class RetryStats:
    """Statistics for retry operations."""

    total_attempts: int = 0
    successful_retries: int = 0
    failed_after_retries: int = 0
    total_delay_ms: float = 0
    max_delay_ms: float = 0

    def record_attempt(self) -> None:
        """Record a retry attempt."""
        self.total_attempts += 1

    def record_success(self) -> None:
        """Record a successful retry."""
        self.successful_retries += 1

    def record_failure(self) -> None:
        """Record a failure after all retries."""
        self.failed_after_retries += 1

    def record_delay(self, delay_ms: float) -> None:
        """Record retry delay."""
        self.total_delay_ms += delay_ms
        self.max_delay_ms = max(self.max_delay_ms, delay_ms)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        avg_delay = (
            self.total_delay_ms / self.total_attempts if self.total_attempts > 0 else 0
        )
        success_rate = (
            (self.successful_retries / self.total_attempts * 100)
            if self.total_attempts > 0
            else 0
        )
        return {
            "total_attempts": self.total_attempts,
            "successful_retries": self.successful_retries,
            "failed_after_retries": self.failed_after_retries,
            "success_rate": f"{success_rate:.1f}%",
            "avg_delay_ms": round(avg_delay, 2),
            "max_delay_ms": round(self.max_delay_ms, 2),
        }


@dataclass
class CircuitBreakerStats:
    """Statistics for circuit breaker."""

    failure_count: int = 0
    success_count: int = 0
    state_changes: int = 0
    last_failure_time: float | None = None
    last_state_change: float = field(default_factory=time.time)

    def record_failure(self) -> None:
        """Record a failure."""
        self.failure_count += 1
        self.last_failure_time = time.time()

    def record_success(self) -> None:
        """Record a success."""
        self.success_count += 1

    def record_state_change(self) -> None:
        """Record a state transition."""
        self.state_changes += 1
        self.last_state_change = time.time()

    def reset_failures(self) -> None:
        """Reset failure count."""
        self.failure_count = 0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "state_changes": self.state_changes,
            "last_failure_time": self.last_failure_time,
            "time_since_state_change_s": round(time.time() - self.last_state_change, 2),
        }


def is_retriable_error(error: Exception) -> bool:
    """
    Determine if an error is retriable (transient).

    Retriable errors include:
    - Network timeouts
    - Connection errors
    - HTTP 429 (rate limit)
    - HTTP 502 (bad gateway)
    - HTTP 503 (service unavailable)

    Non-retriable errors (fail immediately):
    - HTTP 400 (bad request)
    - HTTP 401 (unauthorized)
    - HTTP 403 (forbidden)
    - HTTP 404 (not found)
    - Validation errors

    Args:
        error: Exception to check

    Returns:
        True if error should be retried
    """
    # Timeout errors - always retriable
    if isinstance(error, (asyncio.TimeoutError, TimeoutError)):
        return True

    # Connection errors - always retriable
    if isinstance(error, (ConnectionError, ConnectionRefusedError, ConnectionResetError)):
        return True

    # HTTPX errors
    if isinstance(error, httpx.TimeoutException):
        return True

    if isinstance(error, httpx.ConnectError):
        return True

    if isinstance(error, httpx.RemoteProtocolError):
        return True

    if isinstance(error, httpx.HTTPStatusError):
        # Retriable HTTP status codes
        retriable_statuses = {429, 502, 503, 504}
        return error.response.status_code in retriable_statuses

    # OSError and subclasses (BrokenPipeError, etc.)
    if isinstance(error, OSError):
        return True

    # Default: non-retriable
    return False


class CircuitBreaker:
    """
    Circuit breaker pattern implementation.

    Prevents cascading failures by opening the circuit after a threshold
    of consecutive failures. Periodically tests if the service has recovered.

    States:
    - CLOSED: Normal operation, all requests pass through
    - OPEN: Service is failing, reject requests immediately
    - HALF_OPEN: Testing if service recovered, allow limited requests

    Attributes:
        threshold: Number of failures before opening circuit
        reset_timeout: Seconds to wait before trying half-open state
        half_open_max_calls: Max calls to allow in half-open state
    """

    def __init__(
        self,
        threshold: int = 5,
        reset_timeout: float = 60.0,
        half_open_max_calls: int = 1,
    ):
        """
        Initialize circuit breaker.

        Args:
            threshold: Consecutive failures before opening circuit
            reset_timeout: Seconds before attempting recovery
            half_open_max_calls: Max calls allowed in half-open state
        """
        if threshold < 1:
            raise ValueError("threshold must be positive")
        if reset_timeout <= 0:
            raise ValueError("reset_timeout must be positive")

        self.threshold = threshold
        self.reset_timeout = reset_timeout
        self.half_open_max_calls = half_open_max_calls

        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._last_failure_time: float | None = None
        self._half_open_calls = 0
        self._lock = asyncio.Lock()
        self._stats = CircuitBreakerStats()

        logger.info(
            "circuit_breaker_initialized",
            threshold=threshold,
            reset_timeout=reset_timeout,
        )

    @property
    def state(self) -> CircuitState:
        """Get current circuit state."""
        return self._state

    async def call(self, func: Callable[..., T], *args: Any, **kwargs: Any) -> T:
        """
        Execute a function through the circuit breaker.

        Args:
            func: Function to execute
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Function result

        Raises:
            CircuitBreakerOpenError: If circuit is open
            Exception: Original exception from function
        """
        async with self._lock:
            # Check if we should transition to half-open
            if self._state == CircuitState.OPEN and self._should_attempt_reset():
                self._transition_to_half_open()

            # Reject if circuit is open
            if self._state == CircuitState.OPEN:
                logger.warning("circuit_breaker_open", threshold=self.threshold)
                raise CircuitBreakerOpenError(
                    f"Circuit breaker is open (failures: {self._failure_count})"
                )

            # Limit calls in half-open state
            if self._state == CircuitState.HALF_OPEN:
                if self._half_open_calls >= self.half_open_max_calls:
                    raise CircuitBreakerOpenError("Circuit breaker is half-open (max calls reached)")
                self._half_open_calls += 1

        # Execute the function
        try:
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)

            # Record success
            async with self._lock:
                self._on_success()

            return result

        except Exception as e:
            # Record failure
            async with self._lock:
                self._on_failure()
            raise

    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset."""
        if self._last_failure_time is None:
            return False
        elapsed = time.time() - self._last_failure_time
        return elapsed >= self.reset_timeout

    def _transition_to_half_open(self) -> None:
        """Transition to half-open state."""
        logger.info("circuit_breaker_half_open")
        self._state = CircuitState.HALF_OPEN
        self._half_open_calls = 0
        self._stats.record_state_change()

    def _on_success(self) -> None:
        """Handle successful call."""
        self._stats.record_success()

        if self._state == CircuitState.HALF_OPEN:
            # Service recovered, close circuit
            logger.info("circuit_breaker_closed")
            self._state = CircuitState.CLOSED
            self._failure_count = 0
            self._stats.reset_failures()
            self._stats.record_state_change()
        elif self._state == CircuitState.CLOSED:
            # Reset failure count on success
            self._failure_count = 0
            self._stats.reset_failures()

    def _on_failure(self) -> None:
        """Handle failed call."""
        self._failure_count += 1
        self._last_failure_time = time.time()
        self._stats.record_failure()

        if self._state == CircuitState.HALF_OPEN:
            # Recovery failed, re-open circuit
            logger.warning("circuit_breaker_opened_from_half_open")
            self._state = CircuitState.OPEN
            self._stats.record_state_change()
        elif self._failure_count >= self.threshold:
            # Threshold exceeded, open circuit
            logger.warning(
                "circuit_breaker_opened",
                failures=self._failure_count,
                threshold=self.threshold,
            )
            self._state = CircuitState.OPEN
            self._stats.record_state_change()

    def get_stats(self) -> CircuitBreakerStats:
        """Get circuit breaker statistics."""
        return self._stats

    def reset(self) -> None:
        """Manually reset circuit breaker to closed state."""
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._last_failure_time = None
        self._half_open_calls = 0
        logger.info("circuit_breaker_reset")


class CircuitBreakerOpenError(Exception):
    """Raised when circuit breaker is open and rejects requests."""

    pass


class RetryExhaustedError(Exception):
    """Raised when all retry attempts are exhausted."""

    pass


def retry(
    config: RetryConfig | None = None,
    circuit_breaker: CircuitBreaker | None = None,
    on_retry: Callable[[Exception, int, float], None] | None = None,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Decorator to add retry logic with exponential backoff.

    Args:
        config: Retry configuration
        circuit_breaker: Optional circuit breaker instance
        on_retry: Optional callback called on each retry (error, attempt, delay)

    Returns:
        Decorated function

    Example:
        @retry(RetryConfig(max_retries=3, initial_delay=1.0))
        async def fetch_data():
            ...

        @retry(RetryConfig(max_retries=5), circuit_breaker=my_breaker)
        async def critical_operation():
            ...
    """
    if config is None:
        config = RetryConfig()

    stats = RetryStats()

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> T:
            last_error: Exception | None = None
            delay = config.initial_delay

            for attempt in range(config.max_retries + 1):
                try:
                    # Use circuit breaker if provided
                    if circuit_breaker is not None:
                        return await circuit_breaker.call(func, *args, **kwargs)
                    else:
                        # Execute directly
                        if asyncio.iscoroutinefunction(func):
                            return await func(*args, **kwargs)
                        else:
                            return func(*args, **kwargs)

                except Exception as e:
                    last_error = e
                    stats.record_attempt()

                    # Check if error is retriable
                    if not is_retriable_error(e):
                        logger.warning(
                            "retry_non_retriable_error",
                            error=str(e),
                            error_type=type(e).__name__,
                        )
                        stats.record_failure()
                        raise

                    # Check if we've exhausted retries
                    if attempt >= config.max_retries:
                        logger.error(
                            "retry_exhausted",
                            attempts=attempt + 1,
                            error=str(e),
                        )
                        stats.record_failure()
                        raise RetryExhaustedError(
                            f"Failed after {attempt + 1} attempts: {e}"
                        ) from e

                    # Calculate delay with exponential backoff and jitter
                    jitter_amount = delay * config.jitter * (2 * random.random() - 1)
                    actual_delay = min(config.max_delay, delay + jitter_amount)
                    delay_ms = actual_delay * 1000

                    stats.record_delay(delay_ms)

                    logger.info(
                        "retry_attempt",
                        attempt=attempt + 1,
                        max_retries=config.max_retries,
                        delay_ms=round(delay_ms, 2),
                        error=str(e),
                        error_type=type(e).__name__,
                    )

                    # Call retry callback if provided
                    if on_retry is not None:
                        on_retry(e, attempt + 1, actual_delay)

                    # Wait before retry
                    await asyncio.sleep(actual_delay)

                    # Increase delay for next retry
                    delay = min(config.max_delay, delay * config.multiplier)

            # This should never be reached, but satisfy type checker
            if last_error is not None:
                raise last_error
            raise RetryExhaustedError("Retry logic error")

        @wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> T:
            """Synchronous wrapper (not supported, raise error)."""
            raise NotImplementedError(
                "Retry decorator only supports async functions. "
                "Use 'async def' for functions decorated with @retry."
            )

        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


def get_retry_stats() -> dict[str, Any]:
    """
    Get global retry statistics.

    Returns:
        Dictionary with retry stats
    """
    # Note: This is a placeholder for global stats tracking
    # In a real implementation, we'd maintain a global stats object
    return {
        "message": "Retry stats tracking not yet implemented globally",
    }
