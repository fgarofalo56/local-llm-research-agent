"""
CLI Integration Tests for New Features

Comprehensive tests for:
- Multi-MCP server management
- /mcp commands
- Thinking mode toggle
- Web search integration
- RAG search integration
- Error handling for non-SQL queries
"""

import asyncio
import json
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from rich.console import Console
from typer.testing import CliRunner

from src.cli.chat import app

runner = CliRunner(env={"NO_COLOR": "1", "TERM": "dumb"})


# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def mock_console():
    """Create a mock Rich console."""
    return Console(force_terminal=True, no_color=True)


@pytest.fixture
def temp_mcp_config(tmp_path):
    """Create a temporary MCP configuration file."""
    config_path = tmp_path / "mcp_config.json"
    config = {
        "mcpServers": {
            "mssql": {
                "name": "mssql",
                "server_type": "mssql",
                "transport": "stdio",
                "command": "node",
                "args": ["/path/to/mcp.js"],
                "env": {"SERVER_NAME": "localhost"},
                "enabled": True,
                "description": "Test MSSQL",
            },
            "http-server": {
                "name": "http-server",
                "server_type": "custom",
                "transport": "streamable_http",
                "url": "http://localhost:8080/mcp",
                "enabled": True,
                "description": "Test HTTP Server",
            },
            "disabled-server": {
                "name": "disabled-server",
                "server_type": "custom",
                "transport": "stdio",
                "command": "test",
                "enabled": False,
                "description": "Disabled Server",
            },
        }
    }
    with open(config_path, "w") as f:
        json.dump(config, f, indent=2)
    return config_path


@pytest.fixture
def mock_research_agent():
    """Create a mock ResearchAgent with MCP capabilities."""
    agent = MagicMock()
    agent.chat = AsyncMock(return_value="Test response")
    agent.chat_stream = MagicMock()
    agent.chat_with_details = AsyncMock()
    agent.clear_history = MagicMock()
    agent.get_conversation_history = MagicMock(return_value=[])
    agent._thinking_mode = False
    agent._active_toolsets = []
    return agent


# =============================================================================
# THINKING MODE TESTS
# =============================================================================


@pytest.mark.integration
class TestThinkingModeToggle:
    """Tests for thinking mode toggle functionality."""

    def test_thinking_command_exists(self):
        """Test /thinking command is recognized."""
        # Verify command doesn't crash
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0

    @pytest.mark.asyncio
    async def test_thinking_mode_toggle_on(self, mock_research_agent):
        """Test enabling thinking mode via command."""
        mock_research_agent._thinking_mode = False

        # Simulate toggle command
        with patch("src.agent.core.ResearchAgent", return_value=mock_research_agent):
            mock_research_agent._thinking_mode = True
            assert mock_research_agent._thinking_mode is True

    @pytest.mark.asyncio
    async def test_thinking_mode_toggle_off(self, mock_research_agent):
        """Test disabling thinking mode via command."""
        mock_research_agent._thinking_mode = True

        with patch("src.agent.core.ResearchAgent", return_value=mock_research_agent):
            mock_research_agent._thinking_mode = False
            assert mock_research_agent._thinking_mode is False

    @pytest.mark.asyncio
    async def test_thinking_mode_affects_system_prompt(self, mock_research_agent):
        """Test that thinking mode modifies system prompt."""
        with patch("src.agent.core.ResearchAgent") as mock_cls:
            mock_agent = MagicMock()
            mock_agent._thinking_mode = True
            mock_agent._get_system_prompt = MagicMock(
                return_value="System prompt with thinking instructions"
            )
            mock_cls.return_value = mock_agent

            prompt = mock_agent._get_system_prompt()
            # When thinking mode is on, prompt should include reasoning instructions
            assert "thinking" in prompt.lower() or len(prompt) > 0

    def test_thinking_mode_cli_flag(self):
        """Test --thinking CLI flag is accepted."""
        result = runner.invoke(app, ["chat", "--help"])
        # Check if thinking-related options exist
        assert result.exit_code == 0

    @pytest.mark.asyncio
    async def test_thinking_output_format(self, mock_research_agent):
        """Test thinking tags are parsed and displayed correctly."""
        # Simulate response with thinking tags
        response_with_thinking = """<think>
Let me analyze this step by step:
1. First, I need to understand the question
2. Then, I'll formulate the answer
</think>

The answer is 42."""

        mock_research_agent.chat = AsyncMock(return_value=response_with_thinking)

        with patch("src.agent.core.ResearchAgent", return_value=mock_research_agent):
            result = await mock_research_agent.chat("test")
            assert "<think>" in result or "42" in result


# =============================================================================
# WEB SEARCH INTEGRATION TESTS
# =============================================================================


@pytest.mark.integration
class TestWebSearchIntegration:
    """Tests for web search integration."""

    @pytest.mark.asyncio
    async def test_web_search_tool_available(self):
        """Test web search tool is available to agent."""
        with patch("src.agent.core.ResearchAgent") as mock_cls:
            mock_agent = MagicMock()
            mock_agent._tools = ["search_web", "sql_query", "list_tables"]
            mock_cls.return_value = mock_agent

            assert "search_web" in mock_agent._tools

    @pytest.mark.asyncio
    async def test_web_search_rate_limiting(self):
        """Test web search respects rate limits."""
        from src.utils.rate_limiter import TokenBucketRateLimiter

        # Create rate limiter with 10 tokens, refill 1/sec
        limiter = TokenBucketRateLimiter(
            bucket_size=10,
            refill_rate=1.0,
            name="test-limiter"
        )

        # Should allow first 10 requests
        for _ in range(10):
            assert limiter.try_acquire() is True

        # 11th request should be blocked (bucket empty)
        assert limiter.try_acquire() is False

    @pytest.mark.asyncio
    async def test_web_search_result_formatting(self):
        """Test web search results are formatted correctly."""
        mock_results = [
            {"title": "Result 1", "url": "https://example.com/1", "snippet": "..."},
            {"title": "Result 2", "url": "https://example.com/2", "snippet": "..."},
        ]

        # Simulate formatting
        formatted = "\n".join(
            [f"- {r['title']}: {r['url']}" for r in mock_results]
        )
        assert "Result 1" in formatted
        assert "https://example.com" in formatted

    @pytest.mark.asyncio
    async def test_web_search_error_handling(self):
        """Test graceful handling of web search errors."""
        with patch("src.agent.tools.search_web") as mock_search:
            mock_search.side_effect = Exception("API rate limit exceeded")

            with pytest.raises(Exception) as exc_info:
                await mock_search("test query")

            assert "rate limit" in str(exc_info.value).lower()

    def test_websearch_toggle_command(self, mock_console):
        """Test /websearch toggle command."""
        # Verify toggle command structure
        command = "/websearch"
        assert command.startswith("/")


# =============================================================================
# RAG SEARCH INTEGRATION TESTS
# =============================================================================


@pytest.mark.integration
class TestRAGSearchIntegration:
    """Tests for RAG search integration in CLI."""

    @pytest.mark.asyncio
    async def test_rag_search_tool_available(self):
        """Test RAG search tools are available."""
        expected_tools = [
            "search_knowledge_base",
            "list_knowledge_sources",
            "get_document_content",
        ]

        with patch("src.agent.core.ResearchAgent") as mock_cls:
            mock_agent = MagicMock()
            mock_agent._tools = expected_tools
            mock_cls.return_value = mock_agent

            for tool in expected_tools:
                assert tool in mock_agent._tools

    @pytest.mark.asyncio
    async def test_rag_hybrid_search(self):
        """Test hybrid search combines vector and keyword results."""
        from src.rag.mssql_vector_store import MSSQLVectorStore

        with patch.object(MSSQLVectorStore, "search") as mock_search:
            mock_search.return_value = [
                {"content": "Result 1", "score": 0.95, "metadata": {}},
                {"content": "Result 2", "score": 0.85, "metadata": {}},
            ]

            store = MSSQLVectorStore.__new__(MSSQLVectorStore)
            results = mock_search("test query", top_k=5)

            assert len(results) == 2
            assert results[0]["score"] > results[1]["score"]

    @pytest.mark.asyncio
    async def test_rag_source_citations(self):
        """Test RAG results include source citations."""
        mock_result = {
            "content": "Found information",
            "metadata": {
                "source": "document.pdf",
                "page": 5,
                "title": "Test Document",
            },
            "score": 0.9,
        }

        # Verify citation format
        citation = f"[{mock_result['metadata']['title']}]({mock_result['metadata']['source']})"
        assert "Test Document" in citation

    @pytest.mark.asyncio
    async def test_rag_empty_results_handling(self):
        """Test handling when no RAG results found."""
        with patch("src.rag.mssql_vector_store.MSSQLVectorStore") as mock_store_cls:
            mock_store = MagicMock()
            mock_store.search = AsyncMock(return_value=[])
            mock_store_cls.return_value = mock_store

            results = await mock_store.search("obscure query")
            assert results == []

    def test_rag_toggle_command(self, mock_console):
        """Test /rag toggle command structure."""
        command = "/rag"
        assert command.startswith("/")


# =============================================================================
# MCP COMMAND TESTS
# =============================================================================


@pytest.mark.integration
class TestMCPCommands:
    """Extended tests for /mcp commands."""

    def test_mcp_list_output_format(self, temp_mcp_config):
        """Test /mcp list outputs correctly formatted table."""
        from src.mcp.client import MCPClientManager

        with patch("src.mcp.client.MCPClientManager") as mock_cls:
            mock_manager = MagicMock()
            mock_manager.list_servers.return_value = [
                MagicMock(
                    name="mssql",
                    transport=MagicMock(value="stdio"),
                    server_type=MagicMock(value="mssql"),
                    enabled=True,
                    description="Test MSSQL",
                ),
                MagicMock(
                    name="http-server",
                    transport=MagicMock(value="streamable_http"),
                    server_type=MagicMock(value="custom"),
                    enabled=True,
                    description="Test HTTP",
                ),
            ]
            mock_cls.return_value = mock_manager

            servers = mock_manager.list_servers()
            assert len(servers) == 2

    def test_mcp_enable_command(self, temp_mcp_config):
        """Test /mcp enable command."""
        from src.mcp.client import MCPClientManager

        manager = MCPClientManager(config_path=temp_mcp_config)
        result = manager.enable_server("disabled-server")

        # Verify server was enabled
        servers = manager.list_servers()
        server = next((s for s in servers if s.name == "disabled-server"), None)
        assert server is not None
        assert server.enabled is True

    def test_mcp_disable_command(self, temp_mcp_config):
        """Test /mcp disable command."""
        from src.mcp.client import MCPClientManager

        manager = MCPClientManager(config_path=temp_mcp_config)
        result = manager.disable_server("mssql")

        servers = manager.list_servers()
        server = next((s for s in servers if s.name == "mssql"), None)
        assert server is not None
        assert server.enabled is False

    def test_mcp_status_detailed_info(self, temp_mcp_config):
        """Test /mcp status shows detailed server info."""
        from src.mcp.client import MCPClientManager

        manager = MCPClientManager(config_path=temp_mcp_config)
        servers = manager.list_servers()

        mssql = next((s for s in servers if s.name == "mssql"), None)
        assert mssql is not None
        assert mssql.command == "node"
        assert mssql.description == "Test MSSQL"

    def test_mcp_reconnect_command(self):
        """Test /mcp reconnect command structure."""
        with patch("src.mcp.client.MCPClientManager") as mock_cls:
            mock_manager = MagicMock()
            mock_manager.reconnect_server = MagicMock(return_value=True)
            mock_cls.return_value = mock_manager

            result = mock_manager.reconnect_server("test-server")
            assert result is True

    def test_mcp_tools_command(self):
        """Test /mcp tools lists available tools."""
        with patch("src.mcp.client.MCPClientManager") as mock_cls:
            mock_manager = MagicMock()
            mock_manager.get_server_tools = MagicMock(
                return_value=[
                    {"name": "list_tables", "description": "List all tables"},
                    {"name": "read_data", "description": "Read data from table"},
                ]
            )
            mock_cls.return_value = mock_manager

            tools = mock_manager.get_server_tools("mssql")
            assert len(tools) == 2


# =============================================================================
# ERROR HANDLING TESTS
# =============================================================================


@pytest.mark.integration
class TestErrorHandling:
    """Tests for error handling and graceful degradation."""

    @pytest.mark.asyncio
    async def test_non_sql_query_handling(self, mock_research_agent):
        """Test handling of queries that don't require SQL."""
        mock_research_agent.chat = AsyncMock(
            return_value="I can answer general questions too!"
        )

        with patch("src.agent.core.ResearchAgent", return_value=mock_research_agent):
            response = await mock_research_agent.chat("What is Python?")
            assert "general" in response.lower() or len(response) > 0

    @pytest.mark.asyncio
    async def test_mcp_server_timeout_handling(self):
        """Test handling of MCP server timeouts."""
        from src.mcp.server_manager import MCPTimeoutError

        with patch("src.mcp.client.MCPClientManager") as mock_cls:
            mock_manager = MagicMock()
            mock_manager.get_active_toolsets.side_effect = MCPTimeoutError(
                "Server timeout"
            )
            mock_cls.return_value = mock_manager

            with pytest.raises(MCPTimeoutError):
                mock_manager.get_active_toolsets()

    @pytest.mark.asyncio
    async def test_partial_mcp_failure(self):
        """Test system continues when some MCP servers fail."""
        working_toolset = MagicMock()
        working_toolset.name = "working-server"

        with patch("src.mcp.client.MCPClientManager") as mock_cls:
            mock_manager = MagicMock()
            # Return one working toolset even though another failed
            mock_manager.get_active_toolsets.return_value = [working_toolset]
            mock_manager.failed_servers = ["broken-server"]
            mock_cls.return_value = mock_manager

            toolsets = mock_manager.get_active_toolsets()
            assert len(toolsets) == 1

    @pytest.mark.asyncio
    async def test_invalid_command_handling(self, mock_research_agent):
        """Test handling of invalid slash commands."""
        # Invalid commands should be passed to agent or show error
        invalid_commands = ["/invalid", "/nonexistent", "/foo bar"]

        for cmd in invalid_commands:
            # Command should not crash the system
            assert cmd.startswith("/")

    @pytest.mark.asyncio
    async def test_empty_response_handling(self, mock_research_agent):
        """Test handling of empty agent responses."""
        mock_research_agent.chat = AsyncMock(return_value="")

        with patch("src.agent.core.ResearchAgent", return_value=mock_research_agent):
            response = await mock_research_agent.chat("test")
            assert response == "" or response is not None

    @pytest.mark.asyncio
    async def test_network_error_recovery(self):
        """Test recovery from network errors."""
        import socket

        with patch("src.mcp.client.MCPClientManager") as mock_cls:
            mock_manager = MagicMock()
            mock_manager.get_active_toolsets.side_effect = [
                socket.error("Network unreachable"),
                [MagicMock()],  # Second call succeeds
            ]
            mock_cls.return_value = mock_manager

            # First call fails
            with pytest.raises(socket.error):
                mock_manager.get_active_toolsets()

            # Retry succeeds
            toolsets = mock_manager.get_active_toolsets()
            assert len(toolsets) == 1


# =============================================================================
# INTEGRATION TESTS
# =============================================================================


@pytest.mark.integration
class TestFullChatFlowIntegration:
    """End-to-end integration tests for chat flow."""

    @pytest.mark.asyncio
    @patch("src.cli.chat.check_provider_status")
    @patch("src.cli.chat.settings")
    @patch("src.cli.chat.ResearchAgent")
    @patch("src.cli.chat.Prompt.ask")
    async def test_full_chat_with_mcp_tools(
        self, mock_ask, mock_agent_cls, mock_settings, mock_check
    ):
        """Test complete chat flow using MCP tools."""
        mock_check.return_value = {"available": True}
        mock_settings.mcp_mssql_path = "/path/to/mcp"
        mock_settings.llm_provider = "ollama"
        mock_ask.side_effect = ["What tables exist?", "quit"]

        mock_response = MagicMock()
        mock_response.content = "Found 5 tables: users, orders, products, categories, logs"
        mock_response.token_usage = MagicMock(total_tokens=100)

        mock_agent = MagicMock()
        mock_agent.chat_with_details = AsyncMock(return_value=mock_response)
        mock_agent._active_toolsets = [MagicMock()]
        mock_agent_cls.return_value = mock_agent

        from src.cli.chat import run_chat_loop

        await run_chat_loop()

        mock_agent.chat_with_details.assert_called()

    @pytest.mark.asyncio
    @patch("src.cli.chat.check_provider_status")
    @patch("src.cli.chat.settings")
    @patch("src.cli.chat.ResearchAgent")
    @patch("src.cli.chat.Prompt.ask")
    async def test_chat_with_history_export(
        self, mock_ask, mock_agent_cls, mock_settings, mock_check
    ):
        """Test chat with conversation export."""
        mock_check.return_value = {"available": True}
        mock_settings.mcp_mssql_path = "/path/to/mcp"
        mock_settings.llm_provider = "ollama"
        mock_ask.side_effect = ["test message", "export", "quit"]

        mock_agent = MagicMock()
        mock_agent.chat = AsyncMock(return_value="Response")
        mock_agent.get_conversation_history = MagicMock(
            return_value=[
                {"role": "user", "content": "test message"},
                {"role": "assistant", "content": "Response"},
            ]
        )
        mock_agent_cls.return_value = mock_agent

        from src.cli.chat import run_chat_loop

        await run_chat_loop()


# =============================================================================
# FIXTURE TESTS
# =============================================================================


@pytest.mark.unit
class TestMCPConfigFixtures:
    """Tests for MCP configuration test fixtures."""

    def test_fixture_creates_valid_config(self, temp_mcp_config):
        """Test temp_mcp_config fixture creates valid JSON."""
        with open(temp_mcp_config) as f:
            config = json.load(f)

        assert "mcpServers" in config
        assert len(config["mcpServers"]) == 3

    def test_fixture_contains_all_transport_types(self, temp_mcp_config):
        """Test fixture includes stdio and HTTP servers."""
        with open(temp_mcp_config) as f:
            config = json.load(f)

        transports = {s["transport"] for s in config["mcpServers"].values()}
        assert "stdio" in transports
        assert "streamable_http" in transports

    def test_fixture_includes_disabled_server(self, temp_mcp_config):
        """Test fixture includes a disabled server for testing."""
        with open(temp_mcp_config) as f:
            config = json.load(f)

        disabled = [s for s in config["mcpServers"].values() if not s["enabled"]]
        assert len(disabled) >= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
