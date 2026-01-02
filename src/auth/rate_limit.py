"""
Auth Rate Limiting
Phase 4.5: Security & Authentication

IP-based rate limiting for authentication endpoints to prevent brute force attacks.
"""

import time
from collections import defaultdict
from dataclasses import dataclass, field

import structlog
from fastapi import HTTPException, Request, status

logger = structlog.get_logger()


@dataclass
class RateLimitEntry:
    """Track request counts for rate limiting."""

    count: int = 0
    window_start: float = field(default_factory=time.time)


class AuthRateLimiter:
    """
    IP-based rate limiter for authentication endpoints.

    Uses a sliding window approach to limit requests per IP address.
    """

    def __init__(
        self,
        requests_per_minute: int = 10,
        window_seconds: int = 60,
        block_duration_seconds: int = 300,
    ):
        """
        Initialize the rate limiter.

        Args:
            requests_per_minute: Maximum requests allowed per window
            window_seconds: Size of the sliding window in seconds
            block_duration_seconds: How long to block after exceeding limit
        """
        self.max_requests = requests_per_minute
        self.window_seconds = window_seconds
        self.block_duration = block_duration_seconds
        self._requests: dict[str, RateLimitEntry] = defaultdict(RateLimitEntry)
        self._blocked: dict[str, float] = {}  # IP -> unblock time

    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP from request."""
        # Check for forwarded header (behind proxy)
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()
        # Check for real IP header
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
        # Fall back to client host
        return request.client.host if request.client else "unknown"

    def _cleanup_old_entries(self) -> None:
        """Remove expired entries."""
        now = time.time()

        # Clean up request tracking
        expired_keys = [
            ip
            for ip, entry in self._requests.items()
            if now - entry.window_start > self.window_seconds * 2
        ]
        for ip in expired_keys:
            del self._requests[ip]

        # Clean up block list
        expired_blocks = [ip for ip, unblock_time in self._blocked.items() if now > unblock_time]
        for ip in expired_blocks:
            del self._blocked[ip]
            logger.info("rate_limit_unblocked", ip=ip)

    def is_blocked(self, ip: str) -> bool:
        """Check if an IP is currently blocked."""
        if ip in self._blocked:
            if time.time() < self._blocked[ip]:
                return True
            # Block expired
            del self._blocked[ip]
        return False

    def check_rate_limit(self, request: Request) -> None:
        """
        Check if request is rate limited.

        Args:
            request: FastAPI request object

        Raises:
            HTTPException: If rate limit exceeded
        """
        ip = self._get_client_ip(request)
        now = time.time()

        # Periodic cleanup
        if len(self._requests) > 1000:
            self._cleanup_old_entries()

        # Check if blocked
        if self.is_blocked(ip):
            remaining = int(self._blocked[ip] - now)
            logger.warning("rate_limit_blocked_request", ip=ip, remaining_seconds=remaining)
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Too many requests. Please try again in {remaining} seconds.",
                headers={"Retry-After": str(remaining)},
            )

        # Get or create entry for this IP
        entry = self._requests[ip]

        # Check if we're in a new window
        if now - entry.window_start > self.window_seconds:
            entry.count = 0
            entry.window_start = now

        # Increment counter
        entry.count += 1

        # Check if limit exceeded
        if entry.count > self.max_requests:
            # Block this IP
            self._blocked[ip] = now + self.block_duration
            logger.warning(
                "rate_limit_exceeded",
                ip=ip,
                requests=entry.count,
                block_duration=self.block_duration,
            )
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Please try again in {self.block_duration} seconds.",
                headers={"Retry-After": str(self.block_duration)},
            )

    def get_remaining(self, request: Request) -> dict:
        """Get rate limit status for a request."""
        ip = self._get_client_ip(request)
        now = time.time()

        if self.is_blocked(ip):
            return {
                "blocked": True,
                "remaining": 0,
                "retry_after": int(self._blocked[ip] - now),
            }

        entry = self._requests.get(ip)
        if not entry or now - entry.window_start > self.window_seconds:
            remaining = self.max_requests
        else:
            remaining = max(0, self.max_requests - entry.count)

        return {
            "blocked": False,
            "remaining": remaining,
            "limit": self.max_requests,
            "window_seconds": self.window_seconds,
        }


# Global rate limiters for auth endpoints
_login_limiter: AuthRateLimiter | None = None
_register_limiter: AuthRateLimiter | None = None


def get_login_limiter() -> AuthRateLimiter:
    """Get rate limiter for login endpoint."""
    global _login_limiter
    if _login_limiter is None:
        # Stricter limits for login (5 requests per minute, 5 min block)
        _login_limiter = AuthRateLimiter(
            requests_per_minute=5,
            window_seconds=60,
            block_duration_seconds=300,
        )
    return _login_limiter


def get_register_limiter() -> AuthRateLimiter:
    """Get rate limiter for register endpoint."""
    global _register_limiter
    if _register_limiter is None:
        # Less strict for registration (3 requests per minute, 10 min block)
        _register_limiter = AuthRateLimiter(
            requests_per_minute=3,
            window_seconds=60,
            block_duration_seconds=600,
        )
    return _register_limiter
