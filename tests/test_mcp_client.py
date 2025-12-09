"""
Tests for MCP Client and Configuration

Tests for MCP client manager, MSSQL configuration, and server management.
"""

from unittest.mock import MagicMock, patch

import pytest

from src.mcp.client import MCPClientManager
from src.mcp.mssql_config import (
    MSSQL_TOOLS,
    MSSQLMCPConfig,
    get_readonly_tools,
    get_write_tools,
)


class TestMSSQLMCPConfig:
    """Tests for MSSQL MCP configuration."""

    def test_config_defaults(self):
        """Test default configuration values."""
        config = MSSQLMCPConfig()

        assert config.command == "node"
        assert config.server_name == "localhost"
        assert config.trust_server_certificate is True

    def test_config_from_settings(self):
        """Test creating config from settings."""
        with patch("src.mcp.mssql_config.settings") as mock_settings:
            mock_settings.mcp_mssql_path = "/path/to/mcp.js"
            mock_settings.sql_server_host = "testserver"
            mock_settings.sql_database_name = "testdb"
            mock_settings.sql_trust_server_certificate = True
            mock_settings.mcp_mssql_readonly = True
            mock_settings.sql_username = ""
            mock_settings.sql_password = ""

            config = MSSQLMCPConfig.from_settings()

            assert config.mcp_path == "/path/to/mcp.js"
            assert config.server_name == "testserver"
            assert config.database_name == "testdb"
            assert config.readonly is True

    def test_config_validation_missing_path(self):
        """Test validation fails when MCP path is missing."""
        config = MSSQLMCPConfig(mcp_path="")
        errors = config.validate()

        assert len(errors) > 0
        assert any("MCP_MSSQL_PATH" in e for e in errors)

    def test_config_validation_nonexistent_path(self):
        """Test validation fails when MCP path doesn't exist."""
        config = MSSQLMCPConfig(mcp_path="/nonexistent/path.js")
        errors = config.validate()

        assert len(errors) > 0
        assert any("does not exist" in e for e in errors)

    def test_get_env(self):
        """Test getting environment variables."""
        config = MSSQLMCPConfig(
            server_name="testserver",
            database_name="testdb",
            readonly=True,
            username="user",
            password="pass",
        )

        env = config.get_env()

        assert env["SERVER_NAME"] == "testserver"
        assert env["DATABASE_NAME"] == "testdb"
        assert env["READONLY"] == "true"
        assert env["SQL_USERNAME"] == "user"
        assert env["SQL_PASSWORD"] == "pass"

    def test_get_env_no_credentials(self):
        """Test environment without credentials."""
        config = MSSQLMCPConfig(server_name="testserver")
        env = config.get_env()

        assert "SQL_USERNAME" not in env
        assert "SQL_PASSWORD" not in env


class TestMSSQLTools:
    """Tests for MSSQL tool definitions."""

    def test_all_tools_defined(self):
        """Test all expected tools are defined."""
        expected_tools = [
            "list_tables",
            "describe_table",
            "read_data",
            "insert_data",
            "update_data",
            "create_table",
            "drop_table",
            "create_index",
        ]

        for tool in expected_tools:
            assert tool in MSSQL_TOOLS

    def test_readonly_tools(self):
        """Test read-only tools list."""
        readonly = get_readonly_tools()

        assert "list_tables" in readonly
        assert "describe_table" in readonly
        assert "read_data" in readonly
        assert "insert_data" not in readonly

    def test_write_tools(self):
        """Test write tools list."""
        write = get_write_tools()

        assert "insert_data" in write
        assert "update_data" in write
        assert "list_tables" not in write


class TestMCPClientManager:
    """Tests for MCP client manager."""

    def test_init_with_path(self, tmp_path):
        """Test initialization with config path."""
        manager = MCPClientManager(config_path=tmp_path / "config.json")
        assert manager.config_path is not None

    def test_load_config_not_found(self):
        """Test loading missing config file."""
        manager = MCPClientManager(config_path="/nonexistent/config.json")

        with pytest.raises(FileNotFoundError):
            manager.load_config()

    def test_load_config_success(self, temp_mcp_config):
        """Test successful config loading."""
        manager = MCPClientManager(config_path=temp_mcp_config)
        config = manager.load_config()

        assert "mcpServers" in config
        assert "mssql" in config["mcpServers"]

    def test_resolve_env_vars(self):
        """Test environment variable resolution."""
        manager = MCPClientManager()

        with patch.dict("os.environ", {"TEST_VAR": "test_value"}):
            result = manager._resolve_env_vars("${TEST_VAR}")
            assert result == "test_value"

    def test_resolve_env_vars_with_default(self):
        """Test environment variable resolution with default."""
        manager = MCPClientManager()

        result = manager._resolve_env_vars("${NONEXISTENT:-default_val}")
        assert result == "default_val"

    def test_list_configured_servers(self, temp_mcp_config):
        """Test listing configured servers."""
        manager = MCPClientManager(config_path=temp_mcp_config)
        servers = manager.list_configured_servers()

        assert "mssql" in servers

    def test_get_mssql_server_invalid_config(self):
        """Test getting MSSQL server with invalid config."""
        with patch("src.mcp.client.MSSQLMCPConfig.from_settings") as mock_config:
            mock = MagicMock()
            mock.validate.return_value = ["Missing MCP path"]
            mock_config.return_value = mock

            manager = MCPClientManager()

            with pytest.raises(ValueError) as exc_info:
                manager.get_mssql_server()

            assert "Missing MCP path" in str(exc_info.value)
