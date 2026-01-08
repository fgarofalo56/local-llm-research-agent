"""
WebSocket Connection Manager
Phase 2.5: WebSocket Connection Management Refactor

Manages WebSocket connections with pooling, broadcasting, and heartbeat.
"""

from typing import Any

import structlog
from fastapi import WebSocket

from src.api.websocket.connection import WebSocketConnection
from src.api.websocket.heartbeat import HeartbeatManager

logger = structlog.get_logger()


class WebSocketManager:
    """Manages WebSocket connections with pooling and broadcasting."""

    def __init__(self):
        """Initialize WebSocket manager."""
        # All active connections by connection ID
        self._connections: dict[str, WebSocketConnection] = {}

        # Connections grouped by conversation ID for targeted messaging
        self._conversation_connections: dict[int, list[str]] = {}

        # Heartbeat manager
        self._heartbeat: HeartbeatManager | None = None

    async def connect(
        self,
        websocket: WebSocket,
        connection_id: str,
        conversation_id: int | None = None,
    ) -> WebSocketConnection:
        """
        Register a new WebSocket connection.

        Args:
            websocket: FastAPI WebSocket instance
            connection_id: Unique identifier for this connection
            conversation_id: Optional conversation ID for agent chat

        Returns:
            WebSocketConnection wrapper
        """
        # Accept the WebSocket connection
        await websocket.accept()

        # Create connection wrapper
        connection = WebSocketConnection(
            websocket=websocket,
            connection_id=connection_id,
            conversation_id=conversation_id,
        )

        # Store connection
        self._connections[connection_id] = connection

        # Add to conversation group if applicable
        if conversation_id is not None:
            if conversation_id not in self._conversation_connections:
                self._conversation_connections[conversation_id] = []
            self._conversation_connections[conversation_id].append(connection_id)

        logger.info(
            "websocket_connected",
            connection_id=connection_id,
            conversation_id=conversation_id,
            total_connections=len(self._connections),
        )

        return connection

    async def disconnect(self, connection_id: str) -> None:
        """
        Disconnect and remove a WebSocket connection.

        Args:
            connection_id: Connection ID to disconnect
        """
        connection = self._connections.get(connection_id)
        if not connection:
            logger.warning(
                "websocket_disconnect_not_found",
                connection_id=connection_id,
            )
            return

        # Close the WebSocket
        await connection.close()

        # Remove from conversation group
        if connection.conversation_id is not None:
            conversation_id = connection.conversation_id
            if conversation_id in self._conversation_connections:
                self._conversation_connections[conversation_id] = [
                    cid
                    for cid in self._conversation_connections[conversation_id]
                    if cid != connection_id
                ]
                # Clean up empty conversation groups
                if not self._conversation_connections[conversation_id]:
                    del self._conversation_connections[conversation_id]

        # Remove from connections pool
        del self._connections[connection_id]

        logger.info(
            "websocket_disconnected",
            connection_id=connection_id,
            conversation_id=connection.conversation_id,
            total_connections=len(self._connections),
        )

    async def send_to_connection(
        self,
        connection_id: str,
        message: dict[str, Any],
    ) -> bool:
        """
        Send message to a specific connection.

        Args:
            connection_id: Target connection ID
            message: Message data to send

        Returns:
            True if sent successfully, False otherwise
        """
        connection = self._connections.get(connection_id)
        if not connection:
            logger.warning(
                "websocket_send_connection_not_found",
                connection_id=connection_id,
            )
            return False

        success = await connection.send_json(message)
        if not success:
            # Connection failed, clean it up
            await self.disconnect(connection_id)

        return success

    async def send_to_conversation(
        self,
        conversation_id: int,
        message: dict[str, Any],
    ) -> int:
        """
        Send message to all connections in a conversation.

        Args:
            conversation_id: Target conversation ID
            message: Message data to send

        Returns:
            Number of connections that received the message
        """
        connection_ids = self._conversation_connections.get(conversation_id, [])

        if not connection_ids:
            logger.debug(
                "websocket_send_conversation_no_connections",
                conversation_id=conversation_id,
            )
            return 0

        sent_count = 0
        failed_connections = []

        for connection_id in connection_ids:
            connection = self._connections.get(connection_id)
            if not connection:
                continue

            success = await connection.send_json(message)
            if success:
                sent_count += 1
            else:
                failed_connections.append(connection_id)

        # Clean up failed connections
        for connection_id in failed_connections:
            await self.disconnect(connection_id)

        logger.debug(
            "websocket_sent_to_conversation",
            conversation_id=conversation_id,
            sent_count=sent_count,
            failed_count=len(failed_connections),
        )

        return sent_count

    async def broadcast(
        self,
        message: dict[str, Any],
        exclude_connections: set[str] | None = None,
    ) -> int:
        """
        Broadcast message to all connections.

        Args:
            message: Message data to send
            exclude_connections: Set of connection IDs to exclude

        Returns:
            Number of connections that received the message
        """
        exclude = exclude_connections or set()
        sent_count = 0
        failed_connections = []

        for connection_id, connection in self._connections.items():
            if connection_id in exclude:
                continue

            success = await connection.send_json(message)
            if success:
                sent_count += 1
            else:
                failed_connections.append(connection_id)

        # Clean up failed connections
        for connection_id in failed_connections:
            await self.disconnect(connection_id)

        logger.debug(
            "websocket_broadcast",
            sent_count=sent_count,
            failed_count=len(failed_connections),
            excluded_count=len(exclude),
        )

        return sent_count

    def get_connection(self, connection_id: str) -> WebSocketConnection | None:
        """
        Get connection by ID.

        Args:
            connection_id: Connection ID to retrieve

        Returns:
            WebSocketConnection or None if not found
        """
        return self._connections.get(connection_id)

    def get_conversation_connections(self, conversation_id: int) -> list[WebSocketConnection]:
        """
        Get all connections for a conversation.

        Args:
            conversation_id: Conversation ID

        Returns:
            List of WebSocketConnection instances
        """
        connection_ids = self._conversation_connections.get(conversation_id, [])
        return [self._connections[cid] for cid in connection_ids if cid in self._connections]

    def get_all_connections(self) -> list[WebSocketConnection]:
        """
        Get all active connections.

        Returns:
            List of all WebSocketConnection instances
        """
        return list(self._connections.values())

    def get_connection_count(self) -> int:
        """
        Get total number of active connections.

        Returns:
            Number of active connections
        """
        return len(self._connections)

    def get_conversation_count(self) -> int:
        """
        Get number of active conversations.

        Returns:
            Number of conversations with active connections
        """
        return len(self._conversation_connections)

    async def start_heartbeat(self) -> None:
        """Start the heartbeat background task."""
        if self._heartbeat is None:
            self._heartbeat = HeartbeatManager(self)
        await self._heartbeat.start()

    async def stop_heartbeat(self) -> None:
        """Stop the heartbeat background task."""
        if self._heartbeat:
            await self._heartbeat.stop()

    async def shutdown(self) -> None:
        """Shutdown manager and close all connections."""
        logger.info(
            "websocket_manager_shutdown",
            connection_count=len(self._connections),
        )

        # Stop heartbeat
        await self.stop_heartbeat()

        # Close all connections
        connection_ids = list(self._connections.keys())
        for connection_id in connection_ids:
            await self.disconnect(connection_id)

        logger.info("websocket_manager_shutdown_complete")


# Global WebSocket manager instance
websocket_manager = WebSocketManager()
