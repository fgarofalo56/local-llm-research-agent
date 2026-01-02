"""
Retry Logic Example

Demonstrates the retry mechanism with exponential backoff and circuit breaker
for handling transient failures in the research agent.

Features demonstrated:
- Automatic retry on transient failures (connection errors, timeouts)
- Exponential backoff with jitter
- Circuit breaker pattern to prevent cascading failures
- Immediate failure on non-retriable errors
"""

import asyncio
from datetime import datetime

from src.agent.core import ResearchAgent, create_research_agent
from src.utils.logger import get_logger
from src.utils.retry import CircuitBreaker, RetryConfig, retry

logger = get_logger(__name__)


async def example_basic_retry():
    """
    Example 1: Basic retry with exponential backoff.

    The agent will automatically retry on transient failures like
    connection errors or timeouts.
    """
    print("\n" + "=" * 80)
    print("Example 1: Basic Retry with Exponential Backoff")
    print("=" * 80)

    # Create agent - it comes with built-in retry logic
    agent = create_research_agent(provider_type="ollama", model_name="qwen3:30b")

    print("\nAgent initialized with retry configuration:")
    print(f"  - Max retries: 3")
    print(f"  - Initial delay: 1.0s")
    print(f"  - Max delay: 30.0s")
    print(f"  - Multiplier: 2.0")
    print(f"  - Jitter: 0.1 (10%)")

    try:
        # Make a request - if there are transient failures, it will retry automatically
        print("\nSending query to agent...")
        response = await agent.chat("List all tables in the database")
        print(f"\nResponse: {response[:200]}...")

    except Exception as e:
        print(f"\nError after retries: {e}")


async def example_custom_retry():
    """
    Example 2: Custom retry configuration for specific operations.

    Demonstrates creating a custom retry decorator with different parameters.
    """
    print("\n" + "=" * 80)
    print("Example 2: Custom Retry Configuration")
    print("=" * 80)

    # Create custom retry config for aggressive retries
    aggressive_retry = RetryConfig(
        max_retries=5,
        initial_delay=0.5,
        max_delay=10.0,
        multiplier=1.5,
        jitter=0.2,
    )

    call_count = 0

    @retry(aggressive_retry)
    async def fetch_data_with_custom_retry():
        """Simulated operation that might fail transiently."""
        nonlocal call_count
        call_count += 1
        print(f"  Attempt {call_count}...")

        # Simulate transient failure for first 2 attempts
        if call_count < 3:
            print(f"  > Simulating transient failure (ConnectionRefusedError)")
            raise ConnectionRefusedError("Service temporarily unavailable")

        print(f"  > Success!")
        return "Data fetched successfully"

    print("\nCustom retry configuration:")
    print(f"  - Max retries: {aggressive_retry.max_retries}")
    print(f"  - Initial delay: {aggressive_retry.initial_delay}s")
    print(f"  - Max delay: {aggressive_retry.max_delay}s")
    print(f"  - Multiplier: {aggressive_retry.multiplier}")
    print(f"  - Jitter: {aggressive_retry.jitter}")

    print("\nExecuting function with custom retry...")
    result = await fetch_data_with_custom_retry()
    print(f"\nResult: {result}")
    print(f"Total attempts: {call_count}")


async def example_circuit_breaker():
    """
    Example 3: Circuit breaker pattern.

    Demonstrates how the circuit breaker prevents cascading failures
    by opening the circuit after a threshold of consecutive failures.
    """
    print("\n" + "=" * 80)
    print("Example 3: Circuit Breaker Pattern")
    print("=" * 80)

    # Create circuit breaker
    breaker = CircuitBreaker(
        threshold=3,  # Open after 3 failures
        reset_timeout=5.0,  # Try to recover after 5 seconds
    )

    print("\nCircuit breaker configuration:")
    print(f"  - Failure threshold: 3")
    print(f"  - Reset timeout: 5.0s")
    print(f"  - Initial state: {breaker.state.value}")

    call_count = 0

    @retry(RetryConfig(max_retries=1, initial_delay=0.1), circuit_breaker=breaker)
    async def failing_operation():
        """Simulated operation that always fails."""
        nonlocal call_count
        call_count += 1
        print(f"  Attempt {call_count} (Circuit: {breaker.state.value})")
        raise ConnectionError("Service is down")

    # Make multiple failing calls to trigger circuit breaker
    print("\nMaking failing calls to trigger circuit breaker...")
    for i in range(5):
        try:
            await failing_operation()
        except Exception as e:
            print(f"  Call {i+1} failed: {type(e).__name__}")

    print(f"\nCircuit breaker state: {breaker.state.value}")
    print(f"Total attempts made: {call_count}")

    # Try one more call - should fail immediately with circuit breaker error
    print("\nAttempting one more call (circuit should be open)...")
    try:
        await failing_operation()
    except Exception as e:
        print(f"  Failed immediately: {type(e).__name__}: {e}")

    print(f"\nTotal attempts made: {call_count} (no new attempts when circuit open)")


async def example_retry_callback():
    """
    Example 4: Retry callback for monitoring.

    Demonstrates using a callback to track retry attempts and delays.
    """
    print("\n" + "=" * 80)
    print("Example 4: Retry Callback for Monitoring")
    print("=" * 80)

    retry_events = []

    def on_retry_callback(error, attempt, delay):
        """Track retry events for monitoring/logging."""
        event = {
            "timestamp": datetime.now().isoformat(),
            "error_type": type(error).__name__,
            "error_message": str(error),
            "attempt": attempt,
            "delay_seconds": delay,
        }
        retry_events.append(event)
        print(f"  Retry {attempt}: {type(error).__name__} - waiting {delay:.2f}s")

    config = RetryConfig(max_retries=3, initial_delay=0.5, jitter=0)

    call_count = 0

    @retry(config, on_retry=on_retry_callback)
    async def operation_with_monitoring():
        """Operation with retry monitoring."""
        nonlocal call_count
        call_count += 1

        if call_count < 3:
            raise ConnectionError(f"Connection failed on attempt {call_count}")

        return "Success"

    print("\nExecuting operation with retry monitoring...")
    result = await operation_with_monitoring()

    print(f"\nResult: {result}")
    print(f"\nRetry events collected: {len(retry_events)}")
    for event in retry_events:
        print(f"  - Attempt {event['attempt']}: {event['error_type']} "
              f"(delay: {event['delay_seconds']:.2f}s)")


async def example_agent_with_stats():
    """
    Example 5: Monitoring agent retry behavior.

    Shows how the agent's built-in retry and circuit breaker work together.
    """
    print("\n" + "=" * 80)
    print("Example 5: Agent Retry Behavior and Statistics")
    print("=" * 80)

    # Create agent
    agent = create_research_agent(provider_type="ollama", model_name="qwen3:30b")

    print("\nAgent retry configuration (built-in):")
    print(f"  - Retry max attempts: 3")
    print(f"  - Circuit breaker threshold: 5")
    print(f"  - Circuit breaker reset timeout: 60s")

    print("\nAgent is resilient to transient failures like:")
    print("  - Connection timeouts")
    print("  - Service temporarily unavailable (HTTP 503)")
    print("  - Rate limiting (HTTP 429)")
    print("  - Network errors")

    print("\nNon-retriable errors fail immediately:")
    print("  - Bad request (HTTP 400)")
    print("  - Unauthorized (HTTP 401)")
    print("  - Not found (HTTP 404)")
    print("  - Validation errors")

    # Note: In real usage, the agent would automatically retry on transient failures
    print("\nIn production, the agent automatically handles transient failures")
    print("transparently without requiring any special handling from the caller.")


async def main():
    """Run all examples."""
    print("\n" + "=" * 80)
    print("RETRY LOGIC DEMONSTRATION")
    print("=" * 80)

    # Run examples
    await example_custom_retry()
    await example_circuit_breaker()
    await example_retry_callback()
    await example_agent_with_stats()

    # Note: example_basic_retry() requires a running Ollama instance
    print("\n" + "=" * 80)
    print("Note: To test agent retry with real Ollama, ensure Ollama is running")
    print("      and uncomment the example_basic_retry() call below.")
    print("=" * 80)

    # Uncomment to test with real agent (requires Ollama):
    # await example_basic_retry()


if __name__ == "__main__":
    asyncio.run(main())
