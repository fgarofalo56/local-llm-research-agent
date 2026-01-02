# WebSocket Protocol Documentation

This document describes the WebSocket endpoints available in the Local LLM Research Analytics API for real-time communication.

## Overview

The API provides two main WebSocket endpoints:

1. **Agent Chat WebSocket** (`/ws/agent/{conversation_id}`) - Real-time chat with the research agent
2. **Alert Notifications WebSocket** (`/ws/alerts`) - Real-time alert notifications

Both endpoints use JSON messages for communication and support automatic reconnection.

## Agent Chat WebSocket

### Connection

```javascript
const conversationId = 123; // Existing or new conversation ID
const ws = new WebSocket(`ws://localhost:8000/ws/agent/${conversationId}`);
```

### Lifecycle Events

#### Open

```javascript
ws.onopen = () => {
  console.log('Connected to agent');
};
```

#### Message

```javascript
ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  console.log('Received:', message);
};
```

#### Error

```javascript
ws.onerror = (error) => {
  console.error('WebSocket error:', error);
};
```

#### Close

```javascript
ws.onclose = () => {
  console.log('Disconnected from agent');
  // Implement reconnection logic
};
```

### Message Format

#### Send User Message

```json
{
  "type": "message",
  "message": "What are the active projects?",
  "use_rag": true,
  "mcp_servers": ["mssql"]
}
```

**Fields:**
- `type` (string): Always "message"
- `message` (string): User's message or query
- `use_rag` (boolean): Whether to use RAG for context (optional, default: true)
- `mcp_servers` (array): List of MCP server IDs to use (optional)

#### Receive Agent Response

```json
{
  "type": "response",
  "role": "assistant",
  "content": "There are 5 active projects...",
  "sources": [
    {
      "type": "document",
      "source": "research.pdf",
      "similarity": 0.95,
      "content": "Relevant excerpt..."
    }
  ],
  "tool_calls": [
    {
      "tool": "list_tables",
      "args": {}
    }
  ],
  "tokens_used": 145,
  "completion_time_ms": 2350
}
```

**Fields:**
- `type` (string): "response"
- `role` (string): "assistant"
- `content` (string): Agent's response
- `sources` (array): RAG sources used (if any)
- `tool_calls` (array): Tools called during response generation
- `tokens_used` (number): Tokens consumed
- `completion_time_ms` (number): Response generation time

#### Receive Error

```json
{
  "type": "error",
  "error": "Provider connection failed",
  "error_code": "PROVIDER_ERROR",
  "details": "Ollama not responding"
}
```

**Fields:**
- `type` (string): "error"
- `error` (string): Error message
- `error_code` (string): Machine-readable error code
- `details` (string): Additional details

#### Receive Status Update

```json
{
  "type": "status",
  "status": "processing",
  "message": "Generating response..."
}
```

**Fields:**
- `type` (string): "status"
- `status` (string): Current status
- `message` (string): Status message

### Python Example

```python
import asyncio
import json
import websockets

async def chat_with_agent():
    uri = "ws://localhost:8000/ws/agent/123"

    async with websockets.connect(uri) as ws:
        # Send message
        message = {
            "message": "What are the active projects?",
            "use_rag": True,
            "mcp_servers": ["mssql"]
        }
        await ws.send(json.dumps(message))

        # Receive response
        response = await ws.recv()
        data = json.loads(response)
        print(f"Agent: {data['content']}")

        # Receive until disconnection
        try:
            while True:
                response = await ws.recv()
                data = json.loads(response)
                print(f"Type: {data['type']}, Content: {data}")
        except websockets.exceptions.ConnectionClosed:
            print("Connection closed")

asyncio.run(chat_with_agent())
```

### JavaScript/TypeScript Example

```typescript
interface ChatMessage {
  message: string;
  use_rag?: boolean;
  mcp_servers?: string[];
}

interface AgentResponse {
  type: 'response' | 'error' | 'status';
  role?: string;
  content?: string;
  error?: string;
  status?: string;
  sources?: Array<{
    type: string;
    source: string;
    similarity: number;
  }>;
  tokens_used?: number;
  completion_time_ms?: number;
}

class AgentWebSocket {
  private ws: WebSocket;
  private conversationId: number;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;

  constructor(conversationId: number) {
    this.conversationId = conversationId;
    this.connect();
  }

  private connect(): void {
    this.ws = new WebSocket(
      `ws://localhost:8000/ws/agent/${this.conversationId}`
    );

    this.ws.onopen = () => {
      console.log('Connected');
      this.reconnectAttempts = 0;
    };

    this.ws.onmessage = (event) => {
      const response: AgentResponse = JSON.parse(event.data);
      this.handleResponse(response);
    };

    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    this.ws.onclose = () => {
      console.log('Disconnected');
      this.reconnect();
    };
  }

  private handleResponse(response: AgentResponse): void {
    switch (response.type) {
      case 'response':
        console.log('Response:', response.content);
        break;
      case 'error':
        console.error('Error:', response.error);
        break;
      case 'status':
        console.log('Status:', response.status);
        break;
    }
  }

  private reconnect(): void {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      const delay = Math.pow(2, this.reconnectAttempts) * 1000; // Exponential backoff
      console.log(`Reconnecting in ${delay}ms...`);
      setTimeout(() => this.connect(), delay);
    }
  }

  public send(message: ChatMessage): void {
    if (this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
    } else {
      console.error('WebSocket not open');
    }
  }

  public close(): void {
    this.ws.close();
  }
}

// Usage
const agent = new AgentWebSocket(123);
agent.send({
  message: "What are the active projects?",
  use_rag: true,
  mcp_servers: ["mssql"]
});
```

### React Hook Example

```typescript
import { useEffect, useRef, useState } from 'react';

interface ChatMessage {
  message: string;
  use_rag?: boolean;
}

export function useAgentWebSocket(conversationId: number) {
  const [messages, setMessages] = useState<any[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const ws = useRef<WebSocket | null>(null);

  useEffect(() => {
    ws.current = new WebSocket(
      `ws://localhost:8000/ws/agent/${conversationId}`
    );

    ws.current.onopen = () => setIsConnected(true);
    ws.current.onclose = () => setIsConnected(false);
    ws.current.onmessage = (event) => {
      const message = JSON.parse(event.data);
      setMessages((prev) => [...prev, message]);
    };

    return () => ws.current?.close();
  }, [conversationId]);

  const sendMessage = (message: ChatMessage) => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify(message));
    }
  };

  return { messages, isConnected, sendMessage };
}

// Usage in component
export function ChatComponent({ conversationId }: { conversationId: number }) {
  const { messages, isConnected, sendMessage } = useAgentWebSocket(
    conversationId
  );

  const handleSendMessage = (text: string) => {
    sendMessage({ message: text, use_rag: true });
  };

  return (
    <div>
      <div>Status: {isConnected ? 'Connected' : 'Disconnected'}</div>
      {messages.map((msg, i) => (
        <div key={i}>{msg.content}</div>
      ))}
      <button onClick={() => handleSendMessage('Hello')}>Send</button>
    </div>
  );
}
```

---

## Alert Notifications WebSocket

### Connection

```javascript
const alertWs = new WebSocket('ws://localhost:8000/ws/alerts');
```

### Message Format

#### Receive Alert Notification

```json
{
  "type": "alert",
  "alert_id": 1,
  "name": "High Activity Alert",
  "condition": "greater_than",
  "threshold": 10,
  "current_value": 12,
  "triggered": true,
  "triggered_at": "2024-12-18T10:30:00Z",
  "source": "scheduled_check"
}
```

**Fields:**
- `type` (string): "alert"
- `alert_id` (number): Alert ID
- `name` (string): Alert name
- `condition` (string): Trigger condition
- `threshold` (number): Alert threshold value
- `current_value` (number): Current metric value
- `triggered` (boolean): Whether alert was triggered
- `triggered_at` (string): ISO timestamp of trigger
- `source` (string): "scheduled_check" or "manual_check"

#### Send Ping (Keep-Alive)

```javascript
alertWs.send('ping');
```

#### Receive Pong (Keep-Alive Response)

```javascript
alertWs.onmessage = (event) => {
  if (event.data === 'pong') {
    console.log('Keep-alive pong received');
  }
};
```

### Python Example

```python
import asyncio
import json
import websockets

async def listen_for_alerts():
    uri = "ws://localhost:8000/ws/alerts"

    async with websockets.connect(uri) as ws:
        # Send keep-alive ping
        keep_alive_task = asyncio.create_task(keep_alive(ws))

        try:
            while True:
                message = await ws.recv()
                data = json.loads(message)
                print(f"Alert triggered: {data['name']}")
                print(f"  Value: {data['current_value']}")
                print(f"  Threshold: {data['threshold']}")
        except websockets.exceptions.ConnectionClosed:
            print("Connection closed")
        finally:
            keep_alive_task.cancel()

async def keep_alive(ws):
    while True:
        await asyncio.sleep(30)
        await ws.send('ping')

asyncio.run(listen_for_alerts())
```

### JavaScript Example

```javascript
class AlertListener {
  constructor() {
    this.ws = null;
    this.connect();
  }

  connect() {
    this.ws = new WebSocket('ws://localhost:8000/ws/alerts');

    this.ws.onopen = () => {
      console.log('Alert listener connected');
      this.startKeepAlive();
    };

    this.ws.onmessage = (event) => {
      try {
        const alert = JSON.parse(event.data);
        this.handleAlert(alert);
      } catch (e) {
        console.log('Keep-alive pong received');
      }
    };

    this.ws.onclose = () => {
      console.log('Alert listener disconnected');
      setTimeout(() => this.connect(), 5000); // Reconnect after 5s
    };
  }

  startKeepAlive() {
    this.keepAliveInterval = setInterval(() => {
      if (this.ws?.readyState === WebSocket.OPEN) {
        this.ws.send('ping');
      }
    }, 30000);
  }

  handleAlert(alert) {
    console.log(`Alert: ${alert.name}`);
    console.log(`  Current: ${alert.current_value}`);
    console.log(`  Threshold: ${alert.threshold}`);

    // Show notification
    if (Notification.permission === 'granted') {
      new Notification(alert.name, {
        body: `Value: ${alert.current_value} (threshold: ${alert.threshold})`
      });
    }
  }

  close() {
    clearInterval(this.keepAliveInterval);
    this.ws?.close();
  }
}

// Usage
const listener = new AlertListener();
```

---

## Error Handling

### Connection Errors

Handle connection failures gracefully:

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/agent/123');

ws.onerror = (error) => {
  console.error('WebSocket error:', error);
  // Attempt reconnection
};

ws.onclose = () => {
  console.log('Connection closed');
  // Implement exponential backoff
  setTimeout(() => {
    // Attempt reconnection
  }, 1000);
};
```

### Message Parsing Errors

Always validate incoming messages:

```javascript
ws.onmessage = (event) => {
  try {
    const data = JSON.parse(event.data);

    if (!data.type) {
      console.warn('Invalid message format:', data);
      return;
    }

    switch (data.type) {
      case 'response':
        handleResponse(data);
        break;
      case 'error':
        handleError(data);
        break;
      case 'status':
        handleStatus(data);
        break;
      default:
        console.warn('Unknown message type:', data.type);
    }
  } catch (e) {
    console.error('Failed to parse message:', e);
  }
};
```

### Reconnection Strategy

Implement exponential backoff for reconnection:

```javascript
class ReconnectingWebSocket {
  constructor(url, maxRetries = 5) {
    this.url = url;
    this.maxRetries = maxRetries;
    this.retries = 0;
    this.connect();
  }

  connect() {
    try {
      this.ws = new WebSocket(this.url);

      this.ws.onopen = () => {
        console.log('Connected');
        this.retries = 0;
      };

      this.ws.onclose = () => {
        this.attemptReconnect();
      };

      this.ws.onerror = (error) => {
        console.error('Error:', error);
        this.attemptReconnect();
      };
    } catch (e) {
      console.error('Failed to create WebSocket:', e);
      this.attemptReconnect();
    }
  }

  attemptReconnect() {
    if (this.retries < this.maxRetries) {
      this.retries++;
      const delay = Math.pow(2, this.retries) * 1000; // Exponential backoff
      console.log(`Reconnecting in ${delay}ms (attempt ${this.retries}/${this.maxRetries})`);
      setTimeout(() => this.connect(), delay);
    } else {
      console.error('Max reconnection attempts reached');
    }
  }

  send(message) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
    } else {
      console.warn('WebSocket not ready, message not sent');
    }
  }

  close() {
    this.ws?.close();
  }
}
```

---

## Performance Considerations

### Message Batching

For high-frequency updates, consider batching messages:

```javascript
class MessageBatcher {
  constructor(ws, flushInterval = 100) {
    this.ws = ws;
    this.flushInterval = flushInterval;
    this.buffer = [];
    this.timer = null;
  }

  add(message) {
    this.buffer.push(message);

    if (this.buffer.length >= 10) {
      this.flush();
    } else if (!this.timer) {
      this.timer = setTimeout(() => this.flush(), this.flushInterval);
    }
  }

  flush() {
    if (this.buffer.length > 0) {
      this.ws.send(JSON.stringify({
        type: 'batch',
        messages: this.buffer
      }));
      this.buffer = [];
    }
    clearTimeout(this.timer);
    this.timer = null;
  }
}
```

### Connection Pooling

Maintain a single connection per conversation:

```javascript
class WebSocketPool {
  constructor() {
    this.connections = new Map();
  }

  getConnection(conversationId) {
    if (!this.connections.has(conversationId)) {
      const ws = new WebSocket(
        `ws://localhost:8000/ws/agent/${conversationId}`
      );
      this.connections.set(conversationId, ws);
    }
    return this.connections.get(conversationId);
  }

  closeConnection(conversationId) {
    const ws = this.connections.get(conversationId);
    if (ws) {
      ws.close();
      this.connections.delete(conversationId);
    }
  }

  closeAll() {
    this.connections.forEach((ws) => ws.close());
    this.connections.clear();
  }
}
```

---

## Troubleshooting

### Connection Refused

**Problem:** `WebSocket connection failed`

**Solutions:**
- Verify API is running: `curl http://localhost:8000/api/health`
- Check firewall rules
- Verify correct URL format: `ws://` or `wss://`

### Message Not Received

**Problem:** Send message but no response

**Solutions:**
- Check connection state: `ws.readyState === WebSocket.OPEN`
- Verify message format is valid JSON
- Check browser console for errors
- Check server logs for processing errors

### Connection Drops

**Problem:** Frequent disconnections

**Solutions:**
- Implement keep-alive pings
- Use exponential backoff for reconnection
- Increase timeout values
- Check network stability

### High Latency

**Problem:** Slow responses

**Solutions:**
- Batch multiple messages
- Use pooling for multiple conversations
- Reduce message payload size
- Monitor server resource usage

---

## Best Practices

1. **Always implement reconnection logic** - Network connections are unreliable
2. **Use keep-alive pings** - Prevent connection timeout in proxies
3. **Validate all incoming messages** - Never assume message structure
4. **Handle errors gracefully** - Log errors and inform user
5. **Clean up on disconnect** - Cancel pending operations
6. **Use connection pooling** - Avoid creating multiple connections
7. **Monitor connection health** - Track connect/disconnect events
8. **Implement message queuing** - Queue messages while reconnecting

---

## API Reference

See [Complete API Reference](./reference.md) for HTTP endpoints and additional documentation.
