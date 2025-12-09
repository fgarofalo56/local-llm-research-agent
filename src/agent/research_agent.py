"""
Research Agent

The main AI agent that uses Ollama for inference and MCP tools
for SQL Server data access.
"""

import time
from typing import Any

from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel

from src.agent.prompts import get_system_prompt
from src.mcp.client import MCPClientManager
from src.models.chat import AgentResponse, ChatMessage, Conversation, ConversationTurn
from src.utils.config import settings
from src.utils.logger import get_logger

logger = get_logger(__name__)


class ResearchAgentError(Exception):
    """Base exception for research agent errors."""

    pass


class OllamaConnectionError(ResearchAgentError):
    """Error connecting to Ollama."""

    pass


class ResearchAgent:
    """
    Research agent for SQL Server data analytics.

    Uses Ollama for local LLM inference and MSSQL MCP Server for database access.
    """

    def __init__(
        self,
        ollama_host: str | None = None,
        ollama_model: str | None = None,
        readonly: bool | None = None,
        minimal_prompt: bool = False,
    ):
        """
        Initialize the research agent.

        Args:
            ollama_host: Ollama server URL (default from settings)
            ollama_model: Ollama model name (default from settings)
            readonly: Enable read-only mode (default from settings)
            minimal_prompt: Use minimal system prompt
        """
        self.ollama_host = ollama_host or settings.ollama_host
        self.ollama_model = ollama_model or settings.ollama_model
        self.readonly = readonly if readonly is not None else settings.mcp_mssql_readonly
        self.minimal_prompt = minimal_prompt

        # Initialize components
        self.mcp_manager = MCPClientManager()
        self.mssql_server = self.mcp_manager.get_mssql_server()

        # Configure model
        self.model = OpenAIModel(
            model_name=self.ollama_model,
            base_url=f"{self.ollama_host}/v1",
            api_key="ollama",  # Ollama doesn't validate this
        )

        # Create agent
        self.agent = Agent(
            model=self.model,
            system_prompt=get_system_prompt(readonly=self.readonly, minimal=self.minimal_prompt),
            toolsets=[self.mssql_server],
        )

        # Conversation tracking
        self.conversation = Conversation()

        logger.info(
            "research_agent_initialized",
            model=self.ollama_model,
            readonly=self.readonly,
        )

    async def chat(self, message: str, _include_history: bool = True) -> str:
        """
        Send a message to the agent and get a response.

        Args:
            message: User message
            include_history: Include conversation history for context

        Returns:
            Agent's response text
        """
        start_time = time.time()

        try:
            logger.info("agent_chat_started", message_length=len(message))

            # Run agent with MCP server context
            async with self.agent:
                result = await self.agent.run(message)
                response_text = result.output

            duration_ms = (time.time() - start_time) * 1000

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
            )

            return response_text

        except Exception as e:
            logger.error("agent_chat_error", error=str(e))
            raise ResearchAgentError(f"Chat failed: {e}") from e

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


# Factory function for easy agent creation
def create_research_agent(
    readonly: bool | None = None,
    minimal_prompt: bool = False,
) -> ResearchAgent:
    """
    Create a configured research agent.

    Args:
        readonly: Enable read-only mode
        minimal_prompt: Use minimal system prompt

    Returns:
        Configured ResearchAgent instance
    """
    return ResearchAgent(readonly=readonly, minimal_prompt=minimal_prompt)


# Async context manager for one-shot queries
class ResearchAgentContext:
    """
    Context manager for one-shot agent queries.

    Usage:
        async with ResearchAgentContext() as agent:
            response = await agent.chat("What tables are available?")
    """

    def __init__(self, readonly: bool = True):
        self.readonly = readonly
        self._agent: ResearchAgent | None = None

    async def __aenter__(self) -> ResearchAgent:
        self._agent = create_research_agent(readonly=self.readonly)
        return self._agent

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self._agent = None
