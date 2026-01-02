"""
Core Research Agent Implementation

The main AI agent that uses local LLM providers (Ollama or Foundry Local)
for inference and MCP tools for SQL Server data access.
"""

import time
from collections.abc import AsyncIterator

from pydantic_ai import Agent

from src.agent.cache import AgentCache
from src.agent.prompts import get_system_prompt
from src.agent.stats import AgentStats
from src.mcp.client import MCPClientManager
from src.models.chat import AgentResponse, ChatMessage, Conversation, ConversationTurn, TokenUsage
from src.providers import LLMProvider, ProviderType, create_provider
from src.utils.cache import ResponseCache, get_response_cache
from src.utils.config import settings
from src.utils.logger import get_logger
from src.utils.rate_limiter import get_rate_limiter
from src.utils.retry import CircuitBreaker, RetryConfig, retry

logger = get_logger(__name__)


class ResearchAgentError(Exception):
    """Base exception for research agent errors."""

    pass


class ProviderConnectionError(ResearchAgentError):
    """Error connecting to LLM provider."""

    pass


# Backwards compatibility alias
OllamaConnectionError = ProviderConnectionError


class ResearchAgent:
    """
    Research agent for SQL Server data analytics.

    Uses local LLM providers (Ollama or Foundry Local) for inference
    and MSSQL MCP Server for database access.
    """

    def __init__(
        self,
        provider: LLMProvider | None = None,
        provider_type: ProviderType | str | None = None,
        model_name: str | None = None,
        readonly: bool | None = None,
        minimal_prompt: bool = False,
        cache_enabled: bool | None = None,
        explain_mode: bool = False,
        # Legacy Ollama-specific parameters (for backwards compatibility)
        ollama_host: str | None = None,
        ollama_model: str | None = None,
    ):
        """
        Initialize the research agent.

        Args:
            provider: Pre-configured LLM provider instance
            provider_type: Provider type ('ollama' or 'foundry_local')
            model_name: Model name/alias for the provider
            readonly: Enable read-only mode (default from settings)
            minimal_prompt: Use minimal system prompt
            cache_enabled: Enable response caching (default from settings)
            explain_mode: Enable educational query explanations
            ollama_host: (Legacy) Ollama server URL
            ollama_model: (Legacy) Ollama model name
        """
        self.readonly = readonly if readonly is not None else settings.mcp_mssql_readonly
        self.minimal_prompt = minimal_prompt
        self.explain_mode = explain_mode

        # Initialize response cache
        self._cache_enabled = cache_enabled if cache_enabled is not None else settings.cache_enabled
        self.cache: ResponseCache[str] = get_response_cache(
            max_size=settings.cache_max_size,
            ttl_seconds=settings.cache_ttl_seconds,
            enabled=self._cache_enabled,
        )

        # Initialize MCP components
        self.mcp_manager = MCPClientManager()
        self.mssql_server = self.mcp_manager.get_mssql_server()

        # Configure LLM provider
        if provider is not None:
            # Use provided provider instance
            self.provider = provider
        elif ollama_host or ollama_model:
            # Legacy: explicit Ollama configuration
            from src.providers.ollama import OllamaProvider

            self.provider = OllamaProvider(
                model_name=ollama_model or settings.ollama_model,
                host=ollama_host or settings.ollama_host,
            )
        else:
            # Use factory to create provider based on settings or parameters
            self.provider = create_provider(
                provider_type=provider_type,
                model_name=model_name,
            )

        # Get model from provider
        self.model = self.provider.get_model()

        # Create agent
        self.agent = Agent(
            model=self.model,
            system_prompt=get_system_prompt(
                readonly=self.readonly,
                minimal=self.minimal_prompt,
                explain_mode=self.explain_mode,
            ),
            toolsets=[self.mssql_server],
        )

        # Conversation tracking
        self.conversation = Conversation()

        # Initialize rate limiter
        self.rate_limiter = get_rate_limiter(
            requests_per_minute=settings.rate_limit_rpm,
            enabled=settings.rate_limit_enabled,
        )

        # Initialize cache and stats managers
        self._cache_manager = AgentCache(self.cache)
        self._stats_manager = AgentStats(self.rate_limiter)

        # Initialize retry configuration and circuit breaker
        self._retry_config = RetryConfig(
            max_retries=3,
            initial_delay=1.0,
            max_delay=30.0,
            multiplier=2.0,
            jitter=0.1,
        )
        self._circuit_breaker = CircuitBreaker(
            threshold=5,
            reset_timeout=60.0,
        )

        logger.info(
            "research_agent_initialized",
            provider=self.provider.provider_type.value,
            model=self.provider.model_name,
            readonly=self.readonly,
            cache_enabled=self._cache_enabled,
            explain_mode=self.explain_mode,
            rate_limit_enabled=settings.rate_limit_enabled,
        )

    # Legacy property for backwards compatibility
    @property
    def ollama_model(self) -> str:
        """Get the model name (legacy property for backwards compatibility)."""
        return self.provider.model_name

    @property
    def ollama_host(self) -> str:
        """Get the endpoint (legacy property for backwards compatibility)."""
        return self.provider.endpoint

    async def _run_agent_with_retry(self, message: str) -> str:
        """
        Execute agent.run() with retry logic and circuit breaker.

        This internal method wraps the Pydantic AI agent execution
        with retry and circuit breaker patterns.

        Args:
            message: User message

        Returns:
            Agent response text

        Raises:
            ResearchAgentError: If execution fails after retries
        """

        @retry(config=self._retry_config, circuit_breaker=self._circuit_breaker)
        async def _execute():
            async with self.agent:
                result = await self.agent.run(message)
                return result.output

        return await _execute()

    async def chat(
        self,
        message: str,
        _include_history: bool = True,
        use_cache: bool = True,
    ) -> str:
        """
        Send a message to the agent and get a response.

        Args:
            message: User message
            include_history: Include conversation history for context
            use_cache: Use response cache if available

        Returns:
            Agent's response text
        """
        start_time = time.time()

        try:
            logger.info("agent_chat_started", message_length=len(message))

            # Check cache first if enabled
            if use_cache and self.cache.enabled:
                cached_response = self.cache.get(message)
                if cached_response is not None:
                    duration_ms = (time.time() - start_time) * 1000
                    logger.info(
                        "agent_chat_cache_hit",
                        duration_ms=round(duration_ms, 2),
                        response_length=len(cached_response),
                    )

                    # Record conversation turn (still track even for cached responses)
                    turn = ConversationTurn(
                        user_message=ChatMessage.user(message),
                        assistant_message=ChatMessage.assistant(cached_response),
                        duration_ms=duration_ms,
                    )
                    self.conversation.add_turn(turn)

                    return cached_response

            # Apply rate limiting if enabled
            await self.rate_limiter.acquire()

            # Run agent with retry logic and circuit breaker
            response_text = await self._run_agent_with_retry(message)

            duration_ms = (time.time() - start_time) * 1000

            # Cache the response
            if use_cache and self.cache.enabled:
                self.cache.set(message, response_text)

            # Record conversation turn
            turn = ConversationTurn(
                user_message=ChatMessage.user(message),
                assistant_message=ChatMessage.assistant(response_text),
                duration_ms=duration_ms,
            )
            self.conversation.add_turn(turn)

            logger.info(
                "agent_chat_completed",
                duration_ms=round(duration_ms, 2),
                response_length=len(response_text),
                cached=use_cache and self.cache.enabled,
            )

            return response_text

        except Exception as e:
            logger.error("agent_chat_error", error=str(e))
            raise ResearchAgentError(f"Chat failed: {e}") from e

    async def chat_stream(self, message: str) -> AsyncIterator[str]:
        """
        Stream a response from the agent, yielding text chunks.

        Uses run() internally to ensure tool calls are properly executed,
        then yields the response in chunks for a streaming-like experience.

        Token usage and duration are stored and can be retrieved via
        get_last_response_stats() after streaming completes.

        Args:
            message: User message

        Yields:
            Text chunks (deltas) as they are generated

        Example:
            async for chunk in agent.chat_stream("What tables are available?"):
                print(chunk, end="", flush=True)
            stats = agent.get_last_response_stats()
            print(f"Tokens: {stats['token_usage']}")
        """
        start_time = time.time()
        full_response = ""

        try:
            logger.info("agent_stream_started", message_length=len(message))

            # Apply rate limiting if enabled
            await self.rate_limiter.acquire()

            # Run agent with retry logic (streaming simulation)
            @retry(config=self._retry_config, circuit_breaker=self._circuit_breaker)
            async def _execute_stream():
                async with self.agent:
                    # Use run() instead of run_stream() to ensure tool calls are executed
                    # run_stream() stops after first output which breaks tool execution
                    result = await self.agent.run(message)
                    return result.output, TokenUsage.from_pydantic_usage(result.usage())

            full_response, token_usage = await _execute_stream()

            # Simulate streaming by yielding chunks of the response
            # This ensures tools execute while still providing a streaming-like UX
            chunk_size = 20  # Characters per chunk
            for i in range(0, len(full_response), chunk_size):
                chunk = full_response[i : i + chunk_size]
                yield chunk

            duration_ms = (time.time() - start_time) * 1000

            # Store stats for later retrieval
            self._stats_manager.set_last_response(token_usage, duration_ms)

            # Record conversation turn after streaming completes
            turn = ConversationTurn(
                user_message=ChatMessage.user(message),
                assistant_message=ChatMessage.assistant(full_response),
                duration_ms=duration_ms,
            )
            self.conversation.add_turn(turn)

            logger.info(
                "agent_stream_completed",
                duration_ms=round(duration_ms, 2),
                response_length=len(full_response),
                tokens=token_usage.total_tokens if token_usage else 0,
            )

        except Exception as e:
            logger.error("agent_stream_error", error=str(e))
            raise ResearchAgentError(f"Stream failed: {e}") from e

    async def chat_with_details(self, message: str) -> AgentResponse:
        """
        Send a message and get a detailed response with metadata.

        Args:
            message: User message

        Returns:
            AgentResponse with content, metadata, and token usage
        """
        start_time = time.time()

        try:
            # Run with retry logic
            @retry(config=self._retry_config, circuit_breaker=self._circuit_breaker)
            async def _execute_with_details():
                async with self.agent:
                    result = await self.agent.run(message)
                    return result.output, TokenUsage.from_pydantic_usage(result.usage())

            response_text, token_usage = await _execute_with_details()

            duration_ms = (time.time() - start_time) * 1000

            return AgentResponse(
                content=response_text,
                duration_ms=duration_ms,
                model=self.provider.model_name,
                token_usage=token_usage,
            )

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            return AgentResponse(
                content="",
                duration_ms=duration_ms,
                model=self.provider.model_name,
                error=str(e),
            )

    def get_last_response_stats(self) -> dict:
        """Get statistics from the last response (useful after streaming)."""
        return self._stats_manager.get_last_response_stats()

    def clear_history(self) -> None:
        """Clear conversation history."""
        self.conversation = Conversation()
        logger.info("conversation_history_cleared")

    def get_history(self, max_turns: int = 10) -> list[dict[str, str]]:
        """
        Get conversation history for context.

        Args:
            max_turns: Maximum turns to return

        Returns:
            List of message dictionaries
        """
        return self.conversation.get_history_for_context(max_turns)

    @property
    def turn_count(self) -> int:
        """Get number of conversation turns."""
        return self.conversation.total_turns

    # Cache management methods (delegate to cache manager)
    @property
    def cache_enabled(self) -> bool:
        """Check if caching is enabled."""
        return self._cache_manager.cache_enabled

    @cache_enabled.setter
    def cache_enabled(self, value: bool) -> None:
        """Enable or disable caching."""
        self._cache_manager.cache_enabled = value
        self._cache_enabled = value

    def get_cache_stats(self):
        """Get current cache statistics."""
        return self._cache_manager.get_cache_stats()

    def clear_cache(self) -> int:
        """
        Clear the response cache.

        Returns:
            Number of entries cleared
        """
        return self._cache_manager.clear_cache()

    def invalidate_cache(self, query: str) -> bool:
        """
        Invalidate a specific cache entry.

        Args:
            query: The query to invalidate

        Returns:
            True if entry was found and removed
        """
        return self._cache_manager.invalidate_cache(query)

    # Rate limiting methods (delegate to stats manager)
    def get_rate_limit_stats(self):
        """Get current rate limiting statistics."""
        return self._stats_manager.get_rate_limit_stats()

    def reset_rate_limit_stats(self) -> None:
        """Reset rate limiting statistics."""
        self._stats_manager.reset_rate_limit_stats()

    @property
    def rate_limit_enabled(self) -> bool:
        """Check if rate limiting is enabled."""
        return self._stats_manager.rate_limit_enabled

    @rate_limit_enabled.setter
    def rate_limit_enabled(self, value: bool) -> None:
        """Enable or disable rate limiting."""
        self._stats_manager.rate_limit_enabled = value


# Factory function for easy agent creation
def create_research_agent(
    provider_type: ProviderType | str | None = None,
    model_name: str | None = None,
    readonly: bool | None = None,
    minimal_prompt: bool = False,
    cache_enabled: bool | None = None,
    explain_mode: bool = False,
) -> ResearchAgent:
    """
    Create a configured research agent.

    Args:
        provider_type: LLM provider ('ollama' or 'foundry_local')
        model_name: Model name/alias to use
        readonly: Enable read-only mode
        minimal_prompt: Use minimal system prompt
        cache_enabled: Enable response caching
        explain_mode: Enable educational query explanations

    Returns:
        Configured ResearchAgent instance
    """
    return ResearchAgent(
        provider_type=provider_type,
        model_name=model_name,
        readonly=readonly,
        minimal_prompt=minimal_prompt,
        cache_enabled=cache_enabled,
        explain_mode=explain_mode,
    )
