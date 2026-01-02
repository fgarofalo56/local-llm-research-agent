"""
Configuration Management

Loads configuration from environment variables and provides a typed settings object.
Supports .env files via python-dotenv.

NOTE: This module is being refactored to use ConfigService for centralized configuration.
The Settings class will gradually be replaced by ConfigService from src.services.config_service.
"""

from enum import Enum
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings

# Load .env file from project root
_env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(_env_path)

# Import ConfigService for future migration
try:
    from src.services.config_service import get_config as get_config_service
except ImportError:
    get_config_service = None  # type: ignore


class SqlAuthType(str, Enum):
    """SQL Server authentication types."""

    SQL_AUTH = "sql"  # SQL Server authentication (username/password)
    WINDOWS_AUTH = "windows"  # Windows integrated authentication
    AZURE_AD_INTERACTIVE = "azure_ad_interactive"  # Azure AD interactive (browser)
    AZURE_AD_SERVICE_PRINCIPAL = "azure_ad_service_principal"  # Azure AD app credentials
    AZURE_AD_MANAGED_IDENTITY = "azure_ad_managed_identity"  # Azure managed identity
    AZURE_AD_DEFAULT = "azure_ad_default"  # Azure DefaultAzureCredential (auto-detect)


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # LLM Provider Selection
    llm_provider: str = Field(
        default="ollama", description="LLM provider to use: 'ollama' or 'foundry_local'"
    )

    # Ollama Configuration
    ollama_host: str = Field(default="http://localhost:11434", description="Ollama server URL")
    ollama_model: str = Field(
        default="qwen2.5:7b-instruct", description="Ollama model for inference"
    )

    # Foundry Local Configuration
    foundry_endpoint: str = Field(
        default="http://127.0.0.1:53760", description="Foundry Local API endpoint"
    )
    foundry_model: str = Field(default="phi-4", description="Foundry Local model alias")
    foundry_auto_start: bool = Field(
        default=False, description="Auto-start Foundry Local using SDK"
    )

    # SQL Server Configuration
    sql_server_host: str = Field(default="localhost", description="SQL Server hostname")
    sql_server_port: int = Field(default=1433, description="SQL Server port")
    sql_database_name: str = Field(default="master", description="Database name")
    sql_trust_server_certificate: bool = Field(
        default=True, description="Trust self-signed certificates"
    )
    sql_encrypt: bool = Field(
        default=True, description="Encrypt connection (required for Azure SQL)"
    )

    # SQL Authentication Type
    sql_auth_type: SqlAuthType = Field(
        default=SqlAuthType.SQL_AUTH,
        description="Authentication type: sql, windows, azure_ad_interactive, azure_ad_service_principal, azure_ad_managed_identity, azure_ad_default",
    )

    # SQL Server Authentication (for sql auth type)
    sql_username: str = Field(default="", description="SQL Server username (for SQL auth)")
    sql_password: str = Field(default="", description="SQL Server password (for SQL auth)")

    # Azure AD Service Principal Authentication
    azure_tenant_id: str = Field(
        default="", description="Azure tenant ID (for service principal auth)"
    )
    azure_client_id: str = Field(
        default="",
        description="Azure client/application ID (for service principal or managed identity)",
    )
    azure_client_secret: str = Field(
        default="", description="Azure client secret (for service principal auth)"
    )

    # MCP Configuration
    mcp_mssql_path: str = Field(default="", description="Path to MSSQL MCP Server index.js")
    mcp_mssql_readonly: bool = Field(default=False, description="Enable read-only mode for safety")
    mcp_debug: bool = Field(default=False, description="Enable MCP debug logging")

    # Application Configuration
    log_level: str = Field(default="INFO", description="Logging level")
    streamlit_port: int = Field(default=8501, description="Streamlit server port")
    debug: bool = Field(default=False, description="Enable debug mode")

    # Cache Configuration
    cache_enabled: bool = Field(
        default=True, description="Enable response caching for repeated queries"
    )
    cache_max_size: int = Field(default=100, description="Maximum number of cached responses")
    cache_ttl_seconds: int = Field(
        default=3600, description="Cache time-to-live in seconds (0 = no expiration)"
    )

    # Rate Limiting Configuration
    rate_limit_enabled: bool = Field(
        default=False, description="Enable rate limiting for LLM API calls"
    )
    rate_limit_rpm: int = Field(default=60, description="Maximum requests per minute")
    rate_limit_burst: int = Field(
        default=10, description="Maximum burst size (requests allowed before throttling)"
    )

    # Docker/SA Password (for docker-compose compatibility)
    mssql_sa_password: str = Field(
        default="", description="SQL Server SA password (used by docker-compose)"
    )

    # ===== Phase 2.1 Settings =====

    # ===== Backend Database (SQL Server 2025 with native vectors) =====
    backend_db_host: str = Field(
        default="localhost", description="Backend SQL Server 2025 hostname"
    )
    backend_db_port: int = Field(default=1434, description="Backend SQL Server port")
    backend_db_name: str = Field(
        default="LLM_BackEnd", description="Backend database name"
    )
    backend_db_username: str = Field(
        default="", description="Backend database username (defaults to sql_username)"
    )
    backend_db_password: str = Field(
        default="", description="Backend database password (defaults to sql_password)"
    )
    backend_db_trust_cert: bool = Field(
        default=True, description="Trust self-signed certificates for backend"
    )

    # Vector Store Configuration
    vector_store_type: str = Field(
        default="mssql",
        description="Vector store type: 'mssql' (SQL Server 2025) or 'redis'",
    )
    vector_dimensions: int = Field(
        default=768, description="Embedding dimensions (768 for nomic-embed-text)"
    )

    # Redis (for caching, optional vector fallback)
    redis_url: str = Field(default="redis://localhost:6379", description="Redis connection URL")

    # Embeddings
    embedding_model: str = Field(
        default="nomic-embed-text", description="Ollama model for generating embeddings"
    )

    # Storage
    upload_dir: str = Field(
        default="./data/uploads", description="Directory for uploaded documents"
    )
    max_upload_size_mb: int = Field(default=100, description="Maximum file upload size in MB")

    # RAG
    chunk_size: int = Field(default=500, description="Document chunk size for RAG")
    chunk_overlap: int = Field(default=50, description="Overlap between document chunks")
    rag_top_k: int = Field(default=5, description="Number of chunks to retrieve for RAG")

    # API
    api_host: str = Field(default="0.0.0.0", description="API server bind address")
    api_port: int = Field(default=8000, description="API server port")

    # MCP Config Path
    mcp_config_path: str = Field(
        default="mcp_config.json", description="Path to MCP server configuration file"
    )

    @field_validator("mcp_config_path", mode="after")
    @classmethod
    def resolve_mcp_config_path(cls, v: str) -> str:
        """Resolve mcp_config_path to absolute path relative to project root."""
        config_path = Path(v)
        if not config_path.is_absolute():
            # Resolve relative to project root (parent of src/)
            project_root = Path(__file__).parent.parent.parent
            config_path = project_root / v
        return str(config_path.resolve())

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"  # Ignore extra env vars not defined in Settings

    @field_validator("sql_auth_type", mode="before")
    @classmethod
    def validate_auth_type(cls, v):
        """Validate and normalize auth type."""
        if isinstance(v, SqlAuthType):
            return v
        if isinstance(v, str):
            # Normalize the string
            v_lower = v.lower().strip()
            # Handle common aliases
            aliases = {
                "sql": SqlAuthType.SQL_AUTH,
                "sql_auth": SqlAuthType.SQL_AUTH,
                "sqlauth": SqlAuthType.SQL_AUTH,
                "windows": SqlAuthType.WINDOWS_AUTH,
                "windows_auth": SqlAuthType.WINDOWS_AUTH,
                "integrated": SqlAuthType.WINDOWS_AUTH,
                "azure_ad": SqlAuthType.AZURE_AD_DEFAULT,
                "azure_ad_interactive": SqlAuthType.AZURE_AD_INTERACTIVE,
                "azure_interactive": SqlAuthType.AZURE_AD_INTERACTIVE,
                "interactive": SqlAuthType.AZURE_AD_INTERACTIVE,
                "azure_ad_service_principal": SqlAuthType.AZURE_AD_SERVICE_PRINCIPAL,
                "service_principal": SqlAuthType.AZURE_AD_SERVICE_PRINCIPAL,
                "sp": SqlAuthType.AZURE_AD_SERVICE_PRINCIPAL,
                "azure_ad_managed_identity": SqlAuthType.AZURE_AD_MANAGED_IDENTITY,
                "managed_identity": SqlAuthType.AZURE_AD_MANAGED_IDENTITY,
                "msi": SqlAuthType.AZURE_AD_MANAGED_IDENTITY,
                "azure_ad_default": SqlAuthType.AZURE_AD_DEFAULT,
                "default": SqlAuthType.AZURE_AD_DEFAULT,
            }
            if v_lower in aliases:
                return aliases[v_lower]
            # Try direct enum value
            try:
                return SqlAuthType(v_lower)
            except ValueError:
                pass
        raise ValueError(f"Invalid SQL auth type: {v}")

    @property
    def ollama_api_url(self) -> str:
        """Get the full Ollama API URL for OpenAI-compatible endpoint."""
        return f"{self.ollama_host}/v1"

    @property
    def database_url(self) -> str:
        """Get sync database URL for SQLAlchemy."""
        password = self.sql_password.replace("@", "%40")
        return (
            f"mssql+pyodbc://{self.sql_username}:{password}@"
            f"{self.sql_server_host}:{self.sql_server_port}/{self.sql_database_name}"
            f"?driver=ODBC+Driver+18+for+SQL+Server&TrustServerCertificate=yes"
        )

    @property
    def database_url_async(self) -> str:
        """Get async database URL for SQLAlchemy (sample database)."""
        password = self.sql_password.replace("@", "%40")
        return (
            f"mssql+aioodbc://{self.sql_username}:{password}@"
            f"{self.sql_server_host}:{self.sql_server_port}/{self.sql_database_name}"
            f"?driver=ODBC+Driver+18+for+SQL+Server&TrustServerCertificate=yes"
        )

    @property
    def backend_database_url(self) -> str:
        """Get sync database URL for backend database (LLM_BackEnd)."""
        username = self.backend_db_username or self.sql_username
        password = (self.backend_db_password or self.sql_password).replace("@", "%40")
        trust_cert = "yes" if self.backend_db_trust_cert else "no"
        return (
            f"mssql+pyodbc://{username}:{password}@"
            f"{self.backend_db_host}:{self.backend_db_port}/{self.backend_db_name}"
            f"?driver=ODBC+Driver+18+for+SQL+Server&TrustServerCertificate={trust_cert}"
        )

    @property
    def backend_database_url_async(self) -> str:
        """Get async database URL for backend database (LLM_BackEnd with vectors)."""
        username = self.backend_db_username or self.sql_username
        password = (self.backend_db_password or self.sql_password).replace("@", "%40")
        trust_cert = "yes" if self.backend_db_trust_cert else "no"
        return (
            f"mssql+aioodbc://{username}:{password}@"
            f"{self.backend_db_host}:{self.backend_db_port}/{self.backend_db_name}"
            f"?driver=ODBC+Driver+18+for+SQL+Server&TrustServerCertificate={trust_cert}"
        )

    @property
    def is_azure_sql(self) -> bool:
        """Check if connecting to Azure SQL Database."""
        return ".database.windows.net" in self.sql_server_host.lower()

    @property
    def requires_azure_auth(self) -> bool:
        """Check if Azure AD authentication is configured."""
        return self.sql_auth_type in (
            SqlAuthType.AZURE_AD_INTERACTIVE,
            SqlAuthType.AZURE_AD_SERVICE_PRINCIPAL,
            SqlAuthType.AZURE_AD_MANAGED_IDENTITY,
            SqlAuthType.AZURE_AD_DEFAULT,
        )

    def validate_ollama_model(self) -> bool:
        """Check if the configured model supports tool calling."""
        tool_capable_models = [
            "qwen2.5",
            "llama3.1",
            "llama3.2",
            "mistral",
            "mixtral",
            "command-r",
            "firefunction",
        ]
        model_lower = self.ollama_model.lower()
        return any(model in model_lower for model in tool_capable_models)

    def validate_auth_config(self) -> list[str]:
        """
        Validate authentication configuration.

        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []

        if self.sql_auth_type == SqlAuthType.SQL_AUTH:
            if not self.sql_username:
                errors.append("SQL_USERNAME is required for SQL authentication")
            if not self.sql_password:
                errors.append("SQL_PASSWORD is required for SQL authentication")

        elif self.sql_auth_type == SqlAuthType.AZURE_AD_SERVICE_PRINCIPAL:
            if not self.azure_tenant_id:
                errors.append("AZURE_TENANT_ID is required for service principal authentication")
            if not self.azure_client_id:
                errors.append("AZURE_CLIENT_ID is required for service principal authentication")
            if not self.azure_client_secret:
                errors.append(
                    "AZURE_CLIENT_SECRET is required for service principal authentication"
                )

        elif self.sql_auth_type == SqlAuthType.AZURE_AD_MANAGED_IDENTITY:
            # Client ID is optional for system-assigned managed identity
            pass

        elif self.sql_auth_type == SqlAuthType.AZURE_AD_INTERACTIVE:
            # No additional config required - uses browser login
            pass

        elif self.sql_auth_type == SqlAuthType.AZURE_AD_DEFAULT:
            # Uses DefaultAzureCredential - auto-detects available credentials
            pass

        elif self.sql_auth_type == SqlAuthType.WINDOWS_AUTH:
            # No additional config required - uses current Windows credentials
            if self.sql_username or self.sql_password:
                errors.append(
                    "SQL_USERNAME and SQL_PASSWORD should be empty for Windows authentication"
                )

        # Azure SQL requires encryption
        if self.is_azure_sql and not self.sql_encrypt:
            errors.append("SQL_ENCRYPT must be true for Azure SQL Database connections")

        return errors

    def get_mcp_env(self) -> dict[str, str]:
        """Get environment variables for MCP server."""
        env = {
            "SERVER_NAME": self.sql_server_host,
            "DATABASE_NAME": self.sql_database_name,
            "TRUST_SERVER_CERTIFICATE": str(self.sql_trust_server_certificate).lower(),
            "READONLY": str(self.mcp_mssql_readonly).lower(),
            "ENCRYPT": str(self.sql_encrypt).lower(),
        }

        # Set authentication type for MCP server
        env["AUTH_TYPE"] = self.sql_auth_type.value

        # Add auth-specific environment variables
        if self.sql_auth_type == SqlAuthType.SQL_AUTH:
            if self.sql_username:
                env["SQL_USERNAME"] = self.sql_username
            if self.sql_password:
                env["SQL_PASSWORD"] = self.sql_password

        elif self.sql_auth_type == SqlAuthType.AZURE_AD_SERVICE_PRINCIPAL:
            if self.azure_tenant_id:
                env["AZURE_TENANT_ID"] = self.azure_tenant_id
            if self.azure_client_id:
                env["AZURE_CLIENT_ID"] = self.azure_client_id
            if self.azure_client_secret:
                env["AZURE_CLIENT_SECRET"] = self.azure_client_secret

        elif self.sql_auth_type == SqlAuthType.AZURE_AD_MANAGED_IDENTITY:
            if self.azure_client_id:
                env["AZURE_CLIENT_ID"] = self.azure_client_id  # For user-assigned MI

        elif self.sql_auth_type == SqlAuthType.AZURE_AD_INTERACTIVE:
            # Browser-based login - no additional env vars needed
            env["AZURE_AD_INTERACTIVE"] = "true"

        elif self.sql_auth_type == SqlAuthType.AZURE_AD_DEFAULT:
            # Uses DefaultAzureCredential chain
            env["AZURE_AD_DEFAULT"] = "true"

        return env

    def get_auth_display(self) -> str:
        """Get human-readable authentication type for display."""
        display_names = {
            SqlAuthType.SQL_AUTH: f"SQL Server ({self.sql_username or 'no user'})",
            SqlAuthType.WINDOWS_AUTH: "Windows Integrated",
            SqlAuthType.AZURE_AD_INTERACTIVE: "Azure AD Interactive",
            SqlAuthType.AZURE_AD_SERVICE_PRINCIPAL: f"Azure AD Service Principal ({self.azure_client_id[:8]}...)"
            if self.azure_client_id
            else "Azure AD Service Principal",
            SqlAuthType.AZURE_AD_MANAGED_IDENTITY: "Azure Managed Identity",
            SqlAuthType.AZURE_AD_DEFAULT: "Azure AD (Default Credential)",
        }
        return display_names.get(self.sql_auth_type, self.sql_auth_type.value)


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Convenience alias
settings = get_settings()


def reload_settings() -> Settings:
    """Reload settings (clears cache)."""
    get_settings.cache_clear()
    return get_settings()
