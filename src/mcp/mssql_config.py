"""
MSSQL MCP Server Configuration

Handles building configuration for the MSSQL MCP Server including
environment variable resolution and validation.
"""

from dataclasses import dataclass, field
from pathlib import Path

from src.utils.config import settings
from src.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class MSSQLMCPConfig:
    """Configuration for the MSSQL MCP Server."""

    # Server execution
    command: str = "node"
    mcp_path: str = ""

    # SQL Server connection
    server_name: str = "localhost"
    database_name: str = "master"
    trust_server_certificate: bool = True
    readonly: bool = False

    # Optional authentication
    username: str = ""
    password: str = ""

    # Server options
    timeout: int = 30

    @classmethod
    def from_settings(cls) -> "MSSQLMCPConfig":
        """Create config from application settings."""
        return cls(
            mcp_path=settings.mcp_mssql_path,
            server_name=settings.sql_server_host,
            database_name=settings.sql_database_name,
            trust_server_certificate=settings.sql_trust_server_certificate,
            readonly=settings.mcp_mssql_readonly,
            username=settings.sql_username,
            password=settings.sql_password,
        )

    def validate(self) -> list[str]:
        """
        Validate the configuration.

        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []

        if not self.mcp_path:
            errors.append("MCP_MSSQL_PATH is not set")
        elif not Path(self.mcp_path).exists():
            errors.append(f"MCP_MSSQL_PATH does not exist: {self.mcp_path}")

        if not self.server_name:
            errors.append("SQL_SERVER_HOST is not set")

        if not self.database_name:
            errors.append("SQL_DATABASE_NAME is not set")

        return errors

    def is_valid(self) -> bool:
        """Check if configuration is valid."""
        return len(self.validate()) == 0

    def get_env(self) -> dict[str, str]:
        """
        Get environment variables for MCP server subprocess.

        Returns:
            Dictionary of environment variables
        """
        env = {
            "SERVER_NAME": self.server_name,
            "DATABASE_NAME": self.database_name,
            "TRUST_SERVER_CERTIFICATE": str(self.trust_server_certificate).lower(),
            "READONLY": str(self.readonly).lower(),
        }

        if self.username:
            env["SQL_USERNAME"] = self.username
        if self.password:
            env["SQL_PASSWORD"] = self.password

        return env

    def get_args(self) -> list[str]:
        """Get command arguments for MCP server."""
        return [self.mcp_path]

    def log_config(self, _mask_credentials: bool = True) -> None:
        """Log configuration for debugging."""
        logger.info(
            "mssql_mcp_config",
            server_name=self.server_name,
            database_name=self.database_name,
            readonly=self.readonly,
            mcp_path=self.mcp_path,
            has_credentials=bool(self.username),
        )


@dataclass
class MSSQLToolInfo:
    """Information about MSSQL MCP tools."""

    name: str
    description: str
    safe_for_readonly: bool = True
    examples: list[str] = field(default_factory=list)


# Available tools provided by MSSQL MCP Server
MSSQL_TOOLS: dict[str, MSSQLToolInfo] = {
    "list_tables": MSSQLToolInfo(
        name="list_tables",
        description="Lists all tables in the connected database",
        safe_for_readonly=True,
        examples=["What tables are in the database?", "Show me the schema"],
    ),
    "describe_table": MSSQLToolInfo(
        name="describe_table",
        description="Get schema information for a specific table",
        safe_for_readonly=True,
        examples=["What columns does Users have?", "Describe the Orders table"],
    ),
    "read_data": MSSQLToolInfo(
        name="read_data",
        description="Query and retrieve data from tables",
        safe_for_readonly=True,
        examples=["Show top 10 orders", "Get all customers from NY"],
    ),
    "insert_data": MSSQLToolInfo(
        name="insert_data",
        description="Insert new rows into tables",
        safe_for_readonly=False,
        examples=["Add a new customer", "Insert a product record"],
    ),
    "update_data": MSSQLToolInfo(
        name="update_data",
        description="Modify existing data in tables",
        safe_for_readonly=False,
        examples=["Update status to shipped", "Change the price to $29.99"],
    ),
    "create_table": MSSQLToolInfo(
        name="create_table",
        description="Create new database tables",
        safe_for_readonly=False,
        examples=["Create a logs table", "Make an audit_trail table"],
    ),
    "drop_table": MSSQLToolInfo(
        name="drop_table",
        description="Delete tables from the database",
        safe_for_readonly=False,
        examples=["Remove the temp_data table", "Delete old_orders"],
    ),
    "create_index": MSSQLToolInfo(
        name="create_index",
        description="Create indexes for query optimization",
        safe_for_readonly=False,
        examples=["Create index on email column", "Add index for faster lookups"],
    ),
}


def get_readonly_tools() -> list[str]:
    """Get list of tools safe for read-only mode."""
    return [name for name, tool in MSSQL_TOOLS.items() if tool.safe_for_readonly]


def get_write_tools() -> list[str]:
    """Get list of tools that modify data."""
    return [name for name, tool in MSSQL_TOOLS.items() if not tool.safe_for_readonly]
