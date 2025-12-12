"""
Database Manager

Manages multiple database configurations for connecting to different SQL Server instances.
Supports loading database profiles from environment or configuration file.
"""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from src.utils.config import settings
from src.utils.logger import get_logger

logger = get_logger(__name__)


class DatabaseConfig(BaseModel):
    """Configuration for a single database connection."""

    name: str = Field(..., description="Friendly name for the database")
    host: str = Field(default="localhost", description="SQL Server hostname")
    port: int = Field(default=1433, description="SQL Server port")
    database: str = Field(..., description="Database name")
    username: str = Field(default="", description="SQL username (blank for Windows Auth)")
    password: str = Field(default="", description="SQL password")
    trust_certificate: bool = Field(default=True, description="Trust server certificate")
    readonly: bool = Field(default=False, description="Read-only mode")
    description: str = Field(default="", description="Optional description")

    @property
    def connection_string_display(self) -> str:
        """Display-safe connection string (no password)."""
        auth = f"User={self.username}" if self.username else "Windows Auth"
        return f"{self.host},{self.port}/{self.database} ({auth})"

    def get_mcp_env(self) -> dict[str, str]:
        """Get environment variables for MCP server."""
        env = {
            "SERVER_NAME": self.host,
            "SERVER_PORT": str(self.port),
            "DATABASE_NAME": self.database,
            "TRUST_SERVER_CERTIFICATE": str(self.trust_certificate).lower(),
            "READONLY": str(self.readonly).lower(),
        }

        if self.username:
            env["SQL_USERNAME"] = self.username
        if self.password:
            env["SQL_PASSWORD"] = self.password

        return env


@dataclass
class DatabaseManager:
    """
    Manages multiple database configurations.

    Supports:
    - Loading from configuration file
    - Adding/removing databases at runtime
    - Switching active database
    - Listing available databases
    """

    config_file: Path | None = None
    _databases: dict[str, DatabaseConfig] = field(default_factory=dict)
    _active_db: str | None = None

    def __post_init__(self):
        """Initialize manager and load default database."""
        # Add default database from settings
        self._add_default_database()

        # Load from config file if provided
        if self.config_file and self.config_file.exists():
            self.load_from_file(self.config_file)

    def _add_default_database(self) -> None:
        """Add the default database from settings."""
        default_config = DatabaseConfig(
            name="default",
            host=settings.sql_server_host,
            port=settings.sql_server_port,
            database=settings.sql_database_name,
            username=settings.sql_username,
            password=settings.sql_password,
            trust_certificate=settings.sql_trust_server_certificate,
            readonly=settings.mcp_mssql_readonly,
            description="Default database from environment settings",
        )
        self._databases["default"] = default_config
        self._active_db = "default"

    def add_database(self, config: DatabaseConfig) -> None:
        """
        Add a database configuration.

        Args:
            config: Database configuration to add
        """
        if config.name in self._databases:
            logger.warning("database_replaced", name=config.name)

        self._databases[config.name] = config
        logger.info("database_added", name=config.name, host=config.host)

    def remove_database(self, name: str) -> bool:
        """
        Remove a database configuration.

        Args:
            name: Name of database to remove

        Returns:
            True if removed, False if not found
        """
        if name == "default":
            logger.warning("cannot_remove_default_database")
            return False

        if name in self._databases:
            del self._databases[name]
            if self._active_db == name:
                self._active_db = "default"
            logger.info("database_removed", name=name)
            return True

        return False

    def set_active(self, name: str) -> bool:
        """
        Set the active database.

        Args:
            name: Name of database to activate

        Returns:
            True if successful, False if database not found
        """
        if name not in self._databases:
            logger.error("database_not_found", name=name)
            return False

        self._active_db = name
        logger.info("database_activated", name=name)
        return True

    @property
    def active(self) -> DatabaseConfig | None:
        """Get the active database configuration."""
        if self._active_db:
            return self._databases.get(self._active_db)
        return None

    @property
    def active_name(self) -> str | None:
        """Get the name of the active database."""
        return self._active_db

    def list_databases(self) -> list[dict[str, Any]]:
        """
        List all configured databases.

        Returns:
            List of database info dictionaries
        """
        result = []
        for name, config in self._databases.items():
            result.append(
                {
                    "name": name,
                    "host": config.host,
                    "database": config.database,
                    "readonly": config.readonly,
                    "active": name == self._active_db,
                    "description": config.description,
                }
            )
        return result

    def get_database(self, name: str) -> DatabaseConfig | None:
        """
        Get a specific database configuration.

        Args:
            name: Database name

        Returns:
            DatabaseConfig or None if not found
        """
        return self._databases.get(name)

    def load_from_file(self, filepath: Path) -> int:
        """
        Load database configurations from a JSON file.

        Args:
            filepath: Path to configuration file

        Returns:
            Number of databases loaded

        File format:
        {
            "databases": [
                {
                    "name": "production",
                    "host": "prod-server",
                    "database": "Analytics",
                    "username": "user",
                    "password": "pass",
                    "readonly": true
                }
            ]
        }
        """
        try:
            with open(filepath) as f:
                data = json.load(f)

            databases = data.get("databases", [])
            count = 0

            for db_data in databases:
                try:
                    config = DatabaseConfig(**db_data)
                    self.add_database(config)
                    count += 1
                except Exception as e:
                    logger.warning("database_config_invalid", error=str(e), data=db_data)

            logger.info("databases_loaded_from_file", count=count, file=str(filepath))
            return count

        except Exception as e:
            logger.error("database_file_load_error", error=str(e), file=str(filepath))
            return 0

    def save_to_file(self, filepath: Path) -> bool:
        """
        Save database configurations to a JSON file.

        Args:
            filepath: Path to save configuration

        Returns:
            True if successful
        """
        try:
            data = {
                "databases": [
                    {
                        "name": config.name,
                        "host": config.host,
                        "port": config.port,
                        "database": config.database,
                        "username": config.username,
                        # Don't save passwords in plain text
                        "password": "***" if config.password else "",
                        "trust_certificate": config.trust_certificate,
                        "readonly": config.readonly,
                        "description": config.description,
                    }
                    for name, config in self._databases.items()
                    if name != "default"  # Don't save default, it comes from env
                ]
            }

            filepath.parent.mkdir(parents=True, exist_ok=True)
            with open(filepath, "w") as f:
                json.dump(data, f, indent=2)

            logger.info("databases_saved_to_file", file=str(filepath))
            return True

        except Exception as e:
            logger.error("database_file_save_error", error=str(e))
            return False


# Default config file location
DEFAULT_DB_CONFIG_PATH = Path.home() / ".local-llm-agent" / "databases.json"


def get_database_manager(config_file: Path | None = None) -> DatabaseManager:
    """
    Get a database manager instance.

    Args:
        config_file: Optional path to database config file

    Returns:
        Configured DatabaseManager
    """
    if config_file is None:
        config_file = DEFAULT_DB_CONFIG_PATH

    return DatabaseManager(config_file=config_file if config_file.exists() else None)
