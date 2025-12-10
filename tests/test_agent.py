"""
Tests for the Research Agent

Tests for agent initialization, chat functionality, and error handling.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.agent.prompts import get_system_prompt
from src.agent.research_agent import ResearchAgent, ResearchAgentError


class TestSystemPrompts:
    """Tests for system prompt generation."""

    def test_get_system_prompt_default(self):
        """Test default system prompt."""
        prompt = get_system_prompt()
        assert "SQL data analyst" in prompt
        assert "list_tables" in prompt

    def test_get_system_prompt_readonly(self):
        """Test read-only system prompt."""
        prompt = get_system_prompt(readonly=True)
        assert "READ-ONLY" in prompt
        assert "cannot modify data" in prompt.lower()

    def test_get_system_prompt_minimal(self):
        """Test minimal system prompt."""
        prompt = get_system_prompt(minimal=True)
        assert len(prompt) < 500  # Minimal prompt should be short


class TestResearchAgentInit:
    """Tests for ResearchAgent initialization."""

    @patch("src.agent.research_agent.MCPClientManager")
    @patch("src.agent.research_agent.create_provider")
    @patch("src.agent.research_agent.Agent")
    def test_init_default_settings(self, mock_agent_cls, mock_create_provider, mock_mcp_cls):
        """Test agent initializes with default settings."""
        mock_mcp = MagicMock()
        mock_mcp.get_mssql_server.return_value = MagicMock()
        mock_mcp_cls.return_value = mock_mcp

        # Mock provider
        mock_provider = MagicMock()
        mock_provider.get_model.return_value = MagicMock()
        mock_provider.model_name = "qwen2.5:7b-instruct"
        mock_provider.endpoint = "http://localhost:11434/v1"
        mock_provider.provider_type = MagicMock()
        mock_provider.provider_type.value = "ollama"
        mock_create_provider.return_value = mock_provider

        agent = ResearchAgent()

        assert agent.ollama_host is not None
        assert agent.ollama_model is not None
        mock_mcp.get_mssql_server.assert_called_once()

    @patch("src.agent.research_agent.MCPClientManager")
    @patch("src.providers.ollama.OllamaProvider")
    @patch("src.agent.research_agent.Agent")
    def test_init_custom_settings(self, mock_agent_cls, mock_ollama_provider_cls, mock_mcp_cls):
        """Test agent initializes with custom settings."""
        mock_mcp = MagicMock()
        mock_mcp.get_mssql_server.return_value = MagicMock()
        mock_mcp_cls.return_value = mock_mcp

        # Mock provider
        mock_provider = MagicMock()
        mock_provider.get_model.return_value = MagicMock()
        mock_provider.model_name = "llama3.1:8b"
        mock_provider.endpoint = "http://custom:11434/v1"
        mock_provider.provider_type = MagicMock()
        mock_provider.provider_type.value = "ollama"
        mock_ollama_provider_cls.return_value = mock_provider

        agent = ResearchAgent(
            ollama_host="http://custom:11434",
            ollama_model="llama3.1:8b",
            readonly=True,
        )

        assert agent.ollama_host == "http://custom:11434/v1"
        assert agent.ollama_model == "llama3.1:8b"
        assert agent.readonly is True


class TestResearchAgentChat:
    """Tests for ResearchAgent chat functionality."""

    @pytest.mark.asyncio
    @patch("src.agent.research_agent.MCPClientManager")
    @patch("src.agent.research_agent.create_provider")
    @patch("src.agent.research_agent.Agent")
    async def test_chat_success(self, mock_agent_cls, mock_create_provider, mock_mcp_cls):
        """Test successful chat response."""
        # Setup mocks
        mock_mcp = MagicMock()
        mock_mcp.get_mssql_server.return_value = MagicMock()
        mock_mcp_cls.return_value = mock_mcp

        # Mock provider
        mock_provider = MagicMock()
        mock_provider.get_model.return_value = MagicMock()
        mock_provider.model_name = "qwen2.5:7b-instruct"
        mock_provider.endpoint = "http://localhost:11434/v1"
        mock_provider.provider_type = MagicMock()
        mock_provider.provider_type.value = "ollama"
        mock_create_provider.return_value = mock_provider

        mock_result = MagicMock()
        mock_result.output = "Found 3 tables."

        mock_agent_instance = MagicMock()
        mock_agent_instance.__aenter__ = AsyncMock(return_value=mock_agent_instance)
        mock_agent_instance.__aexit__ = AsyncMock(return_value=None)
        mock_agent_instance.run = AsyncMock(return_value=mock_result)
        mock_agent_cls.return_value = mock_agent_instance

        agent = ResearchAgent()
        response = await agent.chat("What tables exist?")

        assert response == "Found 3 tables."
        mock_agent_instance.run.assert_called_once_with("What tables exist?")

    @pytest.mark.asyncio
    @patch("src.agent.research_agent.MCPClientManager")
    @patch("src.agent.research_agent.create_provider")
    @patch("src.agent.research_agent.Agent")
    async def test_chat_error_handling(self, mock_agent_cls, mock_create_provider, mock_mcp_cls):
        """Test chat error handling."""
        mock_mcp = MagicMock()
        mock_mcp.get_mssql_server.return_value = MagicMock()
        mock_mcp_cls.return_value = mock_mcp

        # Mock provider
        mock_provider = MagicMock()
        mock_provider.get_model.return_value = MagicMock()
        mock_provider.model_name = "qwen2.5:7b-instruct"
        mock_provider.endpoint = "http://localhost:11434/v1"
        mock_provider.provider_type = MagicMock()
        mock_provider.provider_type.value = "ollama"
        mock_create_provider.return_value = mock_provider

        mock_agent_instance = MagicMock()
        mock_agent_instance.__aenter__ = AsyncMock(return_value=mock_agent_instance)
        mock_agent_instance.__aexit__ = AsyncMock(return_value=None)
        mock_agent_instance.run = AsyncMock(side_effect=Exception("Connection failed"))
        mock_agent_cls.return_value = mock_agent_instance

        agent = ResearchAgent()

        with pytest.raises(ResearchAgentError) as exc_info:
            await agent.chat("Test message")

        assert "Chat failed" in str(exc_info.value)


class TestConversationHistory:
    """Tests for conversation history management."""

    @patch("src.agent.research_agent.MCPClientManager")
    @patch("src.agent.research_agent.create_provider")
    @patch("src.agent.research_agent.Agent")
    def test_clear_history(self, mock_agent_cls, mock_create_provider, mock_mcp_cls):
        """Test clearing conversation history."""
        mock_mcp = MagicMock()
        mock_mcp.get_mssql_server.return_value = MagicMock()
        mock_mcp_cls.return_value = mock_mcp

        # Mock provider
        mock_provider = MagicMock()
        mock_provider.get_model.return_value = MagicMock()
        mock_provider.model_name = "qwen2.5:7b-instruct"
        mock_provider.endpoint = "http://localhost:11434/v1"
        mock_provider.provider_type = MagicMock()
        mock_provider.provider_type.value = "ollama"
        mock_create_provider.return_value = mock_provider

        agent = ResearchAgent()
        agent.clear_history()

        assert agent.turn_count == 0

    @patch("src.agent.research_agent.MCPClientManager")
    @patch("src.agent.research_agent.create_provider")
    @patch("src.agent.research_agent.Agent")
    def test_get_history_empty(self, mock_agent_cls, mock_create_provider, mock_mcp_cls):
        """Test getting empty history."""
        mock_mcp = MagicMock()
        mock_mcp.get_mssql_server.return_value = MagicMock()
        mock_mcp_cls.return_value = mock_mcp

        # Mock provider
        mock_provider = MagicMock()
        mock_provider.get_model.return_value = MagicMock()
        mock_provider.model_name = "qwen2.5:7b-instruct"
        mock_provider.endpoint = "http://localhost:11434/v1"
        mock_provider.provider_type = MagicMock()
        mock_provider.provider_type.value = "ollama"
        mock_create_provider.return_value = mock_provider

        agent = ResearchAgent()
        history = agent.get_history()

        assert history == []
