"""
Research Agent

The main AI agent that uses local LLM providers (Ollama or Foundry Local)
for inference and MCP tools for SQL Server data access.
"""

import time
from collections.abc import AsyncIterator
from typing import Any

from pydantic_ai import Agent

from src.agent.prompts import get_system_prompt
from src.mcp.client import MCPClientManager
from src.models.chat import AgentResponse, ChatMessage, Conversation, ConversationTurn
from src.providers import LLMProvider, ProviderType, create_provider
from src.utils.cache import CacheStats, ResponseCache, get_response_cache
from src.utils.config import settings
from src.utils.logger import get_logger
from src.utils.rate_limiter import RateLimitStats, get_rate_limiter

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

            # Run agent with MCP server context
            async with self.agent:
                result = await self.agent.run(message)
                response_text = result.output

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

        Args:
            message: User message

        Yields:
            Text chunks as they are generated

        Example:
            async for chunk in agent.chat_stream("What tables are available?"):
                print(chunk, end="", flush=True)
        """
        start_time = time.time()
        full_response = ""

        try:
            logger.info("agent_stream_started", message_length=len(message))

            # Apply rate limiting if enabled
            await self.rate_limiter.acquire()

            async with self.agent:
                async with self.agent.run_stream(message) as stream:
                    async for chunk in stream.stream_text():
                        full_response += chunk
                        yield chunk

            duration_ms = (time.time() - start_time) * 1000

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
            AgentResponse with content and metadata
        """
        start_time = time.time()

        try:
            async with self.agent:
                result = await self.agent.run(message)
                response_text = result.output

            duration_ms = (time.time() - start_time) * 1000

            return AgentResponse(
                content=response_text,
                duration_ms=duration_ms,
                model=self.ollama_model,
            )

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            return AgentResponse(
                content="",
                duration_ms=duration_ms,
                model=self.ollama_model,
                error=str(e),
            )

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

    # Cache management methods
    @property
    def cache_enabled(self) -> bool:
        """Check if caching is enabled."""
        return self.cache.enabled

    @cache_enabled.setter
    def cache_enabled(self, value: bool) -> None:
        """Enable or disable caching."""
        self.cache.enabled = value
        self._cache_enabled = value

    def get_cache_stats(self) -> CacheStats:
        """Get current cache statistics."""
        return self.cache.get_stats()

    def clear_cache(self) -> int:
        """
        Clear the response cache.

        Returns:
            Number of entries cleared
        """
        return self.cache.clear()

    def invalidate_cache(self, query: str) -> bool:
        """
        Invalidate a specific cache entry.

        Args:
            query: The query to invalidate

        Returns:
            True if entry was found and removed
        """
        return self.cache.invalidate(query)

    # Rate limiting methods
    def get_rate_limit_stats(self) -> RateLimitStats:
        """Get current rate limiting statistics."""
        return self.rate_limiter.get_stats()

    def reset_rate_limit_stats(self) -> None:
        """Reset rate limiting statistics."""
        self.rate_limiter.reset_stats()

    @property
    def rate_limit_enabled(self) -> bool:
        """Check if rate limiting is enabled."""
        return self.rate_limiter.enabled

    @rate_limit_enabled.setter
    def rate_limit_enabled(self, value: bool) -> None:
        """Enable or disable rate limiting."""
        self.rate_limiter.enabled = value


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


# Async context manager for one-shot queries
class ResearchAgentContext:
    """
    Context manager for one-shot agent queries.

    Usage:
        async with ResearchAgentContext() as agent:
            response = await agent.chat("What tables are available?")

        # With Foundry Local:
        async with ResearchAgentContext(provider_type="foundry_local") as agent:
            response = await agent.chat("What tables are available?")
    """

    def __init__(
        self,
        provider_type: ProviderType | str | None = None,
        readonly: bool = True,
    ):
        self.provider_type = provider_type
        self.readonly = readonly
        self._agent: ResearchAgent | None = None

    async def __aenter__(self) -> ResearchAgent:
        self._agent = create_research_agent(
            provider_type=self.provider_type,
            readonly=self.readonly,
        )
        return self._agent

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self._agent = None
