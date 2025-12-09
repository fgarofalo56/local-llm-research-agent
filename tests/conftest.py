"""
Pytest Configuration and Fixtures

Shared fixtures for testing the research agent components.
"""

import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Set test environment before imports
os.environ.setdefault("OLLAMA_HOST", "http://localhost:11434")
os.environ.setdefault("OLLAMA_MODEL", "qwen2.5:7b-instruct")
os.environ.setdefault("SQL_SERVER_HOST", "localhost")
os.environ.setdefault("SQL_DATABASE_NAME", "test_db")
os.environ.setdefault("MCP_MSSQL_PATH", "/path/to/mcp/index.js")
os.environ.setdefault("LOG_LEVEL", "WARNING")


@pytest.fixture
def mock_settings():
    """Mock application settings."""
    with patch("src.utils.config.settings") as mock:
        mock.ollama_host = "http://localhost:11434"
        mock.ollama_model = "qwen2.5:7b-instruct"
        mock.sql_server_host = "localhost"
        mock.sql_database_name = "test_db"
        mock.sql_trust_server_certificate = True
        mock.mcp_mssql_path = "/path/to/mcp/index.js"
        mock.mcp_mssql_readonly = True
        mock.log_level = "WARNING"
        mock.debug = False
        yield mock


@pytest.fixture
def mock_mcp_server():
    """Mock MCPServerStdio."""
    mock = MagicMock()
    mock.__aenter__ = AsyncMock(return_value=mock)
    mock.__aexit__ = AsyncMock(return_value=None)
    mock.list_tools = AsyncMock(return_value=[
        MagicMock(name="list_tables"),
        MagicMock(name="describe_table"),
        MagicMock(name="read_data"),
    ])
    return mock


@pytest.fixture
def mock_agent_result():
    """Mock agent run result."""
    result = MagicMock()
    result.output = "I found 3 tables in the database: Users, Orders, Products."
    return result


@pytest.fixture
def sample_conversation_history():
    """Sample conversation history for testing."""
    return [
        {"role": "user", "content": "What tables are available?"},
        {"role": "assistant", "content": "The database contains: Users, Orders, Products."},
        {"role": "user", "content": "Describe the Users table."},
        {"role": "assistant", "content": "Users has columns: id, name, email, created_at."},
    ]


@pytest.fixture
def temp_env_file(tmp_path):
    """Create a temporary .env file."""
    env_content = """
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=qwen2.5:7b-instruct
SQL_SERVER_HOST=localhost
SQL_DATABASE_NAME=test_db
MCP_MSSQL_PATH=/path/to/mcp/index.js
"""
    env_file = tmp_path / ".env"
    env_file.write_text(env_content)
    return env_file


@pytest.fixture
def temp_mcp_config(tmp_path):
    """Create a temporary MCP config file."""
    config_content = """
{
  "mcpServers": {
    "mssql": {
      "command": "node",
      "args": ["/path/to/index.js"],
      "env": {
        "SERVER_NAME": "localhost",
        "DATABASE_NAME": "test_db"
      }
    }
  }
}
"""
    config_file = tmp_path / "mcp_config.json"
    config_file.write_text(config_content)
    return config_file
