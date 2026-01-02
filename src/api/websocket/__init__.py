"""
WebSocket Connection Management
Phase 2.5: WebSocket Connection Management Refactor

Provides centralized WebSocket connection management with:
- Connection pooling
- Heartbeat/keepalive
- Broadcasting capabilities
- Conversation-based message routing
"""

from src.api.websocket.connection import WebSocketConnection
from src.api.websocket.heartbeat import HeartbeatManager
from src.api.websocket.manager import WebSocketManager, websocket_manager

__all__ = [
    "WebSocketConnection",
    "WebSocketManager",
    "HeartbeatManager",
    "websocket_manager",
]
