"""MCP integration modules for connecting to MCP servers."""

from src.mcp.client import MCPClientManager
from src.mcp.dynamic_manager import (
    DynamicMCPManager,
    MCPServerConfig,
)
from src.mcp.mssql_config import (
    MSSQL_TOOLS,
    MSSQLMCPConfig,
    MSSQLToolInfo,
    get_readonly_tools,
    get_write_tools,
)
from src.mcp.mysql_config import (
    MYSQL_TOOLS,
    MySQLMCPConfig,
    MySQLToolInfo,
)
from src.mcp.postgres_config import (
    POSTGRES_TOOLS,
    PostgresMCPConfig,
    PostgresToolInfo,
)
from src.mcp.server_manager import (
    MCPConnectionError,
    MCPServerError,
    MCPServerManager,
    MCPTimeoutError,
    get_mssql_server,
)

__all__ = [
    # Client
    "MCPClientManager",
    # Dynamic Manager
    "DynamicMCPManager",
    "MCPServerConfig",
    # MSSQL Config
    "MSSQLMCPConfig",
    "MSSQLToolInfo",
    "MSSQL_TOOLS",
    "get_readonly_tools",
    "get_write_tools",
    # PostgreSQL Config
    "PostgresMCPConfig",
    "PostgresToolInfo",
    "POSTGRES_TOOLS",
    # MySQL Config
    "MySQLMCPConfig",
    "MySQLToolInfo",
    "MYSQL_TOOLS",
    # Server Manager
    "MCPServerManager",
    "MCPServerError",
    "MCPConnectionError",
    "MCPTimeoutError",
    "get_mssql_server",
]
