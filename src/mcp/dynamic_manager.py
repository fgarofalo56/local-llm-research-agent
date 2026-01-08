"""
Dynamic MCP Manager
Phase 2.1: Backend Infrastructure & RAG Pipeline

Dynamically loads and manages MCP servers from configuration.
Supports stdio and HTTP server types with environment variable expansion.
"""

import json
import os
import re
from pathlib import Path
from typing import Any

import structlog
from pydantic import BaseModel

logger = structlog.get_logger()


class MCPServerConfig(BaseModel):
    """Configuration for an MCP server."""

    id: str
    name: str
    description: str = ""
    type: str  # 'stdio' or 'http'
    command: str | None = None
    args: list[str] = []
    url: str | None = None
    env: dict[str, str] = {}
    enabled: bool = True
    built_in: bool = False


class DynamicMCPManager:
    """Manage MCP servers dynamically from configuration."""

    DEFAULT_SERVERS = {
        "mssql": MCPServerConfig(
            id="mssql",
            name="MSSQL Server",
            description="SQL Server database access via MCP",
            type="stdio",
            command="node",
            args=["${MCP_MSSQL_PATH}"],
            env={
                "SERVER_NAME": "${SQL_SERVER_HOST}",
                "DATABASE_NAME": "${SQL_DATABASE_NAME}",
                "TRUST_SERVER_CERTIFICATE": "true",
            },
            enabled=True,
            built_in=True,
        ),
        "analytics-management": MCPServerConfig(
            id="analytics-management",
            name="Analytics Management",
            description="Dashboard, widget, and query management",
            type="python",
            command="uv",
            args=["run", "python", "-m", "src.mcp.analytics_mcp_server"],
            env={
                "BACKEND_DB_HOST": "${BACKEND_DB_HOST:-localhost}",
                "BACKEND_DB_PORT": "${BACKEND_DB_PORT:-1434}",
                "BACKEND_DB_NAME": "${BACKEND_DB_NAME:-LLM_BackEnd}",
            },
            enabled=True,
            built_in=True,
        ),
        "data-analytics": MCPServerConfig(
            id="data-analytics",
            name="Data Analytics",
            description="Statistical analysis, aggregations, time series, anomaly detection",
            type="python",
            command="uv",
            args=["run", "python", "-m", "src.mcp.data_analytics_mcp_server"],
            env={
                "SQL_SERVER_HOST": "${SQL_SERVER_HOST:-localhost}",
                "SQL_SERVER_PORT": "${SQL_SERVER_PORT:-1433}",
                "SQL_DATABASE_NAME": "${SQL_DATABASE_NAME:-ResearchAnalytics}",
                "BACKEND_DB_HOST": "${BACKEND_DB_HOST:-localhost}",
                "BACKEND_DB_PORT": "${BACKEND_DB_PORT:-1434}",
                "BACKEND_DB_NAME": "${BACKEND_DB_NAME:-LLM_BackEnd}",
            },
            enabled=True,
            built_in=True,
        ),
    }

    def __init__(self, config_path: str = "mcp_config.json"):
        """
        Initialize the MCP manager.

        Args:
            config_path: Path to the MCP configuration file
        """
        self.config_path = Path(config_path)
        self.servers: dict[str, MCPServerConfig] = {}
        self._active_servers: dict[str, Any] = {}

    async def load_config(self) -> None:
        """Load configuration from file."""
        # Start with defaults
        self.servers = dict(self.DEFAULT_SERVERS)

        # Load user config if exists
        if self.config_path.exists():
            try:
                with open(self.config_path) as f:
                    config = json.load(f)

                for server_id, server_config in config.get("mcpServers", {}).items():
                    # Check if this is a built-in server - preserve built_in status
                    is_built_in = server_id in self.DEFAULT_SERVERS

                    if is_built_in:
                        # For built-in servers, only update mutable fields, preserve built_in flag
                        default_config = self.DEFAULT_SERVERS[server_id]
                        self.servers[server_id] = MCPServerConfig(
                            id=server_id,
                            name=server_config.get("name", default_config.name),
                            description=server_config.get(
                                "description", default_config.description
                            ),
                            type=server_config.get("type", default_config.type),
                            command=server_config.get("command", default_config.command),
                            args=server_config.get("args", default_config.args),
                            url=server_config.get("url", default_config.url),
                            env=server_config.get("env", default_config.env),
                            enabled=server_config.get("enabled", default_config.enabled),
                            built_in=True,  # Preserve built-in status
                        )
                    else:
                        # User-added server
                        self.servers[server_id] = MCPServerConfig(
                            id=server_id,
                            name=server_config.get("name", server_id),
                            description=server_config.get("description", ""),
                            type=server_config.get("type", "stdio"),
                            command=server_config.get("command"),
                            args=server_config.get("args", []),
                            url=server_config.get("url"),
                            env=server_config.get("env", {}),
                            enabled=server_config.get("enabled", True),
                            built_in=False,
                        )
            except Exception as e:
                logger.warning("mcp_config_load_error", error=str(e))

        logger.info("mcp_config_loaded", server_count=len(self.servers))

    async def save_config(self) -> None:
        """Save configuration to file, preserving existing structure."""
        # Load existing config to preserve non-server fields (like $schema, _documentation)
        existing_config: dict[str, Any] = {}
        if self.config_path.exists():
            try:
                with open(self.config_path) as f:
                    existing_config = json.load(f)
            except Exception:
                pass  # If file is corrupted, we'll create a new one

        # Ensure mcpServers dict exists
        if "mcpServers" not in existing_config:
            existing_config["mcpServers"] = {}

        # Update server configurations
        for server_id, server in self.servers.items():
            if not server.built_in:
                # Save user-added servers with all their config
                existing_config["mcpServers"][server_id] = {
                    "name": server.name,
                    "description": server.description,
                    "type": server.type,
                    "command": server.command,
                    "args": server.args,
                    "url": server.url,
                    "env": server.env,
                    "enabled": server.enabled,
                }

        # Remove any servers that were deleted (user-added ones not in self.servers)
        servers_to_remove = []
        for server_id in existing_config["mcpServers"]:
            # Only remove if it's not a built-in and not in our current list
            if server_id not in self.DEFAULT_SERVERS and server_id not in self.servers:
                servers_to_remove.append(server_id)

        for server_id in servers_to_remove:
            del existing_config["mcpServers"][server_id]

        with open(self.config_path, "w") as f:
            json.dump(existing_config, f, indent=2)

        logger.info("mcp_config_saved")

    def _expand_env_vars(self, value: str) -> str:
        """
        Expand environment variables in string.

        Supports ${VAR_NAME} and ${VAR_NAME:-default} syntax.
        """

        def replace_var(match):
            var_name = match.group(1)
            default = match.group(2)
            return os.environ.get(var_name, default or "")

        # Pattern: ${VAR} or ${VAR:-default}
        return re.sub(r"\$\{([^}:]+)(?::-([^}]*))?\}", replace_var, value)

    def get_mcp_server(self, server_id: str):
        """
        Get an MCP server instance.

        Args:
            server_id: Server identifier

        Returns:
            MCPServerStdio or MCPServerStreamableHTTP instance, or None
        """
        if server_id not in self.servers:
            return None

        config = self.servers[server_id]
        if not config.enabled:
            return None

        if config.type == "stdio" or config.type == "python":
            from pydantic_ai.mcp import MCPServerStdio

            # Expand environment variables
            command = self._expand_env_vars(config.command) if config.command else None
            args = [self._expand_env_vars(arg) for arg in config.args]
            env = {k: self._expand_env_vars(v) for k, v in config.env.items()}

            # Merge with current environment for Python servers to inherit PATH, etc.
            if config.type == "python":
                full_env = dict(os.environ)
                full_env.update(env)
                env = full_env

            return MCPServerStdio(
                command=command,
                args=args,
                env=env,
                timeout=60,  # Longer timeout for Python servers
            )

        elif config.type == "http":
            from pydantic_ai.mcp import MCPServerHTTP

            url = self._expand_env_vars(config.url) if config.url else None
            return MCPServerHTTP(url=url)

        elif config.type == "streamable_http":
            from pydantic_ai.mcp import MCPServerStreamableHTTP

            url = self._expand_env_vars(config.url) if config.url else None
            return MCPServerStreamableHTTP(url=url)

        return None

    def get_enabled_servers(self) -> list:
        """
        Get all enabled MCP servers.

        Returns:
            List of MCP server instances
        """
        servers = []
        for server_id in self.servers:
            server = self.get_mcp_server(server_id)
            if server:
                servers.append(server)
        return servers

    def get_servers_by_ids(self, server_ids: list[str]) -> list:
        """
        Get specific MCP servers by ID.

        Args:
            server_ids: List of server IDs

        Returns:
            List of MCP server instances
        """
        servers = []
        for server_id in server_ids:
            server = self.get_mcp_server(server_id)
            if server:
                servers.append(server)
        return servers

    def list_servers(self) -> list[MCPServerConfig]:
        """
        List all configured servers.

        Returns:
            List of server configurations
        """
        return list(self.servers.values())

    async def add_server(self, config: MCPServerConfig) -> None:
        """
        Add a new MCP server.

        Args:
            config: Server configuration
        """
        self.servers[config.id] = config
        await self.save_config()
        logger.info("mcp_server_added", server_id=config.id)

    async def update_server(self, server_id: str, updates: dict[str, Any]) -> None:
        """
        Update an existing server.

        Args:
            server_id: Server identifier
            updates: Dictionary of fields to update

        Raises:
            ValueError: If server not found
        """
        if server_id not in self.servers:
            raise ValueError(f"Server not found: {server_id}")

        server = self.servers[server_id]
        for key, value in updates.items():
            if hasattr(server, key):
                setattr(server, key, value)

        await self.save_config()
        logger.info("mcp_server_updated", server_id=server_id)

    async def remove_server(self, server_id: str) -> None:
        """
        Remove an MCP server.

        Args:
            server_id: Server identifier

        Raises:
            ValueError: If server not found or is built-in
        """
        if server_id not in self.servers:
            raise ValueError(f"Server not found: {server_id}")

        if self.servers[server_id].built_in:
            raise ValueError("Cannot remove built-in server")

        del self.servers[server_id]
        await self.save_config()
        logger.info("mcp_server_removed", server_id=server_id)

    async def shutdown(self) -> None:
        """Shutdown all active servers."""
        for server_id, server in self._active_servers.items():
            try:
                await server.__aexit__(None, None, None)
            except Exception as e:
                logger.error(
                    "server_shutdown_error",
                    server_id=server_id,
                    error=str(e),
                )
        self._active_servers.clear()
        logger.info("all_mcp_servers_shutdown")
