"""
Notification Service
Phase 2.5: Advanced Features & Polish

Service for sending notifications to connected WebSocket clients.
"""

from typing import Any

import structlog
from fastapi import WebSocket

logger = structlog.get_logger()

# In-memory store for connected WebSocket clients
_connected_clients: dict[str, list[WebSocket]] = {}


class NotificationService:
    """Service for sending notifications to WebSocket clients."""

    @staticmethod
    def register_client(client_id: str, websocket: WebSocket) -> None:
        """Register a WebSocket client for notifications."""
        if client_id not in _connected_clients:
            _connected_clients[client_id] = []
        _connected_clients[client_id].append(websocket)
        logger.debug("notification_client_registered", client_id=client_id)

    @staticmethod
    def unregister_client(client_id: str, websocket: WebSocket) -> None:
        """Unregister a WebSocket client."""
        if client_id in _connected_clients:
            _connected_clients[client_id] = [
                ws for ws in _connected_clients[client_id] if ws != websocket
            ]
            if not _connected_clients[client_id]:
                del _connected_clients[client_id]
            logger.debug("notification_client_unregistered", client_id=client_id)

    @staticmethod
    def get_connected_count() -> int:
        """Get the number of connected clients."""
        return sum(len(clients) for clients in _connected_clients.values())

    async def send_alert(
        self,
        alert_id: int,
        alert_name: str,
        condition: str,
        threshold: float,
        current_value: float,
    ) -> None:
        """Send alert notification to all connected clients."""
        message = {
            "type": "alert",
            "data": {
                "id": alert_id,
                "name": alert_name,
                "condition": condition,
                "threshold": threshold,
                "current_value": current_value,
                "message": self._format_message(alert_name, condition, threshold, current_value),
            },
        }

        await self._broadcast(message)
        logger.info("alert_notification_sent", alert_id=alert_id)

    async def send_notification(
        self,
        notification_type: str,
        title: str,
        message: str,
        data: dict[str, Any] | None = None,
    ) -> None:
        """Send a generic notification to all connected clients."""
        payload = {
            "type": notification_type,
            "data": {
                "title": title,
                "message": message,
                **(data or {}),
            },
        }

        await self._broadcast(payload)
        logger.info("notification_sent", type=notification_type, title=title)

    async def _broadcast(self, message: dict[str, Any]) -> None:
        """Broadcast a message to all connected clients."""
        disconnected: list[tuple[str, WebSocket]] = []

        for client_id, websockets in _connected_clients.items():
            for websocket in websockets:
                try:
                    await websocket.send_json(message)
                except Exception as e:
                    logger.warning(
                        "notification_send_error",
                        client_id=client_id,
                        error=str(e),
                    )
                    disconnected.append((client_id, websocket))

        # Clean up disconnected clients
        for client_id, websocket in disconnected:
            self.unregister_client(client_id, websocket)

    def _format_message(
        self,
        name: str,
        condition: str,
        threshold: float,
        value: float,
    ) -> str:
        """Format alert message for display."""
        condition_text = {
            "greater_than": f"exceeded {threshold}",
            "less_than": f"dropped below {threshold}",
            "equals": f"equals {threshold}",
            "changes": "changed",
        }
        return f"{name}: Value {condition_text.get(condition, condition)} (current: {value})"


# Global notification service instance
notification_service = NotificationService()
