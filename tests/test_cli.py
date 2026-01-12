"""
Tests for CLI Interface

Tests for the command-line chat interface.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from typer.testing import CliRunner

from src.cli.chat import app

# Disable colors in CLI output to avoid ANSI escape codes breaking string assertions
runner = CliRunner(env={"NO_COLOR": "1", "TERM": "dumb"})


@pytest.mark.unit
class TestProviderStatusChecks:
    """Tests for provider status checks."""

    @pytest.mark.asyncio
    async def test_check_provider_status_ollama_success(self, mock_ollama_provider):
        """Test successful Ollama provider status check."""
        with patch("src.cli.chat.create_provider", return_value=mock_ollama_provider):
            from src.cli.chat import check_provider_status

            result = await check_provider_status("ollama")

            assert result["available"] is True
            assert result["provider"] == "ollama"
            assert "qwen2.5" in result["model"]

    @pytest.mark.asyncio
    async def test_check_provider_status_foundry_success(self, mock_foundry_provider):
        """Test successful Foundry Local provider status check."""
        with patch("src.cli.chat.create_provider", return_value=mock_foundry_provider):
            from src.cli.chat import check_provider_status

            result = await check_provider_status("foundry_local")

            assert result["available"] is True
            assert result["provider"] == "foundry_local"
            assert result["model"] == "phi-4"

    @pytest.mark.asyncio
    async def test_check_provider_status_unavailable(self, mock_provider_unavailable):
        """Test provider status check when unavailable."""
        with patch("src.cli.chat.create_provider", return_value=mock_provider_unavailable):
            from src.cli.chat import check_provider_status

            result = await check_provider_status("ollama")

            assert result["available"] is False
            assert "Connection refused" in result["error"]


@pytest.mark.unit
class TestCLICommands:
    """Tests for CLI commands."""

    def test_status_command(self):
        """Test status command runs."""
        with (
            patch("src.cli.chat.get_available_providers") as mock_get_providers,
            patch("src.cli.chat.settings") as mock_settings,
        ):
            from src.providers import ProviderType
            from src.utils.config import SqlAuthType

            mock_status = MagicMock()
            mock_status.provider_type = ProviderType.OLLAMA
            mock_status.available = True
            mock_status.model_name = "test-model"
            mock_status.version = "0.3.0"
            mock_status.error = None

            mock_get_providers.return_value = [mock_status]
            mock_settings.llm_provider = "ollama"
            mock_settings.mcp_mssql_path = "/path/to/mcp"
            mock_settings.mcp_mssql_readonly = False
            mock_settings.sql_server_host = "localhost"
            mock_settings.sql_database_name = "TestDB"
            mock_settings.is_azure_sql = False
            mock_settings.sql_auth_type = SqlAuthType.SQL_AUTH
            mock_settings.sql_username = "sa"
            mock_settings.azure_client_id = ""

            result = runner.invoke(app, ["status"])

            assert result.exit_code == 0

    @patch("src.cli.chat.check_provider_status")
    def test_query_command_provider_not_available(self, mock_check):
        """Test query command when provider is not available."""
        mock_check.return_value = {"available": False, "error": "Connection refused"}

        result = runner.invoke(app, ["query", "test query"])

        assert result.exit_code == 1 or "not available" in result.output.lower()

    @patch("src.cli.chat.check_provider_status")
    @patch("src.cli.chat.ResearchAgent")
    def test_query_command_success(self, mock_agent_cls, mock_check):
        """Test successful query command."""
        mock_check.return_value = {"available": True}

        # Create mock response object with token_usage
        mock_response = MagicMock()
        mock_response.content = "Query result: 5 tables found"
        mock_response.token_usage = MagicMock()
        mock_response.token_usage.prompt_tokens = 50
        mock_response.token_usage.completion_tokens = 20
        mock_response.token_usage.total_tokens = 70
        mock_response.duration_ms = 1000.0

        mock_agent = MagicMock()
        mock_agent.chat_with_details = AsyncMock(return_value=mock_response)
        mock_agent_cls.return_value = mock_agent

        with patch("src.cli.chat.settings") as mock_settings:
            mock_settings.llm_provider = "ollama"

            result = runner.invoke(app, ["query", "What tables exist?"])

            # Command should run without crashing
            assert "error" not in result.output.lower() or result.exit_code == 0

    @patch("src.cli.chat.check_provider_status")
    @patch("src.cli.chat.ResearchAgent")
    def test_query_command_with_stream(self, mock_agent_cls, mock_check):
        """Test query command with streaming enabled."""
        mock_check.return_value = {"available": True}

        async def mock_stream():
            yield "Streaming "
            yield "response."

        # Create mock token_usage for get_last_response_stats
        mock_token_usage = MagicMock()
        mock_token_usage.prompt_tokens = 50
        mock_token_usage.completion_tokens = 20
        mock_token_usage.total_tokens = 70

        mock_agent = MagicMock()
        mock_agent.chat_stream = MagicMock(return_value=mock_stream())
        mock_agent.get_last_response_stats = MagicMock(
            return_value={
                "token_usage": mock_token_usage,
                "duration_ms": 1000.0,
            }
        )
        mock_agent_cls.return_value = mock_agent

        with patch("src.cli.chat.settings") as mock_settings:
            mock_settings.llm_provider = "ollama"

            result = runner.invoke(app, ["query", "--stream", "Test query"])

            # Should run without error
            assert result.exit_code == 0 or "error" not in result.output.lower()


@pytest.mark.unit
class TestChatCommand:
    """Tests for main chat command."""

    def test_chat_help(self):
        """Test chat command help."""
        result = runner.invoke(app, ["chat", "--help"])

        assert result.exit_code == 0
        assert "--provider" in result.output
        assert "--model" in result.output
        assert "--stream" in result.output
        assert "--readonly" in result.output

    @patch("src.cli.chat.print_welcome")
    @patch("src.cli.chat.print_status_sync")
    @patch("src.cli.chat.run_chat_loop")
    def test_chat_command_invokes_loop(self, mock_loop, mock_status, mock_welcome):
        """Test that chat command invokes the chat loop."""
        mock_loop.return_value = None

        with patch("src.cli.chat.asyncio.run") as mock_run:
            mock_run.return_value = None

            runner.invoke(app, ["chat"])

            mock_welcome.assert_called_once()
            mock_status.assert_called_once()


@pytest.mark.integration
class TestChatLoopIntegration:
    """Integration tests for chat loop functionality."""

    @pytest.mark.asyncio
    @patch("src.cli.chat.check_provider_status")
    @patch("src.cli.chat.settings")
    @patch("src.cli.chat.ResearchAgent")
    @patch("src.cli.chat.ThinkingModeInput")
    @patch("src.cli.chat.Prompt.ask")
    async def test_chat_loop_quit(
        self, mock_ask, mock_thinking_input, mock_agent_cls, mock_settings, mock_check
    ):
        """Test chat loop exits on quit."""
        mock_check.return_value = {"available": True}
        mock_settings.mcp_mssql_path = "/path/to/mcp"
        mock_settings.llm_provider = "ollama"
        mock_ask.return_value = "quit"

        # Mock ThinkingModeInput to avoid TTY requirement
        mock_input_handler = MagicMock()
        mock_input_handler.is_interactive.return_value = False
        mock_input_handler.prompt.return_value = "quit"
        mock_thinking_input.return_value = mock_input_handler

        mock_agent = MagicMock()
        mock_agent_cls.return_value = mock_agent

        from src.cli.chat import run_chat_loop

        await run_chat_loop()

        # Should exit cleanly

    @pytest.mark.asyncio
    @patch("src.cli.chat.check_provider_status")
    @patch("src.cli.chat.settings")
    @patch("src.cli.chat.ResearchAgent")
    @patch("src.cli.chat.ThinkingModeInput")
    @patch("src.cli.chat.Prompt.ask")
    async def test_chat_loop_clear_command(
        self, mock_ask, mock_thinking_input, mock_agent_cls, mock_settings, mock_check
    ):
        """Test chat loop clears history on clear command."""
        mock_check.return_value = {"available": True}
        mock_settings.mcp_mssql_path = "/path/to/mcp"
        mock_settings.llm_provider = "ollama"
        mock_ask.side_effect = ["clear", "quit"]

        # Mock ThinkingModeInput to avoid TTY requirement
        mock_input_handler = MagicMock()
        mock_input_handler.is_interactive.return_value = False
        mock_input_handler.prompt.side_effect = ["clear", "quit"]
        mock_thinking_input.return_value = mock_input_handler

        mock_agent = MagicMock()
        mock_agent.clear_history = MagicMock()
        mock_agent_cls.return_value = mock_agent

        from src.cli.chat import run_chat_loop

        await run_chat_loop()

        mock_agent.clear_history.assert_called_once()

    @pytest.mark.asyncio
    @patch("src.cli.chat.check_provider_status")
    @patch("src.cli.chat.settings")
    @patch("src.cli.chat.ResearchAgent")
    @patch("src.cli.chat.ThinkingModeInput")
    @patch("src.cli.chat.Prompt.ask")
    async def test_chat_loop_streaming_mode(
        self, mock_ask, mock_thinking_input, mock_agent_cls, mock_settings, mock_check
    ):
        """Test chat loop with streaming enabled."""
        mock_check.return_value = {"available": True}
        mock_settings.mcp_mssql_path = "/path/to/mcp"
        mock_settings.llm_provider = "ollama"
        mock_ask.side_effect = ["test message", "quit"]

        # Mock ThinkingModeInput to avoid TTY requirement
        mock_input_handler = MagicMock()
        mock_input_handler.is_interactive.return_value = False
        mock_input_handler.prompt.side_effect = ["test message", "quit"]
        mock_thinking_input.return_value = mock_input_handler

        async def mock_stream():
            yield "Response "
            yield "chunk."

        mock_agent = MagicMock()
        mock_agent.chat_stream = MagicMock(return_value=mock_stream())
        mock_agent_cls.return_value = mock_agent

        from src.cli.chat import run_chat_loop

        await run_chat_loop(stream=True)

        mock_agent.chat_stream.assert_called_once()


@pytest.mark.unit
class TestProviderSelection:
    """Tests for provider selection in CLI."""

    def test_provider_option_ollama(self):
        """Test --provider ollama option is accepted."""
        result = runner.invoke(app, ["chat", "--provider", "ollama", "--help"])
        # Help should still work with provider specified
        assert "--provider" in result.output

    def test_provider_option_foundry(self):
        """Test --provider foundry_local option is accepted."""
        result = runner.invoke(app, ["chat", "--provider", "foundry_local", "--help"])
        assert "--provider" in result.output

    def test_model_option(self):
        """Test --model option is accepted."""
        result = runner.invoke(app, ["chat", "--model", "custom-model", "--help"])
        assert "--model" in result.output
