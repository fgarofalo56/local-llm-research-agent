"""
Integration Tests

End-to-end integration tests for the research agent.
Tests actual agent functionality with mocked MCP servers.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.agent.research_agent import ResearchAgent, ResearchAgentError, create_research_agent
from src.providers import ProviderType


@pytest.mark.integration
class TestAgentWithOllamaProvider:
    """Integration tests for agent with Ollama provider."""

    @pytest.mark.asyncio
    @patch("src.agent.research_agent.MCPClientManager")
    @patch("src.providers.ollama.OllamaProvider.check_connection")
    @patch("src.agent.research_agent.Agent")
    async def test_agent_chat_with_ollama(
        self, mock_agent_cls, mock_check_conn, mock_mcp_cls
    ):
        """Test complete chat flow with Ollama provider."""
        # Setup MCP mock
        mock_mcp = MagicMock()
        mock_mcp.get_mssql_server.return_value = MagicMock()
        mock_mcp_cls.return_value = mock_mcp

        # Setup provider check
        status = MagicMock()
        status.available = True
        mock_check_conn.return_value = status

        # Setup agent mock
        mock_result = MagicMock()
        mock_result.output = "The database has 5 tables: Users, Orders, Products, Categories, Reviews."

        mock_agent_instance = MagicMock()
        mock_agent_instance.__aenter__ = AsyncMock(return_value=mock_agent_instance)
        mock_agent_instance.__aexit__ = AsyncMock(return_value=None)
        mock_agent_instance.run = AsyncMock(return_value=mock_result)
        mock_agent_cls.return_value = mock_agent_instance

        # Test
        agent = ResearchAgent(provider_type="ollama")
        response = await agent.chat("What tables are in the database?")

        assert "tables" in response.lower()
        assert agent.turn_count == 1

    @pytest.mark.asyncio
    @patch("src.agent.research_agent.MCPClientManager")
    @patch("src.agent.research_agent.Agent")
    async def test_agent_streaming_with_ollama(self, mock_agent_cls, mock_mcp_cls):
        """Test streaming responses with Ollama provider."""
        # Setup MCP mock
        mock_mcp = MagicMock()
        mock_mcp.get_mssql_server.return_value = MagicMock()
        mock_mcp_cls.return_value = mock_mcp

        # Setup streaming mock
        async def mock_stream_text():
            chunks = ["Found ", "3 ", "tables: ", "Users, ", "Orders, ", "Products."]
            for chunk in chunks:
                yield chunk

        mock_stream = MagicMock()
        mock_stream.stream_text = mock_stream_text

        mock_stream_context = MagicMock()
        mock_stream_context.__aenter__ = AsyncMock(return_value=mock_stream)
        mock_stream_context.__aexit__ = AsyncMock(return_value=None)

        mock_agent_instance = MagicMock()
        mock_agent_instance.__aenter__ = AsyncMock(return_value=mock_agent_instance)
        mock_agent_instance.__aexit__ = AsyncMock(return_value=None)
        mock_agent_instance.run_stream = MagicMock(return_value=mock_stream_context)
        mock_agent_cls.return_value = mock_agent_instance

        # Test
        agent = ResearchAgent(provider_type="ollama")
        chunks = []
        async for chunk in agent.chat_stream("List tables"):
            chunks.append(chunk)

        full_response = "".join(chunks)
        assert "tables" in full_response.lower()
        assert len(chunks) > 1  # Should have multiple chunks


@pytest.mark.integration
class TestAgentWithFoundryProvider:
    """Integration tests for agent with Foundry Local provider."""

    @pytest.mark.asyncio
    @patch("src.agent.research_agent.MCPClientManager")
    @patch("src.providers.foundry.FoundryLocalProvider.check_connection")
    @patch("src.agent.research_agent.Agent")
    async def test_agent_chat_with_foundry(
        self, mock_agent_cls, mock_check_conn, mock_mcp_cls
    ):
        """Test complete chat flow with Foundry Local provider."""
        # Setup MCP mock
        mock_mcp = MagicMock()
        mock_mcp.get_mssql_server.return_value = MagicMock()
        mock_mcp_cls.return_value = mock_mcp

        # Setup provider check
        status = MagicMock()
        status.available = True
        mock_check_conn.return_value = status

        # Setup agent mock
        mock_result = MagicMock()
        mock_result.output = "There are 10 users in the database."

        mock_agent_instance = MagicMock()
        mock_agent_instance.__aenter__ = AsyncMock(return_value=mock_agent_instance)
        mock_agent_instance.__aexit__ = AsyncMock(return_value=None)
        mock_agent_instance.run = AsyncMock(return_value=mock_result)
        mock_agent_cls.return_value = mock_agent_instance

        # Test
        agent = ResearchAgent(provider_type="foundry_local")
        response = await agent.chat("How many users are in the database?")

        assert "users" in response.lower()
        mock_agent_instance.run.assert_called_once()


@pytest.mark.integration
class TestProviderSwitching:
    """Tests for switching between providers."""

    @patch("src.agent.research_agent.MCPClientManager")
    @patch("src.agent.research_agent.Agent")
    def test_create_agent_with_ollama(self, mock_agent_cls, mock_mcp_cls):
        """Test creating agent with Ollama provider."""
        mock_mcp = MagicMock()
        mock_mcp.get_mssql_server.return_value = MagicMock()
        mock_mcp_cls.return_value = mock_mcp

        agent = create_research_agent(provider_type="ollama")

        assert agent.provider.provider_type == ProviderType.OLLAMA

    @patch("src.agent.research_agent.MCPClientManager")
    @patch("src.agent.research_agent.Agent")
    def test_create_agent_with_foundry(self, mock_agent_cls, mock_mcp_cls):
        """Test creating agent with Foundry Local provider."""
        mock_mcp = MagicMock()
        mock_mcp.get_mssql_server.return_value = MagicMock()
        mock_mcp_cls.return_value = mock_mcp

        agent = create_research_agent(provider_type="foundry_local")

        assert agent.provider.provider_type == ProviderType.FOUNDRY_LOCAL

    @patch("src.agent.research_agent.MCPClientManager")
    @patch("src.agent.research_agent.Agent")
    def test_legacy_ollama_parameters(self, mock_agent_cls, mock_mcp_cls):
        """Test legacy ollama_host and ollama_model parameters still work."""
        mock_mcp = MagicMock()
        mock_mcp.get_mssql_server.return_value = MagicMock()
        mock_mcp_cls.return_value = mock_mcp

        agent = ResearchAgent(
            ollama_host="http://custom:11434",
            ollama_model="llama3.1:8b",
        )

        # endpoint now includes /v1 suffix for OpenAI compatibility
        assert agent.ollama_host == "http://custom:11434/v1"
        assert agent.ollama_model == "llama3.1:8b"


@pytest.mark.integration
class TestConversationManagement:
    """Tests for conversation history management across providers."""

    @pytest.mark.asyncio
    @patch("src.agent.research_agent.MCPClientManager")
    @patch("src.agent.research_agent.Agent")
    async def test_conversation_history_tracking(self, mock_agent_cls, mock_mcp_cls):
        """Test that conversation history is properly tracked."""
        mock_mcp = MagicMock()
        mock_mcp.get_mssql_server.return_value = MagicMock()
        mock_mcp_cls.return_value = mock_mcp

        # Setup responses
        responses = [
            "The Users table has columns: id, name, email.",
            "The Orders table has columns: id, user_id, total.",
        ]
        response_idx = 0

        def get_response(message):
            nonlocal response_idx
            result = MagicMock()
            result.output = responses[min(response_idx, len(responses) - 1)]
            response_idx += 1
            return result

        mock_agent_instance = MagicMock()
        mock_agent_instance.__aenter__ = AsyncMock(return_value=mock_agent_instance)
        mock_agent_instance.__aexit__ = AsyncMock(return_value=None)
        mock_agent_instance.run = AsyncMock(side_effect=get_response)
        mock_agent_cls.return_value = mock_agent_instance

        agent = ResearchAgent()

        # Multiple chat turns
        await agent.chat("Describe the Users table")
        await agent.chat("Describe the Orders table")

        assert agent.turn_count == 2
        history = agent.get_history()
        assert len(history) == 4  # 2 user + 2 assistant messages

    @patch("src.agent.research_agent.MCPClientManager")
    @patch("src.agent.research_agent.Agent")
    def test_clear_history(self, mock_agent_cls, mock_mcp_cls):
        """Test clearing conversation history."""
        mock_mcp = MagicMock()
        mock_mcp.get_mssql_server.return_value = MagicMock()
        mock_mcp_cls.return_value = mock_mcp

        agent = ResearchAgent()
        agent.clear_history()

        assert agent.turn_count == 0
        assert agent.get_history() == []


@pytest.mark.integration
class TestErrorHandling:
    """Tests for error handling in integration scenarios."""

    @pytest.mark.asyncio
    @patch("src.agent.research_agent.MCPClientManager")
    @patch("src.agent.research_agent.Agent")
    async def test_mcp_connection_error(self, mock_agent_cls, mock_mcp_cls):
        """Test handling MCP server connection errors."""
        mock_mcp = MagicMock()
        mock_mcp.get_mssql_server.return_value = MagicMock()
        mock_mcp_cls.return_value = mock_mcp

        mock_agent_instance = MagicMock()
        mock_agent_instance.__aenter__ = AsyncMock(return_value=mock_agent_instance)
        mock_agent_instance.__aexit__ = AsyncMock(return_value=None)
        mock_agent_instance.run = AsyncMock(
            side_effect=Exception("MCP server not responding")
        )
        mock_agent_cls.return_value = mock_agent_instance

        agent = ResearchAgent()

        with pytest.raises(ResearchAgentError) as exc_info:
            await agent.chat("Test message")

        assert "Chat failed" in str(exc_info.value)

    @pytest.mark.asyncio
    @patch("src.agent.research_agent.MCPClientManager")
    @patch("src.agent.research_agent.Agent")
    async def test_stream_error_handling(self, mock_agent_cls, mock_mcp_cls):
        """Test error handling during streaming."""
        mock_mcp = MagicMock()
        mock_mcp.get_mssql_server.return_value = MagicMock()
        mock_mcp_cls.return_value = mock_mcp

        async def mock_stream_error():
            yield "Starting..."
            raise Exception("Stream interrupted")

        mock_stream = MagicMock()
        mock_stream.stream_text = mock_stream_error

        mock_stream_context = MagicMock()
        mock_stream_context.__aenter__ = AsyncMock(return_value=mock_stream)
        mock_stream_context.__aexit__ = AsyncMock(return_value=None)

        mock_agent_instance = MagicMock()
        mock_agent_instance.__aenter__ = AsyncMock(return_value=mock_agent_instance)
        mock_agent_instance.__aexit__ = AsyncMock(return_value=None)
        mock_agent_instance.run_stream = MagicMock(return_value=mock_stream_context)
        mock_agent_cls.return_value = mock_agent_instance

        agent = ResearchAgent()

        with pytest.raises(ResearchAgentError) as exc_info:
            async for _ in agent.chat_stream("Test"):
                pass

        assert "Stream failed" in str(exc_info.value)


@pytest.mark.integration
class TestReadOnlyMode:
    """Tests for read-only mode functionality."""

    @patch("src.agent.research_agent.MCPClientManager")
    @patch("src.agent.research_agent.Agent")
    def test_readonly_mode_prompt(self, mock_agent_cls, mock_mcp_cls):
        """Test that read-only mode is reflected in system prompt."""
        mock_mcp = MagicMock()
        mock_mcp.get_mssql_server.return_value = MagicMock()
        mock_mcp_cls.return_value = mock_mcp

        agent = ResearchAgent(readonly=True)

        # Agent was created with readonly flag
        assert agent.readonly is True

    @patch("src.agent.research_agent.MCPClientManager")
    @patch("src.agent.research_agent.Agent")
    def test_write_mode(self, mock_agent_cls, mock_mcp_cls):
        """Test write mode configuration."""
        mock_mcp = MagicMock()
        mock_mcp.get_mssql_server.return_value = MagicMock()
        mock_mcp_cls.return_value = mock_mcp

        agent = ResearchAgent(readonly=False)

        assert agent.readonly is False
