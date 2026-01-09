"""
Core Research Agent Implementation

The main AI agent that uses local LLM providers (Ollama or Foundry Local)
for inference and MCP tools for SQL Server data access.
"""

import time
from collections.abc import AsyncIterator

from pydantic_ai import Agent

from src.agent.cache import AgentCache
from src.agent.prompts import get_system_prompt, format_mcp_servers_info
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
    Universal research and tools assistant.

    Supports data analysis, general questions, code assistance, and research.
    Uses local LLM providers (Ollama or Foundry Local) for inference
    and MCP servers for database/tool access.
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
        thinking_mode: bool = False,
        mcp_servers: list | None = None,  # List of MCP server names to enable
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
            thinking_mode: Enable step-by-step reasoning mode
            mcp_servers: List of MCP server names to enable (e.g., ['mssql', 'brave'])
            ollama_host: (Legacy) Ollama server URL
            ollama_model: (Legacy) Ollama model name
        """
        self.readonly = readonly if readonly is not None else settings.mcp_mssql_readonly
        self.minimal_prompt = minimal_prompt
        self.explain_mode = explain_mode
        self.thinking_mode = thinking_mode
        self._enabled_mcp_servers = mcp_servers or ["mssql"]  # Default to MSSQL for compatibility

        # Initialize response cache
        self._cache_enabled = cache_enabled if cache_enabled is not None else settings.cache_enabled
        self.cache: ResponseCache[str] = get_response_cache(
            max_size=settings.cache_max_size,
            ttl_seconds=settings.cache_ttl_seconds,
            enabled=self._cache_enabled,
        )

        # Initialize MCP components
        self.mcp_manager = MCPClientManager()
        
        # Active toolsets will be loaded in initialize()
        self._active_toolsets = []

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

        # Check for tool calling support and warn if not supported
        self._tool_warning: str | None = None
        if not self.provider.supports_tool_calling():
            # Get detailed warning message if available
            if hasattr(self.provider, "get_tool_calling_warning"):
                self._tool_warning = self.provider.get_tool_calling_warning()
            else:
                self._tool_warning = (
                    f"Model '{self.provider.model_name}' may not support tool calling. "
                    "MCP tools may not work correctly."
                )
            logger.warning(
                "model_tool_calling_not_supported",
                provider=self.provider.provider_type.value,
                model=self.provider.model_name,
                warning=self._tool_warning,
            )

        # Conversation tracking
        self.conversation = Conversation()
        
        # Agent will be created in initialize()
        self.agent = None

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

        # Load MCP toolsets and create the Pydantic AI agent
        self._load_toolsets()
        
        # Create agent with loaded toolsets
        enabled_server_names = [s.name for s in self.mcp_manager.list_servers() if s.enabled]
        mcp_info = format_mcp_servers_info(enabled_server_names)
        
        self.agent = Agent(
            model=self.model,
            system_prompt=get_system_prompt(
                readonly=self.readonly,
                minimal=self.minimal_prompt,
                explain_mode=self.explain_mode,
                thinking_mode=self.thinking_mode,
                mcp_servers_info=mcp_info,
            ),
            toolsets=self._active_toolsets,
        )

        logger.info(
            "research_agent_created",
            provider=self.provider.provider_type.value,
            model=self.provider.model_name,
            readonly=self.readonly,
            cache_enabled=self._cache_enabled,
            explain_mode=self.explain_mode,
            thinking_mode=self.thinking_mode,
            rate_limit_enabled=settings.rate_limit_enabled,
            tool_calling_supported=self.provider.supports_tool_calling(),
            active_toolsets=len(self._active_toolsets),
            enabled_servers=enabled_server_names,
        )

    async def initialize(self) -> None:
        """
        Initialize MCP toolsets and create the agent.
        
        DEPRECATED: Initialization now happens in __init__.
        This method is kept for backward compatibility and does nothing.
        """
        pass

    def _load_toolsets(self) -> None:
        """
        Load MCP server toolsets based on enabled servers list.
        
        Gracefully handles failures - agent continues without failed tools.
        """
        # Load configuration first
        self.mcp_manager.load_config()
        
        # Get active toolsets from the manager
        self._active_toolsets = self.mcp_manager.get_active_toolsets()
        
        logger.info("mcp_toolsets_loaded", count=len(self._active_toolsets))
        
        if not self._active_toolsets:
            logger.warning(
                "no_toolsets_loaded",
                message="Agent will operate without MCP tools - can still answer general questions",
            )

    @property
    def tool_warning(self) -> str | None:
        """Get tool calling warning message if model doesn't support tools."""
        return self._tool_warning

    @property
    def supports_tool_calling(self) -> bool:
        """Check if the current model supports tool calling."""
        return self.provider.supports_tool_calling()

    # Legacy property for backwards compatibility
    @property
    def ollama_model(self) -> str:
        """Get the model name (legacy property for backwards compatibility)."""
        return self.provider.model_name

    @property
    def ollama_host(self) -> str:
        """Get the endpoint (legacy property for backwards compatibility)."""
        return self.provider.endpoint

    async def __aenter__(self):
        """
        Enter the agent context.
        
        This establishes MCP server connections once at the start of a session,
        rather than reconnecting on every message.
        """
        await self.agent.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """
        Exit the agent context.
        
        This cleanly closes MCP server connections at the end of the session.
        """
        return await self.agent.__aexit__(exc_type, exc_val, exc_tb)

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
            # Agent context is managed at session level, not per-message
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
                # Agent context is managed at session level, not per-message
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
                # Agent context is managed at session level, not per-message
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
async def create_research_agent(
    provider_type: ProviderType | str | None = None,
    model_name: str | None = None,
    readonly: bool | None = None,
    minimal_prompt: bool = False,
    cache_enabled: bool | None = None,
    explain_mode: bool = False,
    thinking_mode: bool = False,
    mcp_servers: list | None = None,
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
        thinking_mode: Enable step-by-step reasoning mode
        mcp_servers: List of MCP server instances to use as toolsets

    Returns:
        Configured and initialized ResearchAgent instance
    """
    agent = ResearchAgent(
        provider_type=provider_type,
        model_name=model_name,
        readonly=readonly,
        minimal_prompt=minimal_prompt,
        cache_enabled=cache_enabled,
        explain_mode=explain_mode,
        thinking_mode=thinking_mode,
        mcp_servers=mcp_servers,
    )
    await agent.initialize()
    return agent
