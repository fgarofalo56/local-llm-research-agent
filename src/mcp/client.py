"""
MCP Client Manager

Provides a high-level interface for managing MCP server connections,
specifically for the MSSQL MCP Server integration.
"""

import json
import os
import re
from pathlib import Path
from typing import Any

from pydantic_ai.mcp import MCPServerStdio

from src.mcp.mssql_config import MSSQLMCPConfig
from src.utils.logger import get_logger

logger = get_logger(__name__)


class MCPClientManager:
    """
    Manages MCP server configurations and connections.

    Supports loading configuration from JSON files or programmatic setup.
    """

    def __init__(self, config_path: str | Path | None = None):
        """
        Initialize the MCP client manager.

        Args:
            config_path: Optional path to mcp_config.json file
        """
        self.config_path = Path(config_path) if config_path else None
        self._servers: dict[str, Any] = {}
        self._config_cache: dict | None = None

    def load_config(self) -> dict:
        """
        Load MCP configuration from JSON file.

        Returns:
            Configuration dictionary

        Raises:
            FileNotFoundError: If config file doesn't exist
            json.JSONDecodeError: If config file is invalid JSON
        """
        if self._config_cache is not None:
            return self._config_cache

        if self.config_path is None:
            # Look for config in default locations
            search_paths = [
                Path("mcp_config.json"),
                Path(__file__).parent.parent.parent / "mcp_config.json",
            ]
            for path in search_paths:
                if path.exists():
                    self.config_path = path
                    break

        if self.config_path is None or not self.config_path.exists():
            raise FileNotFoundError(
                "MCP configuration file not found. Create mcp_config.json or provide config_path."
            )

        logger.info("loading_mcp_config", path=str(self.config_path))

        with open(self.config_path) as f:
            config = json.load(f)

        self._config_cache = config
        return config

    def _resolve_env_vars(self, value: str) -> str:
        """
        Resolve environment variable placeholders in a string.

        Supports formats:
        - ${VAR} - Required variable
        - ${VAR:-default} - Variable with default value

        Args:
            value: String potentially containing env var placeholders

        Returns:
            String with resolved environment variables
        """
        # Pattern: ${VAR} or ${VAR:-default}
        pattern = r"\$\{([^}:]+)(?::-([^}]*))?\}"

        def replacer(match: re.Match) -> str:
            var_name = match.group(1)
            default = match.group(2)
            return os.environ.get(var_name, default or "")

        return re.sub(pattern, replacer, value)

    def _resolve_env(self, env_dict: dict[str, str]) -> dict[str, str]:
        """
        Resolve all environment variables in a dictionary.

        Args:
            env_dict: Dictionary with potential env var placeholders

        Returns:
            Dictionary with resolved values
        """
        return {key: self._resolve_env_vars(value) for key, value in env_dict.items()}

    def get_mssql_server(self) -> MCPServerStdio:
        """
        Get configured MSSQL MCP Server instance.

        Uses settings from application config and validates before creating.

        Returns:
            Configured MCPServerStdio instance

        Raises:
            ValueError: If configuration is invalid
        """
        config = MSSQLMCPConfig.from_settings()

        # Validate configuration
        errors = config.validate()
        if errors:
            error_msg = "MSSQL MCP configuration errors:\n" + "\n".join(f"  - {e}" for e in errors)
            logger.error("mssql_config_invalid", errors=errors)
            raise ValueError(error_msg)

        config.log_config()

        server = MCPServerStdio(
            command=config.command,
            args=config.get_args(),
            env=config.get_env(),
            timeout=config.timeout,
        )

        self._servers["mssql"] = server
        logger.info("mssql_server_created", readonly=config.readonly)

        return server

    def get_server_from_config(self, server_name: str) -> MCPServerStdio:
        """
        Get an MCP server by name from the configuration file.

        Args:
            server_name: Name of the server in mcpServers config

        Returns:
            Configured MCPServerStdio instance

        Raises:
            KeyError: If server name not found in config
            ValueError: If server config is invalid
        """
        config = self.load_config()

        if "mcpServers" not in config:
            raise ValueError("No mcpServers section in configuration")

        servers = config["mcpServers"]
        if server_name not in servers:
            available = list(servers.keys())
            raise KeyError(f"Server '{server_name}' not found. Available: {available}")

        server_config = servers[server_name]

        # Resolve environment variables in config
        env = self._resolve_env(server_config.get("env", {}))
        args = [self._resolve_env_vars(arg) for arg in server_config.get("args", [])]

        server = MCPServerStdio(
            command=server_config["command"],
            args=args,
            env=env,
            timeout=server_config.get("timeout", 30),
        )

        self._servers[server_name] = server
        logger.info("mcp_server_created", name=server_name)

        return server

    def list_configured_servers(self) -> list[str]:
        """
        List all servers defined in the configuration file.

        Returns:
            List of server names
        """
        try:
            config = self.load_config()
            return list(config.get("mcpServers", {}).keys())
        except FileNotFoundError:
            return []

    def clear_cache(self) -> None:
        """Clear the configuration cache."""
        self._config_cache = None
        self._servers.clear()
