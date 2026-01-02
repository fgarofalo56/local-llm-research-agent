"""
Statistics tracking for research agent.

Tracks token usage, duration, and other metrics for agent responses.
"""

from src.models.chat import TokenUsage
from src.utils.rate_limiter import RateLimitStats, TokenBucketRateLimiter


class AgentStats:
    """
    Manages statistics and metrics for the research agent.

    Tracks last response metadata (token usage, duration) and
    provides rate limiting statistics.
    """

    def __init__(self, rate_limiter: TokenBucketRateLimiter):
        """
        Initialize agent statistics tracker.

        Args:
            rate_limiter: TokenBucketRateLimiter instance to track
        """
        self._rate_limiter = rate_limiter
        self._last_token_usage: TokenUsage | None = None
        self._last_duration_ms: float = 0.0

    def set_last_response(
        self,
        token_usage: TokenUsage | None,
        duration_ms: float,
    ) -> None:
        """
        Store last response statistics.

        Args:
            token_usage: Token usage from last response
            duration_ms: Duration of last response in milliseconds
        """
        self._last_token_usage = token_usage
        self._last_duration_ms = duration_ms

    def get_last_response_stats(self) -> dict:
        """Get statistics from the last response (useful after streaming)."""
        return {
            "token_usage": self._last_token_usage or TokenUsage(),
            "duration_ms": self._last_duration_ms,
        }

    def get_rate_limit_stats(self) -> RateLimitStats:
        """Get current rate limiting statistics."""
        return self._rate_limiter.get_stats()

    def reset_rate_limit_stats(self) -> None:
        """Reset rate limiting statistics."""
        self._rate_limiter.reset_stats()

    @property
    def rate_limit_enabled(self) -> bool:
        """Check if rate limiting is enabled."""
        return self._rate_limiter.enabled

    @rate_limit_enabled.setter
    def rate_limit_enabled(self, value: bool) -> None:
        """Enable or disable rate limiting."""
        self._rate_limiter.enabled = value
