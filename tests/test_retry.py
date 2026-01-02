"""
Tests for retry utilities with exponential backoff and circuit breaker.
"""

import asyncio
from unittest.mock import AsyncMock, Mock

import httpx
import pytest

from src.utils.retry import (
    CircuitBreaker,
    CircuitBreakerOpenError,
    CircuitState,
    RetryConfig,
    RetryExhaustedError,
    is_retriable_error,
    retry,
)


class TestIsRetriableError:
    """Tests for error classification."""

    def test_timeout_errors_are_retriable(self):
        """Timeout errors should be retriable."""
        assert is_retriable_error(asyncio.TimeoutError())
        assert is_retriable_error(TimeoutError())

    def test_connection_errors_are_retriable(self):
        """Connection errors should be retriable."""
        assert is_retriable_error(ConnectionError())
        assert is_retriable_error(ConnectionRefusedError())
        assert is_retriable_error(ConnectionResetError())

    def test_httpx_timeout_is_retriable(self):
        """HTTPX timeout errors should be retriable."""
        assert is_retriable_error(httpx.TimeoutException("timeout"))

    def test_httpx_connect_error_is_retriable(self):
        """HTTPX connection errors should be retriable."""
        assert is_retriable_error(httpx.ConnectError("connection failed"))

    def test_http_429_is_retriable(self):
        """HTTP 429 (rate limit) should be retriable."""
        response = Mock()
        response.status_code = 429
        error = httpx.HTTPStatusError("rate limited", request=Mock(), response=response)
        assert is_retriable_error(error)

    def test_http_502_is_retriable(self):
        """HTTP 502 (bad gateway) should be retriable."""
        response = Mock()
        response.status_code = 502
        error = httpx.HTTPStatusError("bad gateway", request=Mock(), response=response)
        assert is_retriable_error(error)

    def test_http_503_is_retriable(self):
        """HTTP 503 (service unavailable) should be retriable."""
        response = Mock()
        response.status_code = 503
        error = httpx.HTTPStatusError("service unavailable", request=Mock(), response=response)
        assert is_retriable_error(error)

    def test_http_504_is_retriable(self):
        """HTTP 504 (gateway timeout) should be retriable."""
        response = Mock()
        response.status_code = 504
        error = httpx.HTTPStatusError("gateway timeout", request=Mock(), response=response)
        assert is_retriable_error(error)

    def test_http_400_is_not_retriable(self):
        """HTTP 400 (bad request) should not be retriable."""
        response = Mock()
        response.status_code = 400
        error = httpx.HTTPStatusError("bad request", request=Mock(), response=response)
        assert not is_retriable_error(error)

    def test_http_401_is_not_retriable(self):
        """HTTP 401 (unauthorized) should not be retriable."""
        response = Mock()
        response.status_code = 401
        error = httpx.HTTPStatusError("unauthorized", request=Mock(), response=response)
        assert not is_retriable_error(error)

    def test_http_404_is_not_retriable(self):
        """HTTP 404 (not found) should not be retriable."""
        response = Mock()
        response.status_code = 404
        error = httpx.HTTPStatusError("not found", request=Mock(), response=response)
        assert not is_retriable_error(error)

    def test_value_error_is_not_retriable(self):
        """ValueError should not be retriable."""
        assert not is_retriable_error(ValueError("invalid value"))

    def test_os_error_is_retriable(self):
        """OSError and subclasses should be retriable."""
        assert is_retriable_error(OSError("OS error"))
        assert is_retriable_error(BrokenPipeError("broken pipe"))


class TestRetryConfig:
    """Tests for retry configuration."""

    def test_default_config(self):
        """Test default configuration values."""
        config = RetryConfig()
        assert config.max_retries == 3
        assert config.initial_delay == 1.0
        assert config.max_delay == 30.0
        assert config.multiplier == 2.0
        assert config.jitter == 0.1

    def test_custom_config(self):
        """Test custom configuration values."""
        config = RetryConfig(
            max_retries=5,
            initial_delay=2.0,
            max_delay=60.0,
            multiplier=3.0,
            jitter=0.2,
        )
        assert config.max_retries == 5
        assert config.initial_delay == 2.0
        assert config.max_delay == 60.0
        assert config.multiplier == 3.0
        assert config.jitter == 0.2

    def test_invalid_max_retries(self):
        """Negative max_retries should raise ValueError."""
        with pytest.raises(ValueError, match="max_retries must be non-negative"):
            RetryConfig(max_retries=-1)

    def test_invalid_initial_delay(self):
        """Non-positive initial_delay should raise ValueError."""
        with pytest.raises(ValueError, match="initial_delay must be positive"):
            RetryConfig(initial_delay=0)

    def test_invalid_max_delay(self):
        """max_delay < initial_delay should raise ValueError."""
        with pytest.raises(ValueError, match="max_delay must be >= initial_delay"):
            RetryConfig(initial_delay=10.0, max_delay=5.0)

    def test_invalid_multiplier(self):
        """multiplier < 1 should raise ValueError."""
        with pytest.raises(ValueError, match="multiplier must be >= 1"):
            RetryConfig(multiplier=0.5)

    def test_invalid_jitter(self):
        """jitter outside [0, 1] should raise ValueError."""
        with pytest.raises(ValueError, match="jitter must be between 0 and 1"):
            RetryConfig(jitter=-0.1)
        with pytest.raises(ValueError, match="jitter must be between 0 and 1"):
            RetryConfig(jitter=1.5)


class TestCircuitBreaker:
    """Tests for circuit breaker pattern."""

    @pytest.mark.asyncio
    async def test_initial_state_is_closed(self):
        """Circuit breaker should start in closed state."""
        breaker = CircuitBreaker(threshold=3)
        assert breaker.state == CircuitState.CLOSED

    @pytest.mark.asyncio
    async def test_successful_calls_keep_circuit_closed(self):
        """Successful calls should keep circuit closed."""
        breaker = CircuitBreaker(threshold=3)

        async def success_func():
            return "success"

        for _ in range(5):
            result = await breaker.call(success_func)
            assert result == "success"
            assert breaker.state == CircuitState.CLOSED

    @pytest.mark.asyncio
    async def test_opens_after_threshold_failures(self):
        """Circuit should open after threshold failures."""
        breaker = CircuitBreaker(threshold=3)

        async def failing_func():
            raise ConnectionError("connection failed")

        # Fail threshold times
        for i in range(3):
            with pytest.raises(ConnectionError):
                await breaker.call(failing_func)

        # Circuit should now be open
        assert breaker.state == CircuitState.OPEN

    @pytest.mark.asyncio
    async def test_rejects_calls_when_open(self):
        """Circuit should reject calls when open."""
        breaker = CircuitBreaker(threshold=2)

        async def failing_func():
            raise ConnectionError("connection failed")

        # Open the circuit
        for _ in range(2):
            with pytest.raises(ConnectionError):
                await breaker.call(failing_func)

        assert breaker.state == CircuitState.OPEN

        # Should reject new calls
        async def success_func():
            return "success"

        with pytest.raises(CircuitBreakerOpenError):
            await breaker.call(success_func)

    @pytest.mark.asyncio
    async def test_transitions_to_half_open_after_timeout(self):
        """Circuit should transition to half-open after reset timeout."""
        breaker = CircuitBreaker(threshold=2, reset_timeout=0.1)

        async def failing_func():
            raise ConnectionError("connection failed")

        # Open the circuit
        for _ in range(2):
            with pytest.raises(ConnectionError):
                await breaker.call(failing_func)

        assert breaker.state == CircuitState.OPEN

        # Wait for reset timeout
        await asyncio.sleep(0.15)

        # Next call should transition to half-open
        async def success_func():
            return "success"

        result = await breaker.call(success_func)
        assert result == "success"
        assert breaker.state == CircuitState.CLOSED

    @pytest.mark.asyncio
    async def test_closes_on_half_open_success(self):
        """Circuit should close on successful half-open call."""
        breaker = CircuitBreaker(threshold=2, reset_timeout=0.1)

        async def failing_func():
            raise ConnectionError("connection failed")

        # Open the circuit
        for _ in range(2):
            with pytest.raises(ConnectionError):
                await breaker.call(failing_func)

        # Wait for reset timeout
        await asyncio.sleep(0.15)

        # Successful call should close circuit
        async def success_func():
            return "success"

        await breaker.call(success_func)
        assert breaker.state == CircuitState.CLOSED

    @pytest.mark.asyncio
    async def test_reopens_on_half_open_failure(self):
        """Circuit should reopen on failed half-open call."""
        breaker = CircuitBreaker(threshold=2, reset_timeout=0.1)

        async def failing_func():
            raise ConnectionError("connection failed")

        # Open the circuit
        for _ in range(2):
            with pytest.raises(ConnectionError):
                await breaker.call(failing_func)

        # Wait for reset timeout
        await asyncio.sleep(0.15)

        # Failed call should reopen circuit
        with pytest.raises(ConnectionError):
            await breaker.call(failing_func)

        assert breaker.state == CircuitState.OPEN

    @pytest.mark.asyncio
    async def test_resets_failure_count_on_success(self):
        """Successful call should reset failure count."""
        breaker = CircuitBreaker(threshold=3)

        async def failing_func():
            raise ConnectionError("connection failed")

        async def success_func():
            return "success"

        # Fail twice (under threshold)
        for _ in range(2):
            with pytest.raises(ConnectionError):
                await breaker.call(failing_func)

        assert breaker.state == CircuitState.CLOSED

        # Success should reset count
        await breaker.call(success_func)

        # Can fail threshold times again before opening
        for _ in range(3):
            with pytest.raises(ConnectionError):
                await breaker.call(failing_func)

        assert breaker.state == CircuitState.OPEN


class TestRetryDecorator:
    """Tests for retry decorator."""

    @pytest.mark.asyncio
    async def test_successful_first_attempt(self):
        """Successful first attempt should not retry."""
        config = RetryConfig(max_retries=3, initial_delay=0.1)

        call_count = 0

        @retry(config)
        async def success_func():
            nonlocal call_count
            call_count += 1
            return "success"

        result = await success_func()
        assert result == "success"
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_retries_on_retriable_error(self):
        """Should retry on retriable errors."""
        config = RetryConfig(max_retries=3, initial_delay=0.05, jitter=0)

        call_count = 0

        @retry(config)
        async def transient_failure():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ConnectionRefusedError("connection failed")
            return "success"

        result = await transient_failure()
        assert result == "success"
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_fails_immediately_on_non_retriable_error(self):
        """Should fail immediately on non-retriable errors."""
        config = RetryConfig(max_retries=3, initial_delay=0.1)

        call_count = 0

        @retry(config)
        async def non_retriable_failure():
            nonlocal call_count
            call_count += 1
            raise ValueError("invalid value")

        with pytest.raises(ValueError, match="invalid value"):
            await non_retriable_failure()

        assert call_count == 1

    @pytest.mark.asyncio
    async def test_exhausts_retries(self):
        """Should raise RetryExhaustedError after max retries."""
        config = RetryConfig(max_retries=2, initial_delay=0.05, jitter=0)

        call_count = 0

        @retry(config)
        async def always_fails():
            nonlocal call_count
            call_count += 1
            raise ConnectionError("connection failed")

        with pytest.raises(RetryExhaustedError, match="Failed after 3 attempts"):
            await always_fails()

        assert call_count == 3  # initial + 2 retries

    @pytest.mark.asyncio
    async def test_exponential_backoff(self):
        """Should apply exponential backoff between retries."""
        config = RetryConfig(
            max_retries=3,
            initial_delay=0.05,
            multiplier=2.0,
            jitter=0,  # No jitter for predictable testing
        )

        call_times = []

        @retry(config)
        async def measure_timing():
            call_times.append(asyncio.get_event_loop().time())
            if len(call_times) < 3:
                raise ConnectionError("connection failed")
            return "success"

        await measure_timing()

        # Check delays are approximately correct (with some tolerance)
        # Expected delays: 0.05s, 0.1s
        delay1 = call_times[1] - call_times[0]
        delay2 = call_times[2] - call_times[1]

        assert 0.04 <= delay1 <= 0.08  # ~0.05s with tolerance
        assert 0.08 <= delay2 <= 0.15  # ~0.1s with tolerance

    @pytest.mark.asyncio
    async def test_jitter_is_applied(self):
        """Should apply jitter to delays."""
        config = RetryConfig(
            max_retries=10,
            initial_delay=0.1,
            multiplier=1.0,  # No exponential growth
            jitter=0.5,  # High jitter for noticeable variance
        )

        delays = []

        @retry(config)
        async def collect_delays():
            if len(delays) > 0:
                delays.append(asyncio.get_event_loop().time())
            else:
                delays.append(asyncio.get_event_loop().time())

            if len(delays) < 6:
                raise ConnectionError("connection failed")
            return "success"

        await collect_delays()

        # Calculate actual delays
        actual_delays = [delays[i] - delays[i - 1] for i in range(1, len(delays))]

        # With jitter, delays should vary (not all the same)
        # At least some delays should differ by more than 10%
        delay_variance = max(actual_delays) - min(actual_delays)
        assert delay_variance > 0.01  # Should have noticeable variance

    @pytest.mark.asyncio
    async def test_max_delay_is_respected(self):
        """Should not exceed max_delay."""
        config = RetryConfig(
            max_retries=5,
            initial_delay=1.0,
            max_delay=2.0,
            multiplier=10.0,  # Would exceed max without capping
            jitter=0,
        )

        call_times = []

        @retry(config)
        async def test_max():
            call_times.append(asyncio.get_event_loop().time())
            if len(call_times) < 4:
                raise ConnectionError("connection failed")
            return "success"

        await test_max()

        # All delays should be <= max_delay
        for i in range(1, len(call_times)):
            delay = call_times[i] - call_times[i - 1]
            assert delay <= 2.1  # max_delay + small tolerance

    @pytest.mark.asyncio
    async def test_with_circuit_breaker(self):
        """Should work with circuit breaker."""
        config = RetryConfig(max_retries=2, initial_delay=0.05, jitter=0)
        breaker = CircuitBreaker(threshold=3, reset_timeout=60.0)

        call_count = 0

        @retry(config, circuit_breaker=breaker)
        async def with_breaker():
            nonlocal call_count
            call_count += 1
            raise ConnectionError("connection failed")

        # First call - should retry until exhausted (3 attempts: 1 initial + 2 retries)
        with pytest.raises(RetryExhaustedError):
            await with_breaker()

        # Circuit should now be open after 3 failures (matching threshold)
        assert breaker.state == CircuitState.OPEN
        assert call_count == 3

        # Second call - should fail immediately with circuit breaker error
        # The circuit breaker will reject before retry logic kicks in
        with pytest.raises(CircuitBreakerOpenError):
            await with_breaker()

        # Call count should still be 3 (no new attempts were made)
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_on_retry_callback(self):
        """Should call on_retry callback."""
        config = RetryConfig(max_retries=3, initial_delay=0.05, jitter=0)

        retry_events = []

        def on_retry_callback(error, attempt, delay):
            retry_events.append({"error": str(error), "attempt": attempt, "delay": delay})

        @retry(config, on_retry=on_retry_callback)
        async def with_callback():
            if len(retry_events) < 2:
                raise ConnectionError("connection failed")
            return "success"

        await with_callback()

        assert len(retry_events) == 2
        assert retry_events[0]["attempt"] == 1
        assert retry_events[1]["attempt"] == 2

    def test_sync_function_raises_error(self):
        """Retry decorator should not support sync functions."""
        config = RetryConfig()

        @retry(config)
        def sync_func():
            return "sync"

        with pytest.raises(NotImplementedError, match="only supports async functions"):
            sync_func()
