# ADR-005: WebSocket for Real-Time Chat Communication

**Date:** 2025-01-15

**Status:** Accepted

---

## Context

The Local LLM Research Agent provides a conversational interface for querying SQL Server data via natural language. The agent often needs to perform multiple steps (list tables, describe schemas, execute queries) and stream LLM responses token-by-token for better user experience.

### Requirements
- Real-time streaming of LLM tokens as they're generated
- Progressive display of agent tool calls and results
- Immediate feedback during long-running queries
- Maintain conversation context across multiple turns
- Handle connection interruptions gracefully
- Support concurrent users/conversations
- Efficient network utilization (no polling)
- Compatible with React frontend and Pydantic AI backend

### Technical Context
- Pydantic AI supports streaming via async generators
- FastAPI supports WebSocket endpoints
- React frontend needs real-time updates without page refresh
- Local LLM (Ollama) generates tokens progressively
- Agent may call multiple MCP tools per query
- Average query time: 2-10 seconds (schema lookup + query execution)
- Token streaming improves perceived performance

### User Experience Goals
- Show "thinking" indicators during tool calls
- Display partial responses as tokens arrive
- Update UI immediately when tool results come in
- Allow interrupting long-running queries
- Maintain smooth, responsive chat experience

## Decision

We will use **WebSocket** connections for all real-time chat communication between the React frontend and FastAPI backend.

### Implementation Details

**Backend (FastAPI)**:
```python
# src/api/routes/agent.py
@router.websocket("/ws/agent/{conversation_id}")
async def websocket_chat(websocket: WebSocket, conversation_id: str):
    await websocket.accept()
    try:
        async for token in agent.run_stream(message):
            await websocket.send_json({
                "type": "token",
                "content": token
            })
    except WebSocketDisconnect:
        # Handle graceful disconnection
    finally:
        await websocket.close()
```

**Frontend (React)**:
```typescript
// useWebSocket hook
const ws = new WebSocket(`ws://localhost:8000/ws/agent/${conversationId}`);
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  if (data.type === 'token') {
    appendToken(data.content);
  }
};
```

### Message Protocol
```typescript
// Server -> Client message types
type StreamMessage =
  | { type: "token", content: string }
  | { type: "tool_call", tool: string, args: any }
  | { type: "tool_result", result: any }
  | { type: "error", message: string }
  | { type: "done" }

// Client -> Server messages
type ClientMessage = {
  message: string;
  conversation_id: string;
  mcp_servers?: string[];
}
```

### Connection Management
- Auto-reconnect on network interruptions (exponential backoff)
- Heartbeat/ping every 30 seconds to keep connection alive
- Graceful shutdown on page navigation
- Connection pooling handled by FastAPI/Starlette

## Consequences

### Positive Consequences
- **Real-Time UX**: Tokens appear instantly as LLM generates them (no perceived latency)
- **Progressive Loading**: Users see agent "thinking" and tool execution in real-time
- **Efficient**: Single persistent connection vs HTTP polling (reduces server load)
- **Bidirectional**: Server can push updates without client request
- **Stateful**: Connection maintains conversation context naturally
- **Interruption Support**: Can send cancel message over same connection
- **Network Efficient**: Binary framing reduces overhead vs HTTP headers
- **Scalability**: FastAPI async handles thousands of concurrent WebSocket connections
- **Developer Experience**: Native WebSocket support in both FastAPI and modern browsers
- **Streaming Native**: Pydantic AI streaming maps naturally to WebSocket sends

### Negative Consequences
- **Connection Complexity**: Must handle disconnects, reconnects, timeouts
- **State Management**: Need to track connection state in React (connecting, open, closed, error)
- **Debugging Harder**: Can't use browser network tab like REST (need WebSocket inspector)
- **Load Balancing**: Requires sticky sessions or connection tracking for multi-instance deployments
- **Protocol Overhead**: Need to design message format (vs REST's standard conventions)
- **Compatibility**: Some corporate firewalls block WebSocket (fallback to SSE needed)
- **Testing**: More complex to test than REST endpoints

### Neutral Consequences
- **Alternative to SSE**: Could use Server-Sent Events (SSE) for one-way streaming
- **Protocol Choice**: Could use Socket.IO for easier reconnection (adds dependency)
- **JSON vs Binary**: Using JSON for simplicity (could optimize with msgpack/protobuf)

## Alternatives Considered

### Alternative 1: HTTP Polling (Short Polling)
- **Pros:**
  - Simple to implement (just REST endpoints)
  - Works everywhere (no firewall issues)
  - Easy to debug with browser tools
  - Stateless (easier load balancing)
- **Cons:**
  - High latency (poll interval = latency)
  - Wasteful (many empty responses)
  - Server load (constant polling)
  - Not real-time (delayed updates)
  - Poor UX (choppy token display)
- **Reason for rejection:** Terrible user experience; high server load

### Alternative 2: HTTP Long Polling
- **Pros:**
  - More efficient than short polling
  - Works with firewalls
  - Simpler than WebSocket
  - Stateless
- **Cons:**
  - Still higher latency than WebSocket
  - Request/response overhead for each "poll"
  - Complex reconnection logic
  - Not truly bidirectional
  - HTTP header overhead
- **Reason for rejection:** Complexity approaching WebSocket without benefits

### Alternative 3: Server-Sent Events (SSE)
- **Pros:**
  - Native browser support (EventSource API)
  - Simpler than WebSocket (HTTP-based)
  - Automatic reconnection
  - Easy to debug
  - Works through proxies
  - No need for message protocol
- **Cons:**
  - Uni-directional only (server -> client)
  - Need separate POST endpoint for client messages
  - Limited to text/UTF-8 (no binary)
  - No built-in compression
  - Browser connection limits (6 per domain)
- **Reason for rejection:** Uni-directional limitation requires dual-channel setup

### Alternative 4: GraphQL Subscriptions
- **Pros:**
  - GraphQL ecosystem benefits
  - Type-safe schema
  - Strong tooling
  - WebSocket-based under the hood
- **Cons:**
  - Requires full GraphQL setup (Apollo, etc.)
  - Overkill for simple streaming
  - Added complexity (GraphQL + WebSocket)
  - Learning curve for team
  - FastAPI integration less mature than REST
- **Reason for rejection:** Excessive complexity for use case; REST already in use

### Alternative 5: gRPC Streaming
- **Pros:**
  - Binary protocol (efficient)
  - Built-in streaming
  - Strong typing with protobufs
  - Bidirectional
- **Cons:**
  - Requires code generation
  - Browser support requires gRPC-Web proxy
  - Complex setup
  - FastAPI integration not standard
  - Team unfamiliar with gRPC
  - Debugging tools limited
- **Reason for rejection:** Complexity and browser support issues

### Alternative 6: Socket.IO
- **Pros:**
  - Auto-reconnection built-in
  - Fallback to polling if WebSocket blocked
  - Room/namespace support
  - Easy to use
  - Good documentation
- **Cons:**
  - Additional dependency (python-socketio)
  - Custom protocol (not standard WebSocket)
  - Larger client bundle
  - More abstraction than needed
  - FastAPI integration requires adapter
- **Reason for rejection:** FastAPI native WebSocket sufficient; Socket.IO adds complexity

### Alternative 7: REST with Chunked Transfer Encoding
- **Pros:**
  - HTTP-based (familiar)
  - Standard approach
  - Works through proxies
  - No WebSocket setup
- **Cons:**
  - Uni-directional (server -> client)
  - Poor browser support (fetch API doesn't expose chunks easily)
  - Complex client-side parsing
  - No cancellation without AbortController
  - Still need separate endpoint for messages
- **Reason for rejection:** Browser API limitations make implementation complex

## References

- **FastAPI WebSocket Documentation**: [fastapi.tiangolo.com/advanced/websockets](https://fastapi.tiangolo.com/advanced/websockets/)
- **MDN WebSocket API**: [developer.mozilla.org/en-US/docs/Web/API/WebSocket](https://developer.mozilla.org/en-US/docs/Web/API/WebSocket)
- **Related ADRs**:
  - [ADR-004: React Frontend](004-react-frontend.md) - Why React for rich real-time UI
  - [ADR-002: Pydantic AI](002-pydantic-ai.md) - Agent framework with streaming support
- **Implementation Files**:
  - `src/api/routes/agent.py` - WebSocket endpoint: `/ws/agent/{conversation_id}`
  - `frontend/src/hooks/useWebSocket.ts` - React WebSocket hook
  - `frontend/src/components/chat/ChatInterface.tsx` - Chat UI with streaming
  - `frontend/src/lib/websocket.ts` - WebSocket client with auto-reconnect
- **Configuration**:
  - `.env`: `API_HOST=0.0.0.0`, `API_PORT=8000`
  - `vite.config.ts`: WebSocket proxy for development
- **Testing**:
  - `tests/test_websocket.py` - WebSocket endpoint tests
  - Manual testing: `wscat -c ws://localhost:8000/ws/agent/test`

---

**Note:** This decision should be revisited if:
1. Firewall/proxy issues become widespread (consider SSE fallback)
2. Socket.IO features (rooms, namespaces) become necessary
3. Multi-instance deployment requires complex sticky session setup
4. Binary protocol efficiency becomes critical (consider gRPC)
5. GraphQL adoption across project makes subscriptions more natural
