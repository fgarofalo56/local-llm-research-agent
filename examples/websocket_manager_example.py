"""
WebSocket Manager Usage Example
Phase 2.5: WebSocket Connection Management Refactor

Demonstrates how to use the WebSocketManager for managing WebSocket connections.
"""

import asyncio
import sys

from fastapi import FastAPI, WebSocket
from fastapi.testclient import TestClient

from src.api.websocket import WebSocketManager

# Ensure UTF-8 output on Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

# Example 1: Basic WebSocket Manager Usage
async def basic_usage():
    """Basic WebSocketManager usage example."""
    print("Example 1: Basic WebSocket Manager Usage")
    print("-" * 50)

    # Create manager
    manager = WebSocketManager()

    # In a real application, you would accept WebSocket connections
    # from FastAPI endpoints and pass them to the manager
    print("✓ WebSocketManager created")
    print(f"  Active connections: {manager.get_connection_count()}")

    # Start heartbeat (recommended for production)
    await manager.start_heartbeat()
    print("✓ Heartbeat started")

    # Clean up
    await manager.stop_heartbeat()
    await manager.shutdown()
    print("✓ Manager shutdown complete\n")


# Example 2: Connection Management
async def connection_management():
    """Demonstrates connection lifecycle management."""
    print("Example 2: Connection Management")
    print("-" * 50)

    from unittest.mock import AsyncMock, MagicMock

    manager = WebSocketManager()

    # Mock WebSocket (in real app, this comes from FastAPI)
    mock_ws = MagicMock()
    mock_ws.accept = AsyncMock()
    mock_ws.send_json = AsyncMock()
    mock_ws.close = AsyncMock()

    # Connect
    connection = await manager.connect(mock_ws, "user-123", conversation_id=1)
    print(f"✓ Connected: {connection.connection_id}")
    print(f"  Total connections: {manager.get_connection_count()}")

    # Send message
    await manager.send_to_connection("user-123", {"type": "welcome", "message": "Hello!"})
    print("✓ Message sent to connection")

    # Disconnect
    await manager.disconnect("user-123")
    print(f"✓ Disconnected: user-123")
    print(f"  Remaining connections: {manager.get_connection_count()}\n")


# Example 3: Broadcasting
async def broadcasting_example():
    """Demonstrates broadcasting messages to multiple connections."""
    print("Example 3: Broadcasting")
    print("-" * 50)

    from unittest.mock import AsyncMock, MagicMock

    manager = WebSocketManager()

    # Connect multiple clients
    clients = []
    for i in range(3):
        mock_ws = MagicMock()
        mock_ws.accept = AsyncMock()
        mock_ws.send_json = AsyncMock()
        mock_ws.close = AsyncMock()
        await manager.connect(mock_ws, f"user-{i}")
        clients.append(mock_ws)

    print(f"✓ Connected {len(clients)} clients")

    # Broadcast to all
    sent = await manager.broadcast({"type": "announcement", "text": "Server maintenance in 5 min"})
    print(f"✓ Broadcast sent to {sent} connections")

    # Broadcast with exclusion
    sent = await manager.broadcast(
        {"type": "notification", "text": "Update available"},
        exclude_connections={"user-0"},
    )
    print(f"✓ Broadcast sent to {sent} connections (excluding user-0)")

    # Clean up
    for i in range(3):
        await manager.disconnect(f"user-{i}")
    print(f"✓ Cleaned up all connections\n")


# Example 4: Conversation-based Messaging
async def conversation_messaging():
    """Demonstrates sending messages to specific conversations."""
    print("Example 4: Conversation-based Messaging")
    print("-" * 50)

    from unittest.mock import AsyncMock, MagicMock

    manager = WebSocketManager()

    # Connect clients to different conversations
    for conv_id in [1, 2]:
        for client_idx in range(2):
            mock_ws = MagicMock()
            mock_ws.accept = AsyncMock()
            mock_ws.send_json = AsyncMock()
            mock_ws.close = AsyncMock()
            await manager.connect(
                mock_ws,
                f"conv{conv_id}-client{client_idx}",
                conversation_id=conv_id,
            )

    print(f"✓ Connected 4 clients across 2 conversations")
    print(f"  Active conversations: {manager.get_conversation_count()}")

    # Send to specific conversation
    sent = await manager.send_to_conversation(
        1,
        {"type": "message", "content": "Message for conversation 1"},
    )
    print(f"✓ Sent message to conversation 1 ({sent} clients)")

    # Get connections in conversation
    conv1_connections = manager.get_conversation_connections(1)
    print(f"  Conversation 1 has {len(conv1_connections)} connections")

    # Clean up
    await manager.shutdown()
    print(f"✓ Shutdown complete\n")


# Example 5: FastAPI Integration (skeleton)
def fastapi_integration_example():
    """Shows how to integrate with FastAPI endpoints."""
    print("Example 5: FastAPI Integration")
    print("-" * 50)

    app = FastAPI()

    # Import the global manager instance
    from src.api.websocket import websocket_manager

    @app.websocket("/ws/chat/{conversation_id}")
    async def chat_endpoint(websocket: WebSocket, conversation_id: int):
        """WebSocket endpoint using the manager."""
        # Generate unique connection ID
        connection_id = f"chat-{conversation_id}-{id(websocket)}"

        # Connect via manager
        connection = await websocket_manager.connect(
            websocket, connection_id, conversation_id
        )

        try:
            while True:
                # Receive message
                data = await connection.receive_json()
                if data is None:
                    break

                # Process message...
                response = {"type": "response", "content": "Echo: " + data.get("content", "")}

                # Send response
                await connection.send_json(response)

        except Exception as e:
            print(f"Error: {e}")
        finally:
            # Clean up
            await websocket_manager.disconnect(connection_id)

    print("✓ FastAPI endpoint example defined")
    print("  Route: /ws/chat/{conversation_id}")
    print("  Manager handles connection lifecycle")
    print("  Heartbeat runs in background\n")


# Example 6: Health Metrics
async def health_metrics():
    """Demonstrates getting health metrics from the manager."""
    print("Example 6: Health Metrics")
    print("-" * 50)

    from unittest.mock import AsyncMock, MagicMock

    manager = WebSocketManager()

    # Connect some clients
    for i in range(5):
        mock_ws = MagicMock()
        mock_ws.accept = AsyncMock()
        mock_ws.send_json = AsyncMock()
        mock_ws.close = AsyncMock()
        conv_id = i % 2 + 1  # Split across 2 conversations
        await manager.connect(mock_ws, f"client-{i}", conversation_id=conv_id)

    # Get metrics
    print("WebSocket Metrics:")
    print(f"  Total connections: {manager.get_connection_count()}")
    print(f"  Active conversations: {manager.get_conversation_count()}")

    all_connections = manager.get_all_connections()
    print(f"  Connections list: {len(all_connections)} items")

    for conn in all_connections[:2]:  # Show first 2
        print(f"    - {conn.connection_id} (idle: {conn.idle_seconds:.2f}s)")

    # Clean up
    await manager.shutdown()
    print(f"✓ Shutdown complete\n")


async def main():
    """Run all examples."""
    print("\n" + "=" * 60)
    print("WebSocket Manager Examples")
    print("=" * 60 + "\n")

    await basic_usage()
    await connection_management()
    await broadcasting_example()
    await conversation_messaging()
    fastapi_integration_example()
    await health_metrics()

    print("=" * 60)
    print("All examples completed!")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
