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
os.environ.setdefault("LLM_PROVIDER", "ollama")
os.environ.setdefault("FOUNDRY_ENDPOINT", "http://127.0.0.1:55588")
os.environ.setdefault("FOUNDRY_MODEL", "phi-4")
os.environ.setdefault("SQL_SERVER_HOST", "localhost")
os.environ.setdefault("SQL_DATABASE_NAME", "test_db")
os.environ.setdefault("MCP_MSSQL_PATH", "/path/to/mcp/index.js")
os.environ.setdefault("LOG_LEVEL", "WARNING")


def pytest_configure(config):
    """Register custom pytest markers."""
    config.addinivalue_line("markers", "unit: mark test as unit test")
    config.addinivalue_line("markers", "integration: mark test as integration test")
    config.addinivalue_line("markers", "slow: mark test as slow running")
    config.addinivalue_line("markers", "requires_ollama: mark test as requiring Ollama")
    config.addinivalue_line("markers", "requires_foundry: mark test as requiring Foundry Local")


@pytest.fixture
def mock_settings():
    """Mock application settings."""
    with patch("src.utils.config.settings") as mock:
        mock.ollama_host = "http://localhost:11434"
        mock.ollama_model = "qwen2.5:7b-instruct"
        mock.llm_provider = "ollama"
        mock.foundry_endpoint = "http://127.0.0.1:55588"
        mock.foundry_model = "phi-4"
        mock.foundry_auto_start = False
        mock.sql_server_host = "localhost"
        mock.sql_database_name = "test_db"
        mock.sql_trust_server_certificate = True
        mock.mcp_mssql_path = "/path/to/mcp/index.js"
        mock.mcp_mssql_readonly = True
        mock.log_level = "WARNING"
        mock.debug = False
        yield mock


@pytest.fixture
def mock_ollama_provider():
    """Mock Ollama provider."""
    from src.providers import ProviderType

    mock = MagicMock()
    mock.provider_type = ProviderType.OLLAMA
    mock.model_name = "qwen2.5:7b-instruct"
    mock.endpoint = "http://localhost:11434"
    mock.get_model.return_value = MagicMock()

    status = MagicMock()
    status.available = True
    status.provider_type = ProviderType.OLLAMA
    status.model_name = "qwen2.5:7b-instruct"
    status.endpoint = "http://localhost:11434"
    status.error = None
    status.version = "0.3.0"
    mock.check_connection = AsyncMock(return_value=status)
    mock.list_models = AsyncMock(return_value=["qwen2.5:7b-instruct", "llama3.1:8b"])

    return mock


@pytest.fixture
def mock_foundry_provider():
    """Mock Foundry Local provider."""
    from src.providers import ProviderType

    mock = MagicMock()
    mock.provider_type = ProviderType.FOUNDRY_LOCAL
    mock.model_name = "phi-4"
    mock.endpoint = "http://127.0.0.1:55588"
    mock.get_model.return_value = MagicMock()

    status = MagicMock()
    status.available = True
    status.provider_type = ProviderType.FOUNDRY_LOCAL
    status.model_name = "phi-4"
    status.endpoint = "http://127.0.0.1:55588"
    status.error = None
    status.version = None
    mock.check_connection = AsyncMock(return_value=status)
    mock.list_models = AsyncMock(return_value=["phi-4", "phi-3-mini"])

    return mock


@pytest.fixture
def mock_provider_unavailable():
    """Mock unavailable provider."""
    from src.providers import ProviderType

    mock = MagicMock()
    mock.provider_type = ProviderType.OLLAMA
    mock.model_name = "qwen2.5:7b-instruct"
    mock.endpoint = "http://localhost:11434"

    status = MagicMock()
    status.available = False
    status.provider_type = ProviderType.OLLAMA
    status.model_name = None
    status.endpoint = "http://localhost:11434"
    status.error = "Connection refused"
    status.version = None
    mock.check_connection = AsyncMock(return_value=status)
    mock.list_models = AsyncMock(return_value=[])

    return mock


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
