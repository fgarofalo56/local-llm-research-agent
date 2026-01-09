# MCP Session Management Fix

## Problem

The CLI was establishing **new MCP sessions on every message**, causing:
- Multiple POST requests to HTTP MCP servers (Microsoft Learn, Archon)
- Session overhead even for simple questions
- Inefficient use of resources
- Slower response times

**Root Cause:** The `ResearchAgent._run_agent_with_retry()` method wrapped every call in `async with self.agent:`, which tells Pydantic AI to establish new MCP connections.

## Solution

Use Pydantic AI's context manager pattern correctly:
1. **Enter agent context ONCE** at CLI session start
2. **Keep MCP sessions open** for the entire CLI session  
3. **Only close sessions** when user exits CLI

This matches the Pydantic AI best practice for long-running applications.

## Changes Required

### 1. Update `src/agent/core.py`

Add context manager support to `ResearchAgent`:

```python
async def __aenter__(self):
    """Enter async context - opens MCP sessions once."""
    await self.agent.__aenter__()
    return self

async def __aexit__(self, exc_type, exc_val, exc_tb):
    """Exit async context - closes MCP sessions."""
    return await self.agent.__aexit__(exc_type, exc_val, exc_tb)
```

Remove the `async with` from `_run_agent_with_retry()`:

```python
@retry(config=self._retry_config, circuit_breaker=self._circuit_breaker)
async def _execute():
    # Remove: async with self.agent:
    result = await self.agent.run(message)
    return result.output
```

### 2. Update `src/cli/chat.py`

Wrap the entire chat loop in the agent context:

```python
# Create agent
agent = ResearchAgent(...)

# Enter agent context for entire session
async with agent:
    console.print(f"✓ MCP sessions established")
    
    while True:
        # Handle user input...
        # All messages use the same MCP sessions
```

## Benefits

✅ **No reconnection overhead** - MCP sessions stay open  
✅ **Faster responses** - No session establishment delay  
✅ **Clean logs** - Only connect once at startup  
✅ **Resource efficient** - Reuse connections  
✅ **Follows Pydantic AI best practices**

## Testing

Before fix:
```
You: do you have access to tools?

23:49:59 POST https://learn.microsoft.com/api/mcp "HTTP/1.1 200 OK"
23:49:59 Session ID: eyJ...
23:50:06 POST http://localhost:8051/mcp "HTTP/1.1 200 OK"  
23:50:06 Session ID: fc51...
```

After fix:
```
Loading MCP servers: mssql, microsoft.docs.mcp, archon...
✓ MCP sessions established

You: do you have access to tools?
[Agent responds immediately, no new connections]

You: search archon for "claude agents sdk"
[Uses existing Archon session, no reconnection]
```

## Implementation

See the following files for complete implementation:
- `src/agent/core.py` - Context manager support
- `src/cli/chat.py` - Session-level context wrapping

## References

- [Pydantic AI Agents Documentation](https://ai.pydantic.dev/)
- [MCP Specification](https://modelcontextprotocol.io)
- [Async Context Managers in Python](https://docs.python.org/3/reference/datamodel.html#async-context-managers)
