"""
MCP Client Manager

Provides a high-level interface for managing multiple MCP server connections.
Supports dynamic loading/unloading, hot-reload, and configuration persistence.
"""

import json
import os
import re
from pathlib import Path
from typing import Any

from pydantic_ai.mcp import MCPServerStdio

from src.mcp.config import MCPConfigFile, MCPServerConfig
from src.mcp.mssql_config import MSSQLMCPConfig
from src.utils.logger import get_logger

logger = get_logger(__name__)


class MCPClientManager:
    """
    Manages MCP server configurations and connections.

    Supports:
    - Multiple simultaneous MCP servers
    - Dynamic server loading/unloading
    - Configuration persistence to JSON
    - Hot-reload capabilities
    """

    def __init__(self, config_path: str | Path | None = None):
        """
        Initialize the MCP client manager.

        Args:
            config_path: Optional path to mcp_config.json file
        """
        self.config_path = Path(config_path) if config_path else None
        self._servers: dict[str, MCPServerStdio] = {}
        self._config: MCPConfigFile | None = None

    def load_config(self) -> MCPConfigFile:
        """
        Load MCP configuration from JSON file.

        Returns:
            MCPConfigFile instance

        Raises:
            FileNotFoundError: If config file doesn't exist
            json.JSONDecodeError: If config file is invalid JSON
        """
        if self._config is not None:
            return self._config

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
            logger.warning("mcp_config_not_found", message="Creating default configuration")
            self._config = MCPConfigFile()
            return self._config

        logger.info("loading_mcp_config", path=str(self.config_path))

        with open(self.config_path) as f:
            data = json.load(f)

        self._config = MCPConfigFile.from_dict(data)
        return self._config

    def save_config(self) -> None:
        """Save current configuration to JSON file."""
        if self._config is None:
            return

        if self.config_path is None:
            self.config_path = Path("mcp_config.json")

        logger.info("saving_mcp_config", path=str(self.config_path))

        with open(self.config_path, "w") as f:
            json.dump(self._config.to_dict(), f, indent=2)

    def add_server(self, config: MCPServerConfig) -> None:
        """
        Add a new MCP server configuration.

        Args:
            config: Server configuration to add
        """
        if self._config is None:
            self._config = self.load_config()

        self._config.add_server(config)
        self.save_config()
        logger.info("mcp_server_added", name=config.name, type=config.server_type.value)

    def remove_server(self, name: str) -> bool:
        """
        Remove an MCP server configuration.

        Args:
            name: Server name to remove

        Returns:
            True if removed, False if not found
        """
        if self._config is None:
            self._config = self.load_config()

        # Stop the server if it's running
        if name in self._servers:
            del self._servers[name]

        removed = self._config.remove_server(name)
        if removed:
            self.save_config()
            logger.info("mcp_server_removed", name=name)

        return removed

    def enable_server(self, name: str) -> bool:
        """
        Enable an MCP server.

        Args:
            name: Server name to enable

        Returns:
            True if enabled, False if not found
        """
        if self._config is None:
            self._config = self.load_config()

        server_config = self._config.get_server(name)
        if server_config:
            server_config.enabled = True
            self.save_config()
            logger.info("mcp_server_enabled", name=name)
            return True

        return False

    def disable_server(self, name: str) -> bool:
        """
        Disable an MCP server without removing it.

        Args:
            name: Server name to disable

        Returns:
            True if disabled, False if not found
        """
        if self._config is None:
            self._config = self.load_config()

        server_config = self._config.get_server(name)
        if server_config:
            server_config.enabled = False
            # Remove from active servers
            if name in self._servers:
                del self._servers[name]
            self.save_config()
            logger.info("mcp_server_disabled", name=name)
            return True

        return False

    def list_servers(self) -> list[MCPServerConfig]:
        """
        List all configured MCP servers.

        Returns:
            List of server configurations
        """
        if self._config is None:
            self._config = self.load_config()

        return list(self._config.mcpServers.values())

    def get_active_toolsets(self) -> list[MCPServerStdio]:
        """
        Get list of active MCP server toolsets for agent.

        Only returns enabled servers that have been loaded.

        Returns:
            List of MCPServerStdio instances
        """
        if self._config is None:
            self._config = self.load_config()

        toolsets = []
        for server_config in self._config.get_enabled_servers():
            try:
                if server_config.name not in self._servers:
                    # Load server on demand
                    self._load_server(server_config)

                if server_config.name in self._servers:
                    toolsets.append(self._servers[server_config.name])
            except Exception as e:
                logger.warning(
                    "failed_to_load_toolset",
                    server=server_config.name,
                    error=str(e),
                )

        return toolsets

    def _load_server(self, config: MCPServerConfig) -> None:
        """
        Load an MCP server from configuration.

        Args:
            config: Server configuration

        Raises:
            ValueError: If configuration is invalid
        """
        # Skip servers with no command (HTTP-based servers not yet supported)
        if config.command is None:
            logger.info(
                "skipping_http_server",
                name=config.name,
                message="HTTP-based MCP servers not yet supported",
            )
            return

        # Resolve environment variables
        env = self._resolve_env(config.env)
        args = [self._resolve_env_vars(arg) for arg in config.args]

        server = MCPServerStdio(
            command=config.command,
            args=args,
            env=env,
            timeout=config.timeout,
        )

        self._servers[config.name] = server
        logger.info("mcp_server_loaded", name=config.name, type=config.server_type.value)

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
        if self._config is None:
            self._config = self.load_config()

        server_config = self._config.get_server(server_name)
        if not server_config:
            available = self._config.list_server_names()
            raise KeyError(f"Server '{server_name}' not found. Available: {available}")

        # Use the new loading mechanism
        if server_name not in self._servers:
            self._load_server(server_config)

        return self._servers[server_name]

    def list_configured_servers(self) -> list[str]:
        """
        List all servers defined in the configuration file.

        Returns:
            List of server names
        """
        if self._config is None:
            try:
                self._config = self.load_config()
            except FileNotFoundError:
                return []

        return self._config.list_server_names()

    def get_enabled_servers(self) -> list[MCPServerStdio]:
        """
        Get all enabled MCP servers as toolsets.
        
        Returns:
            List of MCPServerStdio instances for enabled servers
        """
        return self.get_active_toolsets()

    def clear_cache(self) -> None:
        """Clear the configuration cache and reload."""
        self._config = None
        self._servers.clear()
        logger.info("mcp_cache_cleared")

    def reconnect_server(self, name: str) -> bool:
        """
        Reconnect a failed MCP server.

        Args:
            name: Server name to reconnect

        Returns:
            True if reconnected successfully, False otherwise
        """
        if self._config is None:
            self._config = self.load_config()

        server_config = self._config.get_server(name)
        if not server_config:
            return False

        # Remove old instance
        if name in self._servers:
            del self._servers[name]

        # Try to load again
        try:
            self._load_server(server_config)
            logger.info("mcp_server_reconnected", name=name)
            return True
        except Exception as e:
            logger.error("mcp_reconnect_failed", name=name, error=str(e))
            return False

