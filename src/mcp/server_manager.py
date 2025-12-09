"""
MCP Server Lifecycle Manager

Handles starting, stopping, and monitoring MCP server connections.
Provides context managers for proper resource cleanup.
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from pydantic_ai.mcp import MCPServerStdio

from src.mcp.client import MCPClientManager
from src.utils.logger import get_logger

logger = get_logger(__name__)


class MCPServerError(Exception):
    """Base exception for MCP server errors."""

    pass


class MCPConnectionError(MCPServerError):
    """Error connecting to MCP server."""

    pass


class MCPTimeoutError(MCPServerError):
    """MCP server operation timed out."""

    pass


class MCPServerManager:
    """
    Manages the lifecycle of MCP server connections.

    Provides methods for:
    - Starting and stopping servers
    - Health checks
    - Connection validation
    """

    def __init__(self, client_manager: MCPClientManager | None = None):
        """
        Initialize the server manager.

        Args:
            client_manager: Optional MCPClientManager instance
        """
        self.client_manager = client_manager or MCPClientManager()
        self._active_servers: dict[str, MCPServerStdio] = {}

    async def start_mssql_server(self) -> MCPServerStdio:
        """
        Start the MSSQL MCP server.

        Returns:
            Started MCPServerStdio instance

        Raises:
            MCPConnectionError: If server fails to start
        """
        try:
            server = self.client_manager.get_mssql_server()
            self._active_servers["mssql"] = server

            logger.info("mssql_server_starting")

            # The server will actually start when entering the async context
            # We return it here for use with context managers

            return server

        except ValueError as e:
            logger.error("mssql_server_config_error", error=str(e))
            raise MCPConnectionError(f"Failed to configure MSSQL server: {e}") from e

    async def stop_server(self, name: str) -> None:
        """
        Stop an active server.

        Args:
            name: Name of the server to stop
        """
        if name in self._active_servers:
            logger.info("stopping_mcp_server", name=name)
            del self._active_servers[name]

    async def stop_all(self) -> None:
        """Stop all active servers."""
        server_names = list(self._active_servers.keys())
        for name in server_names:
            await self.stop_server(name)
        logger.info("all_servers_stopped", count=len(server_names))

    @asynccontextmanager
    async def mssql_server_context(self) -> AsyncIterator[MCPServerStdio]:
        """
        Context manager for MSSQL MCP server.

        Usage:
            async with server_manager.mssql_server_context() as server:
                tools = await server.list_tools()

        Yields:
            Connected MCPServerStdio instance
        """
        server = await self.start_mssql_server()

        try:
            async with server:
                logger.info("mssql_server_connected")
                yield server
        except TimeoutError as e:
            logger.error("mssql_server_timeout")
            raise MCPTimeoutError("MSSQL server connection timed out") from e
        except Exception as e:
            logger.error("mssql_server_error", error=str(e))
            raise MCPConnectionError(f"MSSQL server error: {e}") from e
        finally:
            await self.stop_server("mssql")

    async def validate_mssql_connection(self) -> bool:
        """
        Validate that MSSQL MCP server can connect and list tools.

        Returns:
            True if connection is valid

        Raises:
            MCPConnectionError: If validation fails
        """
        try:
            async with self.mssql_server_context() as server:
                tools = await server.list_tools()
                tool_count = len(tools)
                logger.info("mssql_connection_validated", tool_count=tool_count)
                return tool_count > 0
        except Exception as e:
            logger.error("mssql_validation_failed", error=str(e))
            raise MCPConnectionError(f"MSSQL validation failed: {e}") from e

    async def list_mssql_tools(self) -> list[str]:
        """
        List available tools from MSSQL MCP server.

        Returns:
            List of tool names
        """
        async with self.mssql_server_context() as server:
            tools = await server.list_tools()
            return [tool.name for tool in tools]


# Convenience function for quick server access
@asynccontextmanager
async def get_mssql_server() -> AsyncIterator[MCPServerStdio]:
    """
    Quick context manager to get a connected MSSQL server.

    Usage:
        async with get_mssql_server() as server:
            tools = await server.list_tools()

    Yields:
        Connected MCPServerStdio instance
    """
    manager = MCPServerManager()
    async with manager.mssql_server_context() as server:
        yield server
