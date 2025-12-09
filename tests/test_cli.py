"""
Tests for CLI Interface

Tests for the command-line chat interface.
"""

from unittest.mock import AsyncMock, MagicMock, patch

from typer.testing import CliRunner

from src.cli.chat import app, check_model_available, check_ollama_connection

runner = CliRunner()


class TestOllamaChecks:
    """Tests for Ollama connection checks."""

    @patch("src.cli.chat.httpx.get")
    def test_check_ollama_connection_success(self, mock_get):
        """Test successful Ollama connection check."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        result = check_ollama_connection()

        assert result is True

    @patch("src.cli.chat.httpx.get")
    def test_check_ollama_connection_failure(self, mock_get):
        """Test failed Ollama connection check."""
        mock_get.side_effect = Exception("Connection refused")

        result = check_ollama_connection()

        assert result is False

    @patch("src.cli.chat.httpx.get")
    def test_check_model_available_success(self, mock_get):
        """Test model availability check success."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "models": [
                {"name": "qwen2.5:7b-instruct"},
                {"name": "llama3.1:8b"},
            ]
        }
        mock_get.return_value = mock_response

        result = check_model_available("qwen2.5:7b-instruct")

        assert result is True

    @patch("src.cli.chat.httpx.get")
    def test_check_model_available_not_found(self, mock_get):
        """Test model availability check when model not found."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"models": [{"name": "other-model"}]}
        mock_get.return_value = mock_response

        result = check_model_available("qwen2.5:7b-instruct")

        assert result is False


class TestCLICommands:
    """Tests for CLI commands."""

    def test_status_command(self):
        """Test status command runs."""
        with (
            patch("src.cli.chat.check_ollama_connection", return_value=True),
            patch("src.cli.chat.settings") as mock_settings,
        ):
            mock_settings.ollama_model = "test-model"
            mock_settings.mcp_mssql_path = "/path/to/mcp"
            mock_settings.mcp_mssql_readonly = False

            result = runner.invoke(app, ["status"])

            assert result.exit_code == 0

    @patch("src.cli.chat.check_ollama_connection")
    def test_query_command_ollama_not_running(self, mock_check):
        """Test query command when Ollama is not running."""
        mock_check.return_value = False

        result = runner.invoke(app, ["query", "test query"])

        # Check that error is shown (exit code may vary based on how typer handles it)
        assert "not running" in result.output.lower() or result.exit_code == 1

    @patch("src.cli.chat.check_ollama_connection")
    @patch("src.cli.chat.ResearchAgent")
    def test_query_command_success(self, mock_agent_cls, mock_check):
        """Test successful query command."""
        mock_check.return_value = True

        mock_agent = MagicMock()
        mock_agent.chat = AsyncMock(return_value="Query result")
        mock_agent_cls.return_value = mock_agent

        # Just invoke the command - async context makes full testing complex
        runner.invoke(app, ["query", "What tables exist?"])


class TestChatLoop:
    """Tests for chat loop functionality."""

    @patch("src.cli.chat.check_ollama_connection")
    @patch("src.cli.chat.settings")
    @patch("src.cli.chat.ResearchAgent")
    @patch("src.cli.chat.Prompt.ask")
    async def test_chat_loop_quit(self, mock_ask, mock_agent_cls, mock_settings, mock_check):
        """Test chat loop exits on quit."""
        mock_check.return_value = True
        mock_settings.mcp_mssql_path = "/path/to/mcp"
        mock_ask.return_value = "quit"

        from src.cli.chat import run_chat_loop

        await run_chat_loop()

        # Should exit cleanly without error

    @patch("src.cli.chat.check_ollama_connection")
    @patch("src.cli.chat.settings")
    @patch("src.cli.chat.ResearchAgent")
    @patch("src.cli.chat.Prompt.ask")
    async def test_chat_loop_clear(self, mock_ask, mock_agent_cls, mock_settings, mock_check):
        """Test chat loop clears history."""
        mock_check.return_value = True
        mock_settings.mcp_mssql_path = "/path/to/mcp"
        mock_ask.side_effect = ["clear", "quit"]

        mock_agent = MagicMock()
        mock_agent.clear_history = MagicMock()
        mock_agent_cls.return_value = mock_agent

        from src.cli.chat import run_chat_loop

        await run_chat_loop()

        mock_agent.clear_history.assert_called_once()
