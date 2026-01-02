"""
Tests for WebSocket Connection Management
Phase 2.5: WebSocket Connection Management Refactor

Tests for WebSocketManager, WebSocketConnection, and HeartbeatManager.
"""

import asyncio
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.api.websocket import WebSocketConnection, WebSocketManager
from src.api.websocket.heartbeat import HeartbeatManager


@pytest.fixture
def mock_websocket():
    """Create mock WebSocket."""
    ws = MagicMock()
    ws.accept = AsyncMock()
    ws.send_json = AsyncMock()
    ws.send_text = AsyncMock()
    ws.receive_json = AsyncMock()
    ws.receive_text = AsyncMock()
    ws.close = AsyncMock()
    return ws


@pytest.fixture
def websocket_manager():
    """Create WebSocketManager instance."""
    return WebSocketManager()


class TestWebSocketConnection:
    """Tests for WebSocketConnection class."""

    @pytest.mark.asyncio
    async def test_send_json_success(self, mock_websocket):
        """Test successful JSON send."""
        connection = WebSocketConnection(mock_websocket, "test-1")
        data = {"type": "test", "message": "hello"}

        result = await connection.send_json(data)

        assert result is True
        mock_websocket.send_json.assert_called_once_with(data)

    @pytest.mark.asyncio
    async def test_send_json_failure(self, mock_websocket):
        """Test JSON send failure handling."""
        mock_websocket.send_json.side_effect = Exception("Connection lost")
        connection = WebSocketConnection(mock_websocket, "test-1")

        result = await connection.send_json({"type": "test"})

        assert result is False
        assert connection.is_closed is True

    @pytest.mark.asyncio
    async def test_send_text_success(self, mock_websocket):
        """Test successful text send."""
        connection = WebSocketConnection(mock_websocket, "test-1")

        result = await connection.send_text("pong")

        assert result is True
        mock_websocket.send_text.assert_called_once_with("pong")

    @pytest.mark.asyncio
    async def test_receive_json_success(self, mock_websocket):
        """Test successful JSON receive."""
        mock_websocket.receive_json.return_value = {"type": "message"}
        connection = WebSocketConnection(mock_websocket, "test-1")

        data = await connection.receive_json()

        assert data == {"type": "message"}

    @pytest.mark.asyncio
    async def test_receive_json_failure(self, mock_websocket):
        """Test JSON receive failure."""
        mock_websocket.receive_json.side_effect = Exception("Connection lost")
        connection = WebSocketConnection(mock_websocket, "test-1")

        data = await connection.receive_json()

        assert data is None
        assert connection.is_closed is True

    @pytest.mark.asyncio
    async def test_close(self, mock_websocket):
        """Test connection close."""
        connection = WebSocketConnection(mock_websocket, "test-1")

        await connection.close()

        assert connection.is_closed is True
        mock_websocket.close.assert_called_once_with(1000)

    @pytest.mark.asyncio
    async def test_idle_seconds(self, mock_websocket):
        """Test idle time calculation."""
        connection = WebSocketConnection(mock_websocket, "test-1")

        # Set last activity to 5 seconds ago
        connection.last_activity = datetime.now(timezone.utc) - timedelta(seconds=5)

        idle = connection.idle_seconds
        assert idle >= 5
        assert idle < 6  # Allow small margin

    def test_connection_tracking(self, mock_websocket):
        """Test connection ID and conversation tracking."""
        connection = WebSocketConnection(
            mock_websocket, "test-1", conversation_id=42
        )

        assert connection.connection_id == "test-1"
        assert connection.conversation_id == 42
        assert connection.is_closed is False


class TestWebSocketManager:
    """Tests for WebSocketManager class."""

    @pytest.mark.asyncio
    async def test_connect(self, websocket_manager, mock_websocket):
        """Test connecting a WebSocket."""
        connection = await websocket_manager.connect(
            mock_websocket, "conn-1", conversation_id=1
        )

        assert connection.connection_id == "conn-1"
        assert connection.conversation_id == 1
        assert websocket_manager.get_connection_count() == 1
        mock_websocket.accept.assert_called_once()

    @pytest.mark.asyncio
    async def test_disconnect(self, websocket_manager, mock_websocket):
        """Test disconnecting a WebSocket."""
        connection = await websocket_manager.connect(mock_websocket, "conn-1")

        await websocket_manager.disconnect("conn-1")

        assert websocket_manager.get_connection_count() == 0
        mock_websocket.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_disconnect_nonexistent(self, websocket_manager):
        """Test disconnecting nonexistent connection."""
        # Should not raise exception
        await websocket_manager.disconnect("nonexistent")

    @pytest.mark.asyncio
    async def test_send_to_connection(self, websocket_manager, mock_websocket):
        """Test sending to specific connection."""
        await websocket_manager.connect(mock_websocket, "conn-1")

        result = await websocket_manager.send_to_connection(
            "conn-1", {"type": "test"}
        )

        assert result is True
        mock_websocket.send_json.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_to_nonexistent_connection(self, websocket_manager):
        """Test sending to nonexistent connection."""
        result = await websocket_manager.send_to_connection(
            "nonexistent", {"type": "test"}
        )

        assert result is False

    @pytest.mark.asyncio
    async def test_send_to_conversation(self, websocket_manager):
        """Test sending to all connections in conversation."""
        ws1 = MagicMock()
        ws1.accept = AsyncMock()
        ws1.send_json = AsyncMock()
        ws1.close = AsyncMock()

        ws2 = MagicMock()
        ws2.accept = AsyncMock()
        ws2.send_json = AsyncMock()
        ws2.close = AsyncMock()

        # Connect two clients to same conversation
        await websocket_manager.connect(ws1, "conn-1", conversation_id=1)
        await websocket_manager.connect(ws2, "conn-2", conversation_id=1)

        sent_count = await websocket_manager.send_to_conversation(
            1, {"type": "test"}
        )

        assert sent_count == 2
        ws1.send_json.assert_called_once()
        ws2.send_json.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_to_empty_conversation(self, websocket_manager):
        """Test sending to conversation with no connections."""
        sent_count = await websocket_manager.send_to_conversation(
            999, {"type": "test"}
        )

        assert sent_count == 0

    @pytest.mark.asyncio
    async def test_broadcast(self, websocket_manager):
        """Test broadcasting to all connections."""
        ws1 = MagicMock()
        ws1.accept = AsyncMock()
        ws1.send_json = AsyncMock()
        ws1.close = AsyncMock()

        ws2 = MagicMock()
        ws2.accept = AsyncMock()
        ws2.send_json = AsyncMock()
        ws2.close = AsyncMock()

        await websocket_manager.connect(ws1, "conn-1")
        await websocket_manager.connect(ws2, "conn-2")

        sent_count = await websocket_manager.broadcast({"type": "broadcast"})

        assert sent_count == 2
        ws1.send_json.assert_called_once()
        ws2.send_json.assert_called_once()

    @pytest.mark.asyncio
    async def test_broadcast_with_exclusion(self, websocket_manager):
        """Test broadcasting with excluded connections."""
        ws1 = MagicMock()
        ws1.accept = AsyncMock()
        ws1.send_json = AsyncMock()
        ws1.close = AsyncMock()

        ws2 = MagicMock()
        ws2.accept = AsyncMock()
        ws2.send_json = AsyncMock()
        ws2.close = AsyncMock()

        await websocket_manager.connect(ws1, "conn-1")
        await websocket_manager.connect(ws2, "conn-2")

        sent_count = await websocket_manager.broadcast(
            {"type": "broadcast"}, exclude_connections={"conn-1"}
        )

        assert sent_count == 1
        ws1.send_json.assert_not_called()
        ws2.send_json.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_connection(self, websocket_manager, mock_websocket):
        """Test retrieving specific connection."""
        await websocket_manager.connect(mock_websocket, "conn-1")

        connection = websocket_manager.get_connection("conn-1")

        assert connection is not None
        assert connection.connection_id == "conn-1"

    @pytest.mark.asyncio
    async def test_get_conversation_connections(self, websocket_manager):
        """Test getting all connections in conversation."""
        ws1 = MagicMock()
        ws1.accept = AsyncMock()
        ws1.close = AsyncMock()

        ws2 = MagicMock()
        ws2.accept = AsyncMock()
        ws2.close = AsyncMock()

        await websocket_manager.connect(ws1, "conn-1", conversation_id=1)
        await websocket_manager.connect(ws2, "conn-2", conversation_id=1)

        connections = websocket_manager.get_conversation_connections(1)

        assert len(connections) == 2
        assert connections[0].conversation_id == 1
        assert connections[1].conversation_id == 1

    @pytest.mark.asyncio
    async def test_get_all_connections(self, websocket_manager):
        """Test getting all active connections."""
        ws1 = MagicMock()
        ws1.accept = AsyncMock()
        ws1.close = AsyncMock()

        ws2 = MagicMock()
        ws2.accept = AsyncMock()
        ws2.close = AsyncMock()

        await websocket_manager.connect(ws1, "conn-1")
        await websocket_manager.connect(ws2, "conn-2")

        connections = websocket_manager.get_all_connections()

        assert len(connections) == 2

    @pytest.mark.asyncio
    async def test_connection_count(self, websocket_manager, mock_websocket):
        """Test connection count tracking."""
        assert websocket_manager.get_connection_count() == 0

        await websocket_manager.connect(mock_websocket, "conn-1")
        assert websocket_manager.get_connection_count() == 1

        await websocket_manager.disconnect("conn-1")
        assert websocket_manager.get_connection_count() == 0

    @pytest.mark.asyncio
    async def test_conversation_count(self, websocket_manager):
        """Test conversation count tracking."""
        ws1 = MagicMock()
        ws1.accept = AsyncMock()
        ws1.close = AsyncMock()

        ws2 = MagicMock()
        ws2.accept = AsyncMock()
        ws2.close = AsyncMock()

        assert websocket_manager.get_conversation_count() == 0

        await websocket_manager.connect(ws1, "conn-1", conversation_id=1)
        assert websocket_manager.get_conversation_count() == 1

        await websocket_manager.connect(ws2, "conn-2", conversation_id=2)
        assert websocket_manager.get_conversation_count() == 2

        # Adding to existing conversation doesn't increase count
        ws3 = MagicMock()
        ws3.accept = AsyncMock()
        ws3.close = AsyncMock()
        await websocket_manager.connect(ws3, "conn-3", conversation_id=1)
        assert websocket_manager.get_conversation_count() == 2

    @pytest.mark.asyncio
    async def test_shutdown(self, websocket_manager):
        """Test manager shutdown."""
        ws1 = MagicMock()
        ws1.accept = AsyncMock()
        ws1.close = AsyncMock()
        ws1.send_json = AsyncMock()

        ws2 = MagicMock()
        ws2.accept = AsyncMock()
        ws2.close = AsyncMock()
        ws2.send_json = AsyncMock()

        await websocket_manager.connect(ws1, "conn-1")
        await websocket_manager.connect(ws2, "conn-2")

        await websocket_manager.shutdown()

        assert websocket_manager.get_connection_count() == 0
        ws1.close.assert_called_once()
        ws2.close.assert_called_once()


class TestHeartbeatManager:
    """Tests for HeartbeatManager class."""

    @pytest.mark.asyncio
    async def test_start_stop(self, websocket_manager):
        """Test starting and stopping heartbeat."""
        heartbeat = HeartbeatManager(websocket_manager)

        await heartbeat.start()
        assert heartbeat._running is True

        await heartbeat.stop()
        assert heartbeat._running is False

    @pytest.mark.asyncio
    async def test_send_pings(self, websocket_manager):
        """Test sending ping messages."""
        ws = MagicMock()
        ws.accept = AsyncMock()
        ws.send_json = AsyncMock()
        ws.close = AsyncMock()

        await websocket_manager.connect(ws, "conn-1")

        heartbeat = HeartbeatManager(websocket_manager)
        await heartbeat._send_pings()

        # Should send ping message
        ws.send_json.assert_called_once()
        call_args = ws.send_json.call_args[0][0]
        assert call_args["type"] == "ping"

    @pytest.mark.asyncio
    async def test_cleanup_stale_connections(self, websocket_manager):
        """Test cleaning up stale connections."""
        ws = MagicMock()
        ws.accept = AsyncMock()
        ws.send_json = AsyncMock()
        ws.close = AsyncMock()

        connection = await websocket_manager.connect(ws, "conn-1")

        # Make connection stale
        connection.last_activity = datetime.now(timezone.utc) - timedelta(seconds=100)

        heartbeat = HeartbeatManager(websocket_manager)
        await heartbeat._cleanup_stale_connections()

        # Connection should be removed
        assert websocket_manager.get_connection_count() == 0
        ws.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_cleanup_active_connections(self, websocket_manager):
        """Test that active connections are not cleaned up."""
        ws = MagicMock()
        ws.accept = AsyncMock()
        ws.send_json = AsyncMock()
        ws.close = AsyncMock()

        await websocket_manager.connect(ws, "conn-1")

        heartbeat = HeartbeatManager(websocket_manager)
        await heartbeat._cleanup_stale_connections()

        # Connection should remain
        assert websocket_manager.get_connection_count() == 1
        ws.close.assert_not_called()

    @pytest.mark.asyncio
    async def test_heartbeat_loop_cancellation(self, websocket_manager):
        """Test heartbeat loop cancellation."""
        heartbeat = HeartbeatManager(websocket_manager)

        await heartbeat.start()
        await asyncio.sleep(0.1)  # Let task start
        await heartbeat.stop()

        # Should complete without error
        assert heartbeat._running is False
        assert heartbeat._task is None
