# WebSocket Connection Management Refactor

**Phase 2.5: Advanced Features & Polish**

## Overview

This refactoring extracts WebSocket connection management from inline implementations in `src/api/main.py` into a dedicated, reusable module with comprehensive connection pooling, heartbeat mechanism, and broadcasting capabilities.

## Architecture

### Module Structure

```
src/api/websocket/
├── __init__.py           # Module exports
├── connection.py         # WebSocketConnection wrapper
├── manager.py           # WebSocketManager for pooling
└── heartbeat.py         # HeartbeatManager for keepalive
```

### Components

#### 1. WebSocketConnection (`connection.py`)

**Purpose:** Wraps FastAPI's WebSocket with connection tracking and error handling.

**Features:**
- Automatic activity timestamp tracking
- Graceful error handling for send/receive operations
- Idle time calculation for stale connection detection
- Connection state management (open/closed)

**Key Methods:**
```python
async def send_json(data: dict) -> bool
async def send_text(text: str) -> bool
async def receive_json() -> dict | None
async def receive_text() -> str | None
async def close(code: int = 1000) -> None

@property
def is_closed() -> bool
def idle_seconds() -> float
```

#### 2. WebSocketManager (`manager.py`)

**Purpose:** Centralized connection pool management with broadcasting and routing capabilities.

**Features:**
- Connection pooling by connection ID
- Conversation-based grouping for targeted messaging
- Broadcasting to all connections with exclusion support
- Automatic cleanup on failed sends
- Health metrics and statistics

**Key Methods:**
```python
async def connect(websocket, connection_id, conversation_id=None) -> WebSocketConnection
async def disconnect(connection_id) -> None
async def send_to_connection(connection_id, message) -> bool
async def send_to_conversation(conversation_id, message) -> int
async def broadcast(message, exclude_connections=None) -> int

def get_connection(connection_id) -> WebSocketConnection | None
def get_conversation_connections(conversation_id) -> list[WebSocketConnection]
def get_all_connections() -> list[WebSocketConnection]
def get_connection_count() -> int
def get_conversation_count() -> int

async def start_heartbeat() -> None
async def stop_heartbeat() -> None
async def shutdown() -> None
```

#### 3. HeartbeatManager (`heartbeat.py`)

**Purpose:** Background task for connection health monitoring and cleanup.

**Features:**
- Automatic ping messages every 30 seconds
- Stale connection cleanup (90 seconds idle timeout)
- Graceful error handling
- Configurable intervals

**Configuration:**
```python
HEARTBEAT_INTERVAL = 30  # Send ping every 30 seconds
STALE_CONNECTION_TIMEOUT = 90  # Disconnect if no activity for 90 seconds
```

## Integration

### Application Lifecycle

The WebSocket manager is initialized during application startup and shutdown:

**`src/api/deps.py`:**
```python
async def init_services():
    # ... other services ...

    # Initialize WebSocket manager with heartbeat
    from src.api.websocket import websocket_manager as ws_mgr
    _websocket_manager = ws_mgr
    await _websocket_manager.start_heartbeat()
    logger.info("websocket_manager_initialized")

async def shutdown_services():
    # Stop WebSocket manager first
    if _websocket_manager:
        await _websocket_manager.shutdown()

    # ... other cleanup ...
```

### Endpoint Usage

**Agent WebSocket (`src/api/routes/agent.py`):**
```python
@router.websocket("/ws/{conversation_id}")
async def agent_websocket(websocket: WebSocket, conversation_id: int):
    from src.api.deps import get_websocket_manager_optional

    ws_manager = get_websocket_manager_optional()

    if ws_manager:
        connection_id = f"agent-{conversation_id}-{id(websocket)}"
        connection = await ws_manager.connect(websocket, connection_id, conversation_id)
    else:
        # Fallback to direct WebSocket
        await websocket.accept()
        connection = None

    try:
        while True:
            # Use connection wrapper if available
            if connection:
                data = await connection.receive_json()
                if data is None:
                    break
            else:
                data = await websocket.receive_json()

            # Process message...

            # Send response
            if connection:
                await connection.send_json(response_msg)
            else:
                await websocket.send_json(response_msg)

    finally:
        if ws_manager and connection:
            await ws_manager.disconnect(connection.connection_id)
```

**Alert Notifications (`src/api/main.py`):**
```python
@app.websocket("/ws/alerts")
async def websocket_alerts(websocket: WebSocket):
    from src.api.deps import get_websocket_manager_optional
    from src.services.notification_service import NotificationService

    ws_manager = get_websocket_manager_optional()

    if ws_manager:
        client_id = f"alerts-{id(websocket)}"
        connection = await ws_manager.connect(websocket, client_id)

        NotificationService.register_client(client_id, websocket)

        try:
            while True:
                data = await connection.receive_text()
                if data is None:
                    break
                if data == "ping":
                    await connection.send_text("pong")
        finally:
            NotificationService.unregister_client(client_id, websocket)
            await ws_manager.disconnect(client_id)
    else:
        # Fallback implementation...
```

## Benefits

### 1. Code Reusability
- Single implementation for all WebSocket endpoints
- Consistent error handling and logging
- Shared connection lifecycle management

### 2. Maintainability
- Centralized connection logic
- Easy to add new features (metrics, rate limiting, etc.)
- Clear separation of concerns

### 3. Reliability
- Automatic heartbeat prevents silent disconnections
- Stale connection cleanup prevents resource leaks
- Graceful error handling with automatic cleanup

### 4. Observability
- Connection metrics and statistics
- Structured logging for all connection events
- Easy to monitor active connections and conversations

### 5. Scalability
- Efficient connection pooling
- Conversation-based grouping for targeted messaging
- Broadcasting with exclusion support

## Testing

Comprehensive test suite with 28 tests covering:

**WebSocketConnection Tests:**
- Send/receive JSON and text messages
- Error handling and connection state
- Idle time tracking
- Connection lifecycle

**WebSocketManager Tests:**
- Connection management (connect/disconnect)
- Sending to specific connections
- Conversation-based messaging
- Broadcasting with/without exclusions
- Metrics and statistics
- Shutdown behavior

**HeartbeatManager Tests:**
- Start/stop lifecycle
- Ping message sending
- Stale connection cleanup
- Background task cancellation

**Test Results:**
```
tests/test_websocket.py::TestWebSocketConnection - 8 tests ✓
tests/test_websocket.py::TestWebSocketManager - 15 tests ✓
tests/test_websocket.py::TestHeartbeatManager - 5 tests ✓

Total: 28 tests, all passing
```

## Message Protocol

### Client → Server
```json
{
  "type": "message",
  "content": "user message",
  "mcp_servers": ["mssql"]
}
```

### Server → Client
```json
// Streaming chunk
{"type": "chunk", "content": "partial response"}

// Completion
{"type": "complete", "message": {...}}

// Error
{"type": "error", "error": "error message"}

// Heartbeat (automatic)
{"type": "ping"}
```

## Configuration

### Heartbeat Settings

Located in `src/api/websocket/heartbeat.py`:

```python
HEARTBEAT_INTERVAL = 30  # Ping interval (seconds)
STALE_CONNECTION_TIMEOUT = 90  # Idle timeout (seconds)
```

Adjust these values based on your requirements:
- **Lower intervals:** More responsive but higher network overhead
- **Higher intervals:** Less overhead but slower stale detection

## Examples

See `examples/websocket_manager_example.py` for comprehensive usage examples:

1. Basic WebSocket Manager Usage
2. Connection Management
3. Broadcasting
4. Conversation-based Messaging
5. FastAPI Integration
6. Health Metrics

Run the examples:
```bash
uv run python examples/websocket_manager_example.py
```

## Backward Compatibility

The refactoring maintains full backward compatibility:

- Existing endpoints continue to work
- Graceful fallback if manager not initialized
- No breaking changes to message protocols
- All existing tests pass (465 tests)

## Future Enhancements

Potential improvements for future iterations:

1. **Rate Limiting:** Per-connection message rate limits
2. **Authentication:** Token-based WebSocket authentication
3. **Compression:** Message compression for large payloads
4. **Reconnection:** Automatic reconnection with session recovery
5. **Load Balancing:** Distributed connection management across instances
6. **Metrics Export:** Prometheus/StatsD metrics integration
7. **Connection Quotas:** Per-user connection limits

## Migration Guide

For existing WebSocket endpoints:

### Before
```python
@app.websocket("/ws/endpoint")
async def my_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_json()
            await websocket.send_json(response)
    except WebSocketDisconnect:
        pass
```

### After
```python
@app.websocket("/ws/endpoint")
async def my_endpoint(websocket: WebSocket):
    from src.api.deps import get_websocket_manager_optional

    ws_manager = get_websocket_manager_optional()
    if ws_manager:
        connection = await ws_manager.connect(websocket, f"endpoint-{id(websocket)}")
        try:
            while True:
                data = await connection.receive_json()
                if data is None:
                    break
                await connection.send_json(response)
        finally:
            await ws_manager.disconnect(connection.connection_id)
    else:
        # Keep old implementation as fallback
        await websocket.accept()
        # ...
```

## Performance Considerations

- **Memory:** O(n) where n = number of active connections
- **CPU:** Heartbeat runs every 30 seconds (minimal overhead)
- **Network:** One ping message per connection every 30 seconds
- **Cleanup:** Automatic with no memory leaks

## Troubleshooting

### High connection count
Check `manager.get_connection_count()` and review heartbeat cleanup logs.

### Stale connections not cleaned up
Verify heartbeat is started: `await manager.start_heartbeat()`

### Messages not received
Check connection state: `connection.is_closed` and `connection.idle_seconds`

### Memory growth
Monitor connection cleanup in logs and ensure proper disconnect handling.

## References

- [FastAPI WebSockets Documentation](https://fastapi.tiangolo.com/advanced/websockets/)
- [WebSocket RFC 6455](https://tools.ietf.org/html/rfc6455)
- Project WebSocket tests: `tests/test_websocket.py`
- Usage examples: `examples/websocket_manager_example.py`
