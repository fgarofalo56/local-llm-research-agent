"""
WebSocket Connection Wrapper
Phase 2.5: WebSocket Connection Management Refactor

Wraps WebSocket with connection tracking and error handling.
"""

from datetime import UTC, datetime
from typing import Any

import structlog
from fastapi import WebSocket

logger = structlog.get_logger()


class WebSocketConnection:
    """Wrapper for WebSocket with connection tracking and heartbeat."""

    def __init__(
        self,
        websocket: WebSocket,
        connection_id: str,
        conversation_id: int | None = None,
    ):
        """
        Initialize WebSocket connection wrapper.

        Args:
            websocket: The FastAPI WebSocket instance
            connection_id: Unique identifier for this connection
            conversation_id: Optional conversation ID for agent chat
        """
        self.websocket = websocket
        self.connection_id = connection_id
        self.conversation_id = conversation_id
        self.connected_at = datetime.now(UTC)
        self.last_activity = datetime.now(UTC)
        self._closed = False

    async def send_json(self, data: dict[str, Any]) -> bool:
        """
        Send JSON message to client with error handling.

        Args:
            data: Dictionary to send as JSON

        Returns:
            True if sent successfully, False if failed
        """
        if self._closed:
            logger.warning(
                "websocket_send_to_closed",
                connection_id=self.connection_id,
            )
            return False

        try:
            await self.websocket.send_json(data)
            self.last_activity = datetime.now(UTC)
            return True
        except Exception as e:
            logger.warning(
                "websocket_send_error",
                connection_id=self.connection_id,
                error=str(e),
            )
            self._closed = True
            return False

    async def send_text(self, text: str) -> bool:
        """
        Send text message to client with error handling.

        Args:
            text: Text message to send

        Returns:
            True if sent successfully, False if failed
        """
        if self._closed:
            logger.warning(
                "websocket_send_to_closed",
                connection_id=self.connection_id,
            )
            return False

        try:
            await self.websocket.send_text(text)
            self.last_activity = datetime.now(UTC)
            return True
        except Exception as e:
            logger.warning(
                "websocket_send_error",
                connection_id=self.connection_id,
                error=str(e),
            )
            self._closed = True
            return False

    async def receive_json(self) -> dict[str, Any] | None:
        """
        Receive JSON message from client.

        Returns:
            JSON data or None if connection closed
        """
        if self._closed:
            return None

        try:
            data = await self.websocket.receive_json()
            self.last_activity = datetime.now(UTC)
            return data
        except Exception as e:
            logger.debug(
                "websocket_receive_error",
                connection_id=self.connection_id,
                error=str(e),
            )
            self._closed = True
            return None

    async def receive_text(self) -> str | None:
        """
        Receive text message from client.

        Returns:
            Text message or None if connection closed
        """
        if self._closed:
            return None

        try:
            text = await self.websocket.receive_text()
            self.last_activity = datetime.now(UTC)
            return text
        except Exception as e:
            logger.debug(
                "websocket_receive_error",
                connection_id=self.connection_id,
                error=str(e),
            )
            self._closed = True
            return None

    async def close(self, code: int = 1000) -> None:
        """
        Close the WebSocket connection.

        Args:
            code: WebSocket close code (default: 1000 - normal closure)
        """
        if self._closed:
            return

        try:
            await self.websocket.close(code)
        except Exception as e:
            logger.debug(
                "websocket_close_error",
                connection_id=self.connection_id,
                error=str(e),
            )
        finally:
            self._closed = True

    @property
    def is_closed(self) -> bool:
        """Check if connection is closed."""
        return self._closed

    @property
    def idle_seconds(self) -> float:
        """Get seconds since last activity."""
        delta = datetime.now(UTC) - self.last_activity
        return delta.total_seconds()

    def __repr__(self) -> str:
        """String representation of connection."""
        return (
            f"WebSocketConnection(id={self.connection_id}, "
            f"conversation={self.conversation_id}, "
            f"closed={self._closed})"
        )
