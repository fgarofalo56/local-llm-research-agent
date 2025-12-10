"""
Tests for MSSQL MCP Server Configuration

Tests the MSSQLMCPConfig class and related utilities in src/mcp/mssql_config.py.
"""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.mcp.mssql_config import (
    MSSQLMCPConfig,
    MSSQLToolInfo,
    MSSQL_TOOLS,
    get_readonly_tools,
    get_write_tools,
)


class TestMSSQLMCPConfig:
    """Tests for MSSQLMCPConfig class."""

    def test_default_config(self):
        """Test default configuration values."""
        config = MSSQLMCPConfig()

        assert config.command == "node"
        assert config.mcp_path == ""
        assert config.server_name == "localhost"
        assert config.database_name == "master"
        assert config.trust_server_certificate is True
        assert config.readonly is False
        assert config.username == ""
        assert config.password == ""
        assert config.timeout == 30

    def test_custom_config(self):
        """Test creating config with custom values."""
        config = MSSQLMCPConfig(
            mcp_path="/path/to/mcp/index.js",
            server_name="sqlserver.local",
            database_name="TestDB",
            readonly=True,
            username="testuser",
            password="testpass",
            timeout=60,
        )

        assert config.mcp_path == "/path/to/mcp/index.js"
        assert config.server_name == "sqlserver.local"
        assert config.database_name == "TestDB"
        assert config.readonly is True
        assert config.username == "testuser"
        assert config.password == "testpass"
        assert config.timeout == 60

    def test_from_settings(self):
        """Test creating config from application settings."""
        with patch("src.mcp.mssql_config.settings") as mock_settings:
            mock_settings.mcp_mssql_path = "/path/to/mcp"
            mock_settings.sql_server_host = "testserver"
            mock_settings.sql_database_name = "testdb"
            mock_settings.sql_trust_server_certificate = False
            mock_settings.mcp_mssql_readonly = True
            mock_settings.sql_username = "user"
            mock_settings.sql_password = "pass"

            config = MSSQLMCPConfig.from_settings()

        assert config.mcp_path == "/path/to/mcp"
        assert config.server_name == "testserver"
        assert config.database_name == "testdb"
        assert config.trust_server_certificate is False
        assert config.readonly is True
        assert config.username == "user"
        assert config.password == "pass"

    def test_validate_missing_mcp_path(self):
        """Test validation catches missing MCP path."""
        config = MSSQLMCPConfig(mcp_path="")
        errors = config.validate()

        assert "MCP_MSSQL_PATH is not set" in errors

    def test_validate_nonexistent_mcp_path(self):
        """Test validation catches non-existent MCP path."""
        config = MSSQLMCPConfig(mcp_path="/nonexistent/path/index.js")
        errors = config.validate()

        assert any("does not exist" in err for err in errors)

    def test_validate_missing_server_name(self):
        """Test validation catches missing server name."""
        config = MSSQLMCPConfig(
            mcp_path="/some/path",  # Would fail existence check too
            server_name="",
        )
        errors = config.validate()

        assert "SQL_SERVER_HOST is not set" in errors

    def test_validate_missing_database_name(self):
        """Test validation catches missing database name."""
        config = MSSQLMCPConfig(
            mcp_path="/some/path",
            database_name="",
        )
        errors = config.validate()

        assert "SQL_DATABASE_NAME is not set" in errors

    def test_validate_valid_config(self, tmp_path):
        """Test validation passes for valid config."""
        # Create a temporary file to simulate MCP script
        mcp_file = tmp_path / "index.js"
        mcp_file.write_text("// MCP script")

        config = MSSQLMCPConfig(
            mcp_path=str(mcp_file),
            server_name="localhost",
            database_name="testdb",
        )

        errors = config.validate()
        assert errors == []
        assert config.is_valid() is True

    def test_is_valid_false(self):
        """Test is_valid returns False for invalid config."""
        config = MSSQLMCPConfig(mcp_path="", server_name="")
        assert config.is_valid() is False

    def test_get_env_basic(self):
        """Test getting environment variables."""
        config = MSSQLMCPConfig(
            server_name="testserver",
            database_name="testdb",
            trust_server_certificate=True,
            readonly=False,
        )

        env = config.get_env()

        assert env["SERVER_NAME"] == "testserver"
        assert env["DATABASE_NAME"] == "testdb"
        assert env["TRUST_SERVER_CERTIFICATE"] == "true"
        assert env["READONLY"] == "false"
        assert "SQL_USERNAME" not in env
        assert "SQL_PASSWORD" not in env

    def test_get_env_with_credentials(self):
        """Test environment includes credentials when set."""
        config = MSSQLMCPConfig(
            server_name="server",
            database_name="db",
            username="user",
            password="pass",
        )

        env = config.get_env()

        assert env["SQL_USERNAME"] == "user"
        assert env["SQL_PASSWORD"] == "pass"

    def test_get_env_readonly_mode(self):
        """Test environment in readonly mode."""
        config = MSSQLMCPConfig(
            server_name="server",
            database_name="db",
            readonly=True,
        )

        env = config.get_env()
        assert env["READONLY"] == "true"

    def test_get_args(self):
        """Test getting command arguments."""
        config = MSSQLMCPConfig(mcp_path="/path/to/index.js")
        args = config.get_args()

        assert args == ["/path/to/index.js"]

    def test_log_config(self):
        """Test config logging doesn't raise errors."""
        config = MSSQLMCPConfig(
            server_name="testserver",
            database_name="testdb",
            mcp_path="/path/to/mcp",
            username="user",
        )

        # Should not raise any errors
        config.log_config()
        config.log_config(_mask_credentials=True)


class TestMSSQLToolInfo:
    """Tests for MSSQLToolInfo dataclass."""

    def test_create_tool_info(self):
        """Test creating tool info."""
        tool = MSSQLToolInfo(
            name="test_tool",
            description="A test tool",
            safe_for_readonly=True,
            examples=["Example 1", "Example 2"],
        )

        assert tool.name == "test_tool"
        assert tool.description == "A test tool"
        assert tool.safe_for_readonly is True
        assert len(tool.examples) == 2

    def test_tool_info_defaults(self):
        """Test tool info default values."""
        tool = MSSQLToolInfo(
            name="tool",
            description="desc",
        )

        assert tool.safe_for_readonly is True
        assert tool.examples == []


class TestMSSQLTools:
    """Tests for MSSQL_TOOLS dictionary."""

    def test_all_expected_tools_exist(self):
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

        for tool_name in expected_tools:
            assert tool_name in MSSQL_TOOLS, f"Tool {tool_name} should be defined"

    def test_tool_info_structure(self):
        """Test all tools have required info."""
        for name, tool in MSSQL_TOOLS.items():
            assert isinstance(tool, MSSQLToolInfo)
            assert tool.name == name
            assert tool.description
            assert isinstance(tool.safe_for_readonly, bool)
            assert isinstance(tool.examples, list)

    def test_readonly_tools(self):
        """Test readonly tools are correctly marked."""
        readonly_tools = ["list_tables", "describe_table", "read_data"]

        for tool_name in readonly_tools:
            tool = MSSQL_TOOLS[tool_name]
            assert tool.safe_for_readonly is True, f"{tool_name} should be readonly safe"

    def test_write_tools(self):
        """Test write tools are correctly marked."""
        write_tools = ["insert_data", "update_data", "create_table", "drop_table", "create_index"]

        for tool_name in write_tools:
            tool = MSSQL_TOOLS[tool_name]
            assert tool.safe_for_readonly is False, f"{tool_name} should not be readonly safe"


class TestGetReadonlyTools:
    """Tests for get_readonly_tools function."""

    def test_returns_readonly_tools(self):
        """Test function returns only readonly-safe tools."""
        readonly_tools = get_readonly_tools()

        assert "list_tables" in readonly_tools
        assert "describe_table" in readonly_tools
        assert "read_data" in readonly_tools

        # Write tools should not be included
        assert "insert_data" not in readonly_tools
        assert "update_data" not in readonly_tools
        assert "create_table" not in readonly_tools
        assert "drop_table" not in readonly_tools

    def test_returns_list(self):
        """Test function returns a list."""
        result = get_readonly_tools()
        assert isinstance(result, list)


class TestGetWriteTools:
    """Tests for get_write_tools function."""

    def test_returns_write_tools(self):
        """Test function returns only write tools."""
        write_tools = get_write_tools()

        assert "insert_data" in write_tools
        assert "update_data" in write_tools
        assert "create_table" in write_tools
        assert "drop_table" in write_tools
        assert "create_index" in write_tools

        # Readonly tools should not be included
        assert "list_tables" not in write_tools
        assert "describe_table" not in write_tools
        assert "read_data" not in write_tools

    def test_returns_list(self):
        """Test function returns a list."""
        result = get_write_tools()
        assert isinstance(result, list)


class TestToolCategorization:
    """Tests for tool categorization consistency."""

    def test_all_tools_categorized(self):
        """Test all tools are in either readonly or write category."""
        readonly = set(get_readonly_tools())
        write = set(get_write_tools())
        all_tools = set(MSSQL_TOOLS.keys())

        categorized = readonly | write
        assert categorized == all_tools, "All tools should be categorized"

    def test_no_overlap(self):
        """Test no tool is in both categories."""
        readonly = set(get_readonly_tools())
        write = set(get_write_tools())

        overlap = readonly & write
        assert len(overlap) == 0, f"Tools should not be in both categories: {overlap}"
