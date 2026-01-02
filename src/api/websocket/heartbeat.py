"""
WebSocket Heartbeat Mechanism
Phase 2.5: WebSocket Connection Management Refactor

Provides ping/pong heartbeat and stale connection cleanup.
"""

import asyncio
from typing import TYPE_CHECKING

import structlog

if TYPE_CHECKING:
    from src.api.websocket.manager import WebSocketManager

logger = structlog.get_logger()

# Heartbeat configuration
HEARTBEAT_INTERVAL = 30  # Send ping every 30 seconds
STALE_CONNECTION_TIMEOUT = 90  # Disconnect if no activity for 90 seconds


class HeartbeatManager:
    """Manages WebSocket heartbeat and stale connection cleanup."""

    def __init__(self, manager: "WebSocketManager"):
        """
        Initialize heartbeat manager.

        Args:
            manager: WebSocketManager instance to monitor
        """
        self.manager = manager
        self._task: asyncio.Task | None = None
        self._running = False

    async def start(self) -> None:
        """Start the heartbeat background task."""
        if self._running:
            logger.warning("heartbeat_already_running")
            return

        self._running = True
        self._task = asyncio.create_task(self._heartbeat_loop())
        logger.info("heartbeat_started")

    async def stop(self) -> None:
        """Stop the heartbeat background task."""
        if not self._running:
            return

        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None

        logger.info("heartbeat_stopped")

    async def _heartbeat_loop(self) -> None:
        """Background task that sends pings and cleans up stale connections."""
        logger.debug("heartbeat_loop_started")

        while self._running:
            try:
                # Send ping to all connections
                await self._send_pings()

                # Clean up stale connections
                await self._cleanup_stale_connections()

                # Wait for next interval
                await asyncio.sleep(HEARTBEAT_INTERVAL)

            except asyncio.CancelledError:
                logger.debug("heartbeat_loop_cancelled")
                break
            except Exception as e:
                logger.error(
                    "heartbeat_loop_error",
                    error=str(e),
                )
                # Continue running even if there's an error
                await asyncio.sleep(HEARTBEAT_INTERVAL)

    async def _send_pings(self) -> None:
        """Send ping message to all active connections."""
        connections = self.manager.get_all_connections()

        if not connections:
            return

        logger.debug("heartbeat_sending_pings", connection_count=len(connections))

        for connection in connections:
            try:
                success = await connection.send_json({"type": "ping"})
                if not success:
                    logger.debug(
                        "heartbeat_ping_failed",
                        connection_id=connection.connection_id,
                    )
            except Exception as e:
                logger.warning(
                    "heartbeat_ping_error",
                    connection_id=connection.connection_id,
                    error=str(e),
                )

    async def _cleanup_stale_connections(self) -> None:
        """Close connections that haven't been active recently."""
        connections = self.manager.get_all_connections()

        if not connections:
            return

        stale_connections = [
            conn for conn in connections if conn.idle_seconds > STALE_CONNECTION_TIMEOUT
        ]

        if stale_connections:
            logger.info(
                "heartbeat_cleaning_stale_connections",
                count=len(stale_connections),
            )

            for connection in stale_connections:
                try:
                    logger.debug(
                        "heartbeat_closing_stale_connection",
                        connection_id=connection.connection_id,
                        idle_seconds=connection.idle_seconds,
                    )
                    await self.manager.disconnect(connection.connection_id)
                except Exception as e:
                    logger.error(
                        "heartbeat_cleanup_error",
                        connection_id=connection.connection_id,
                        error=str(e),
                    )
