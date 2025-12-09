"""
Tests for Rate Limiter

Tests the token bucket rate limiter implementation.
"""

import asyncio
import time

import pytest

from src.utils.rate_limiter import (
    RateLimitExceededError,
    RateLimitStats,
    TokenBucketRateLimiter,
    rate_limited,
    with_rate_limit,
)


class TestRateLimitStats:
    """Tests for RateLimitStats dataclass."""

    def test_initial_values(self):
        """Test default initial values."""
        stats = RateLimitStats()
        assert stats.total_requests == 0
        assert stats.throttled_requests == 0
        assert stats.total_wait_time_ms == 0
        assert stats.max_wait_time_ms == 0

    def test_record_request(self):
        """Test recording a request."""
        stats = RateLimitStats()
        stats.record_request()
        stats.record_request()
        assert stats.total_requests == 2

    def test_record_throttle(self):
        """Test recording throttled requests."""
        stats = RateLimitStats()
        stats.record_throttle(100.0)
        stats.record_throttle(200.0)

        assert stats.throttled_requests == 2
        assert stats.total_wait_time_ms == 300.0
        assert stats.max_wait_time_ms == 200.0

    def test_reset(self):
        """Test resetting statistics."""
        stats = RateLimitStats()
        stats.record_request()
        stats.record_request()
        stats.record_throttle(100.0)

        stats.reset()

        assert stats.total_requests == 0
        assert stats.throttled_requests == 0
        assert stats.total_wait_time_ms == 0

    def test_to_dict(self):
        """Test conversion to dictionary."""
        stats = RateLimitStats()
        stats.record_request()
        stats.record_request()
        stats.record_throttle(100.0)

        result = stats.to_dict()

        assert result["total_requests"] == 2
        assert result["throttled_requests"] == 1
        assert "throttle_rate" in result
        assert "avg_wait_time_ms" in result
        assert "max_wait_time_ms" in result


class TestTokenBucketRateLimiter:
    """Tests for TokenBucketRateLimiter."""

    def test_initialization(self):
        """Test rate limiter initialization."""
        limiter = TokenBucketRateLimiter(
            requests_per_minute=60,
            burst_capacity=10,
            enabled=True,
        )

        assert limiter.requests_per_minute == 60
        assert limiter.max_tokens == 10
        assert limiter.enabled is True

    def test_disabled_limiter(self):
        """Test disabled rate limiter always grants permission."""
        limiter = TokenBucketRateLimiter(
            requests_per_minute=1,  # Very low limit
            enabled=False,
        )

        # Should always succeed when disabled
        for _ in range(100):
            assert limiter.try_acquire() is True

    @pytest.mark.asyncio
    async def test_acquire_basic(self):
        """Test basic acquire functionality."""
        limiter = TokenBucketRateLimiter(
            requests_per_minute=60,
            burst_capacity=5,
            enabled=True,
        )

        # Should be able to acquire burst capacity immediately
        for _ in range(5):
            result = await limiter.acquire()
            assert result is True

    def test_try_acquire_no_tokens(self):
        """Test try_acquire when no tokens available."""
        limiter = TokenBucketRateLimiter(
            requests_per_minute=60,
            burst_capacity=2,
            enabled=True,
        )

        # Exhaust tokens
        assert limiter.try_acquire() is True
        assert limiter.try_acquire() is True

        # Should fail without waiting
        assert limiter.try_acquire() is False

    def test_available_tokens(self):
        """Test available tokens property."""
        limiter = TokenBucketRateLimiter(
            requests_per_minute=60,
            burst_capacity=5,
            enabled=True,
        )

        initial_tokens = limiter.available_tokens
        assert initial_tokens == 5.0

        limiter.try_acquire()
        assert limiter.available_tokens == 4.0

    def test_stats_tracking(self):
        """Test statistics tracking."""
        limiter = TokenBucketRateLimiter(
            requests_per_minute=60,
            burst_capacity=2,
            enabled=True,
        )

        limiter.try_acquire()
        limiter.try_acquire()

        stats = limiter.get_stats()
        assert stats.total_requests == 2

    def test_reset_stats(self):
        """Test resetting statistics."""
        limiter = TokenBucketRateLimiter(
            requests_per_minute=60,
            enabled=True,
        )

        limiter.try_acquire()
        limiter.try_acquire()

        assert limiter.get_stats().total_requests == 2

        limiter.reset_stats()
        assert limiter.get_stats().total_requests == 0

    @pytest.mark.asyncio
    async def test_acquire_with_refill(self):
        """Test token refill over time."""
        # 600 requests per minute = 10 per second
        limiter = TokenBucketRateLimiter(
            requests_per_minute=600,
            burst_capacity=1,
            enabled=True,
        )

        # Use the one token
        assert limiter.try_acquire() is True
        assert limiter.try_acquire() is False

        # Wait for refill (100ms should give ~1 token at 10/sec)
        await asyncio.sleep(0.15)

        # Should have refilled
        assert limiter.try_acquire() is True


class TestRateLimitedDecorator:
    """Tests for the rate_limited decorator."""

    @pytest.mark.asyncio
    async def test_decorator_basic(self):
        """Test basic decorator usage."""
        call_count = 0

        @rate_limited
        async def my_function() -> str:
            nonlocal call_count
            call_count += 1
            return "result"

        result = await my_function()
        assert result == "result"
        assert call_count == 1


class TestWithRateLimit:
    """Tests for the with_rate_limit helper."""

    @pytest.mark.asyncio
    async def test_with_rate_limit_basic(self):
        """Test basic with_rate_limit usage."""

        async def my_coro() -> str:
            return "result"

        result = await with_rate_limit(my_coro())
        assert result == "result"


class TestRateLimitIntegration:
    """Integration tests for rate limiting."""

    @pytest.mark.asyncio
    async def test_concurrent_requests(self):
        """Test concurrent requests are properly rate limited."""
        limiter = TokenBucketRateLimiter(
            requests_per_minute=600,  # 10 per second
            burst_capacity=3,
            enabled=True,
        )

        results = []

        async def make_request(i: int) -> int:
            await limiter.acquire()
            return i

        # Launch 5 concurrent requests with only 3 burst capacity
        start = time.monotonic()
        tasks = [make_request(i) for i in range(5)]
        results = await asyncio.gather(*tasks)
        elapsed = time.monotonic() - start

        # All should complete
        assert len(results) == 5
        # Should have taken some time due to rate limiting
        # 3 burst + 2 waiting at 10/sec = ~0.2 seconds
        assert elapsed >= 0.1  # Some delay occurred
