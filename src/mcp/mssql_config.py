"""
MSSQL MCP Server Configuration

Handles building configuration for the MSSQL MCP Server including
environment variable resolution and validation.
Supports SQL Auth, Windows Auth, and Azure AD authentication.

Supports both:
- Python-based MCP server (microsoft_sql_server_mcp) for SQL Server authentication
- Node.js-based Azure-Samples MCP server for Azure AD authentication
"""

from dataclasses import dataclass, field
from pathlib import Path

from src.utils.config import SqlAuthType, settings
from src.utils.logger import get_logger

logger = get_logger(__name__)

# Marker value for Python-based MCP server
PYTHON_MCP_MARKER = "python-mcp"


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
    encrypt: bool = True
    readonly: bool = False

    # Authentication type
    auth_type: SqlAuthType = SqlAuthType.SQL_AUTH

    # SQL Server Authentication
    username: str = ""
    password: str = ""

    # Azure AD Service Principal Authentication
    azure_tenant_id: str = ""
    azure_client_id: str = ""
    azure_client_secret: str = ""

    # Server options
    timeout: int = 30

    @classmethod
    def from_settings(cls) -> "MSSQLMCPConfig":
        """Create config from application settings."""
        mcp_path = settings.mcp_mssql_path

        # Determine command based on MCP path
        command = "python" if mcp_path == PYTHON_MCP_MARKER else "node"

        return cls(
            command=command,
            mcp_path=mcp_path,
            server_name=settings.sql_server_host,
            database_name=settings.sql_database_name,
            trust_server_certificate=settings.sql_trust_server_certificate,
            encrypt=settings.sql_encrypt,
            readonly=settings.mcp_mssql_readonly,
            auth_type=settings.sql_auth_type,
            username=settings.sql_username,
            password=settings.sql_password,
            azure_tenant_id=settings.azure_tenant_id,
            azure_client_id=settings.azure_client_id,
            azure_client_secret=settings.azure_client_secret,
        )

    @property
    def is_python_mcp(self) -> bool:
        """Check if using Python-based MCP server."""
        return self.mcp_path == PYTHON_MCP_MARKER

    @property
    def is_azure_sql(self) -> bool:
        """Check if connecting to Azure SQL Database."""
        return ".database.windows.net" in self.server_name.lower()

    @property
    def requires_azure_auth(self) -> bool:
        """Check if Azure AD authentication is configured."""
        return self.auth_type in (
            SqlAuthType.AZURE_AD_INTERACTIVE,
            SqlAuthType.AZURE_AD_SERVICE_PRINCIPAL,
            SqlAuthType.AZURE_AD_MANAGED_IDENTITY,
            SqlAuthType.AZURE_AD_DEFAULT,
        )

    @property
    def auth_display(self) -> str:
        """Get human-readable authentication type for display."""
        display_names = {
            SqlAuthType.SQL_AUTH: f"SQL Server ({self.username or 'no user'})",
            SqlAuthType.WINDOWS_AUTH: "Windows Integrated",
            SqlAuthType.AZURE_AD_INTERACTIVE: "Azure AD Interactive",
            SqlAuthType.AZURE_AD_SERVICE_PRINCIPAL: f"Azure AD SP ({self.azure_client_id[:8]}...)"
            if self.azure_client_id
            else "Azure AD SP",
            SqlAuthType.AZURE_AD_MANAGED_IDENTITY: "Azure Managed Identity",
            SqlAuthType.AZURE_AD_DEFAULT: "Azure AD Default",
        }
        return display_names.get(self.auth_type, self.auth_type.value)

    def validate(self) -> list[str]:
        """
        Validate the configuration.

        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []

        # MCP path validation
        if not self.mcp_path:
            errors.append("MCP_MSSQL_PATH is not set")
        elif self.mcp_path == PYTHON_MCP_MARKER:
            # Python MCP server - no path validation needed
            pass
        elif not Path(self.mcp_path).exists():
            errors.append(f"MCP_MSSQL_PATH does not exist: {self.mcp_path}")

        # Server validation
        if not self.server_name:
            errors.append("SQL_SERVER_HOST is not set")

        if not self.database_name:
            errors.append("SQL_DATABASE_NAME is not set")

        # Authentication validation
        if self.auth_type == SqlAuthType.SQL_AUTH:
            if not self.username:
                errors.append("SQL_USERNAME is required for SQL authentication")
            if not self.password:
                errors.append("SQL_PASSWORD is required for SQL authentication")

        elif self.auth_type == SqlAuthType.AZURE_AD_SERVICE_PRINCIPAL:
            if not self.azure_tenant_id:
                errors.append("AZURE_TENANT_ID is required for service principal authentication")
            if not self.azure_client_id:
                errors.append("AZURE_CLIENT_ID is required for service principal authentication")
            if not self.azure_client_secret:
                errors.append(
                    "AZURE_CLIENT_SECRET is required for service principal authentication"
                )

        elif self.auth_type == SqlAuthType.WINDOWS_AUTH:
            if self.username or self.password:
                errors.append(
                    "SQL_USERNAME and SQL_PASSWORD should be empty for Windows authentication"
                )

        # Azure SQL requires encryption
        if self.is_azure_sql and not self.encrypt:
            errors.append("SQL_ENCRYPT must be true for Azure SQL Database connections")

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
        if self.is_python_mcp:
            # Python-based MCP server (microsoft_sql_server_mcp)
            # Uses different environment variable names
            # Note: pymssql doesn't support encrypt parameter the same way
            env = {
                "MSSQL_SERVER": self.server_name,
                "MSSQL_DATABASE": self.database_name,
            }

            # Add authentication-specific environment variables
            if self.auth_type == SqlAuthType.SQL_AUTH:
                env["MSSQL_USER"] = self.username
                env["MSSQL_PASSWORD"] = self.password
            elif self.auth_type == SqlAuthType.WINDOWS_AUTH:
                env["MSSQL_WINDOWS_AUTH"] = "true"

            # Note: pymssql doesn't support encrypt parameter directly
            # The connection uses TLS automatically when server requires it

            return env

        # Node.js-based MCP server (Azure-Samples)
        env = {
            "SERVER_NAME": self.server_name,
            "DATABASE_NAME": self.database_name,
            "TRUST_SERVER_CERTIFICATE": str(self.trust_server_certificate).lower(),
            "ENCRYPT": str(self.encrypt).lower(),
            "READONLY": str(self.readonly).lower(),
            "AUTH_TYPE": self.auth_type.value,
        }

        # Add authentication-specific environment variables
        if self.auth_type == SqlAuthType.SQL_AUTH:
            if self.username:
                env["SQL_USERNAME"] = self.username
            if self.password:
                env["SQL_PASSWORD"] = self.password

        elif self.auth_type == SqlAuthType.WINDOWS_AUTH:
            env["WINDOWS_AUTH"] = "true"

        elif self.auth_type == SqlAuthType.AZURE_AD_INTERACTIVE:
            env["AZURE_AD_INTERACTIVE"] = "true"
            # The MCP server should handle interactive browser login

        elif self.auth_type == SqlAuthType.AZURE_AD_SERVICE_PRINCIPAL:
            if self.azure_tenant_id:
                env["AZURE_TENANT_ID"] = self.azure_tenant_id
            if self.azure_client_id:
                env["AZURE_CLIENT_ID"] = self.azure_client_id
            if self.azure_client_secret:
                env["AZURE_CLIENT_SECRET"] = self.azure_client_secret

        elif self.auth_type == SqlAuthType.AZURE_AD_MANAGED_IDENTITY:
            env["AZURE_AD_MANAGED_IDENTITY"] = "true"
            if self.azure_client_id:
                # User-assigned managed identity
                env["AZURE_CLIENT_ID"] = self.azure_client_id

        elif self.auth_type == SqlAuthType.AZURE_AD_DEFAULT:
            env["AZURE_AD_DEFAULT"] = "true"
            # Uses DefaultAzureCredential chain - tries multiple auth methods

        return env

    def get_args(self) -> list[str]:
        """Get command arguments for MCP server."""
        if self.is_python_mcp:
            # Use our custom pyodbc-based MCP server
            return ["-m", "src.mcp.pyodbc_mssql_server"]
        return [self.mcp_path]

    def log_config(self, mask_credentials: bool = True) -> None:
        """Log configuration for debugging."""
        logger.info(
            "mssql_mcp_config",
            server_name=self.server_name,
            database_name=self.database_name,
            auth_type=self.auth_type.value,
            auth_display=self.auth_display,
            readonly=self.readonly,
            encrypt=self.encrypt,
            mcp_path=self.mcp_path,
            is_python_mcp=self.is_python_mcp,
            is_azure_sql=self.is_azure_sql,
            has_sql_credentials=bool(self.username),
            has_azure_credentials=bool(self.azure_client_id),
        )

    def get_connection_info(self) -> dict:
        """Get connection info for display (credentials masked)."""
        return {
            "server": self.server_name,
            "database": self.database_name,
            "auth_type": self.auth_display,
            "readonly": self.readonly,
            "encrypt": self.encrypt,
            "is_azure": self.is_azure_sql,
            "mcp_type": "python" if self.is_python_mcp else "node",
        }


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
