"""
Configuration Management

Loads configuration from environment variables and provides a typed settings object.
Supports .env files via python-dotenv.
"""

from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings

# Load .env file from project root
_env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(_env_path)


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # LLM Provider Selection
    llm_provider: str = Field(
        default="ollama",
        description="LLM provider to use: 'ollama' or 'foundry_local'"
    )

    # Ollama Configuration
    ollama_host: str = Field(
        default="http://localhost:11434",
        description="Ollama server URL"
    )
    ollama_model: str = Field(
        default="qwen2.5:7b-instruct",
        description="Ollama model for inference"
    )

    # Foundry Local Configuration
    foundry_endpoint: str = Field(
        default="http://127.0.0.1:55588",
        description="Foundry Local API endpoint"
    )
    foundry_model: str = Field(
        default="phi-4",
        description="Foundry Local model alias"
    )
    foundry_auto_start: bool = Field(
        default=False,
        description="Auto-start Foundry Local using SDK"
    )

    # SQL Server Configuration
    sql_server_host: str = Field(
        default="localhost",
        description="SQL Server hostname"
    )
    sql_server_port: int = Field(
        default=1433,
        description="SQL Server port"
    )
    sql_database_name: str = Field(
        default="master",
        description="Database name"
    )
    sql_trust_server_certificate: bool = Field(
        default=True,
        description="Trust self-signed certificates"
    )
    sql_username: str = Field(
        default="",
        description="SQL Server username (blank for Windows Auth)"
    )
    sql_password: str = Field(
        default="",
        description="SQL Server password"
    )

    # MCP Configuration
    mcp_mssql_path: str = Field(
        default="",
        description="Path to MSSQL MCP Server index.js"
    )
    mcp_mssql_readonly: bool = Field(
        default=False,
        description="Enable read-only mode for safety"
    )
    mcp_debug: bool = Field(
        default=False,
        description="Enable MCP debug logging"
    )

    # Application Configuration
    log_level: str = Field(
        default="INFO",
        description="Logging level"
    )
    streamlit_port: int = Field(
        default=8501,
        description="Streamlit server port"
    )
    debug: bool = Field(
        default=False,
        description="Enable debug mode"
    )

    # Cache Configuration
    cache_enabled: bool = Field(
        default=True,
        description="Enable response caching for repeated queries"
    )
    cache_max_size: int = Field(
        default=100,
        description="Maximum number of cached responses"
    )
    cache_ttl_seconds: int = Field(
        default=3600,
        description="Cache time-to-live in seconds (0 = no expiration)"
    )

    # Rate Limiting Configuration
    rate_limit_enabled: bool = Field(
        default=False,
        description="Enable rate limiting for LLM API calls"
    )
    rate_limit_rpm: int = Field(
        default=60,
        description="Maximum requests per minute"
    )
    rate_limit_burst: int = Field(
        default=10,
        description="Maximum burst size (requests allowed before throttling)"
    )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

    @property
    def ollama_api_url(self) -> str:
        """Get the full Ollama API URL for OpenAI-compatible endpoint."""
        return f"{self.ollama_host}/v1"

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

    def get_mcp_env(self) -> dict[str, str]:
        """Get environment variables for MCP server."""
        env = {
            "SERVER_NAME": self.sql_server_host,
            "DATABASE_NAME": self.sql_database_name,
            "TRUST_SERVER_CERTIFICATE": str(self.sql_trust_server_certificate).lower(),
            "READONLY": str(self.mcp_mssql_readonly).lower(),
        }

        if self.sql_username:
            env["SQL_USERNAME"] = self.sql_username
        if self.sql_password:
            env["SQL_PASSWORD"] = self.sql_password

        return env


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
