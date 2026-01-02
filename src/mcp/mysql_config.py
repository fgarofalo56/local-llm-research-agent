"""
MySQL MCP Server Configuration
Phase 4.6: Multi-Database Support

Handles building configuration for MySQL MCP Server including
environment variable resolution and validation.
"""

from dataclasses import dataclass, field

from src.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class MySQLMCPConfig:
    """Configuration for a MySQL MCP Server."""

    # Server execution
    command: str = "npx"
    mcp_path: str = "@benborber/mcp-server-mysql"

    # MySQL connection
    host: str = "localhost"
    port: int = 3306
    database: str = "mysql"
    username: str = ""
    password: str = ""

    # SSL settings
    ssl_enabled: bool = False

    # Connection options
    connection_timeout: int = 30

    @classmethod
    def from_connection(
        cls,
        host: str,
        port: int,
        database: str,
        username: str,
        password: str,
        ssl_enabled: bool = False,
    ) -> "MySQLMCPConfig":
        """Create config from connection parameters."""
        return cls(
            host=host,
            port=port,
            database=database,
            username=username,
            password=password,
            ssl_enabled=ssl_enabled,
        )

    def validate(self) -> list[str]:
        """
        Validate the configuration.

        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []

        if not self.host:
            errors.append("Host is not set")
        if not self.database:
            errors.append("Database is not set")
        if not self.username:
            errors.append("Username is required for MySQL")

        return errors

    def is_valid(self) -> bool:
        """Check if configuration is valid."""
        return len(self.validate()) == 0

    def get_connection_string(self) -> str:
        """
        Build MySQL connection string.

        Returns:
            MySQL connection URL
        """
        # Build connection URL
        auth = f"{self.username}:{self.password}@" if self.username else ""
        ssl_param = "?ssl=true" if self.ssl_enabled else ""
        return f"mysql://{auth}{self.host}:{self.port}/{self.database}{ssl_param}"

    def get_env(self) -> dict[str, str]:
        """
        Get environment variables for MCP server subprocess.

        Returns:
            Dictionary of environment variables
        """
        return {
            "MYSQL_HOST": self.host,
            "MYSQL_PORT": str(self.port),
            "MYSQL_DATABASE": self.database,
            "MYSQL_USER": self.username,
            "MYSQL_PASSWORD": self.password,
        }

    def get_args(self) -> list[str]:
        """Get command arguments for MCP server."""
        return ["-y", self.mcp_path]

    def log_config(self, mask_credentials: bool = True) -> None:
        """Log configuration for debugging."""
        logger.info(
            "mysql_mcp_config",
            host=self.host,
            port=self.port,
            database=self.database,
            username=self.username if not mask_credentials else "***",
            ssl_enabled=self.ssl_enabled,
        )

    def get_connection_info(self) -> dict:
        """Get connection info for display (credentials masked)."""
        return {
            "host": self.host,
            "port": self.port,
            "database": self.database,
            "username": self.username,
            "ssl_enabled": self.ssl_enabled,
            "db_type": "mysql",
        }


@dataclass
class MySQLToolInfo:
    """Information about MySQL MCP tools."""

    name: str
    description: str
    safe_for_readonly: bool = True
    examples: list[str] = field(default_factory=list)


# Available tools provided by MySQL MCP Server
MYSQL_TOOLS: dict[str, MySQLToolInfo] = {
    "query": MySQLToolInfo(
        name="query",
        description="Execute a SQL query",
        safe_for_readonly=True,
        examples=["SELECT * FROM users LIMIT 10", "Get all active orders"],
    ),
    "list_tables": MySQLToolInfo(
        name="list_tables",
        description="List all tables in the database",
        safe_for_readonly=True,
        examples=["What tables are available?", "Show me the schema"],
    ),
    "describe_table": MySQLToolInfo(
        name="describe_table",
        description="Get schema information for a specific table",
        safe_for_readonly=True,
        examples=["What columns does the users table have?"],
    ),
}
