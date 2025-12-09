# Pydantic AI MCP Integration Reference

## Overview

Pydantic AI provides native support for the Model Context Protocol (MCP) through the `pydantic-ai[mcp]` extra. This allows agents to connect to MCP servers and use their tools.

## Installation

```bash
pip install pydantic-ai[mcp]
# or
uv add pydantic-ai[mcp]
```

## MCP Server Types

### MCPServerStdio

Connects via standard I/O to a subprocess:

```python
from pydantic_ai.mcp import MCPServerStdio

server = MCPServerStdio(
    command="node",
    args=["/path/to/server/index.js"],
    env={"KEY": "value"},
    timeout=30
)
```

### MCPServerStreamableHTTP

Connects via HTTP to a running server:

```python
from pydantic_ai.mcp import MCPServerStreamableHTTP

server = MCPServerStreamableHTTP('http://localhost:8000/mcp')
```

## Agent Integration

Attach MCP servers to agents via `toolsets`:

```python
from pydantic_ai import Agent
from pydantic_ai.mcp import MCPServerStdio

server = MCPServerStdio(
    command="node",
    args=["server.js"],
    timeout=30
)

agent = Agent(
    model='openai:gpt-4',
    toolsets=[server]
)

# Use async context manager to manage server lifecycle
async with agent:
    result = await agent.run("Use the tools")
```

## Loading from Configuration

Load servers from a JSON config file:

```python
from pydantic_ai.mcp import load_mcp_servers

# Config format matches Claude Desktop configuration
servers = load_mcp_servers('mcp_config.json')

agent = Agent(
    model='openai:gpt-4',
    toolsets=servers
)
```

### Config File Format

```json
{
  "mcpServers": {
    "server_name": {
      "command": "node",
      "args": ["/path/to/index.js"],
      "env": {
        "VAR": "value",
        "OTHER": "${ENV_VAR:-default}"
      }
    }
  }
}
```

Environment variable substitution:
- `${VAR}` - Required environment variable
- `${VAR:-default}` - With default value

## Ollama Integration

Use Ollama as an OpenAI-compatible provider:

```python
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel

# Ollama exposes OpenAI-compatible API at /v1
model = OpenAIModel(
    model_name="qwen2.5:7b-instruct",
    base_url="http://localhost:11434/v1",
    api_key="ollama"  # Required but not validated
)

agent = Agent(
    model=model,
    system_prompt="You are a helpful assistant.",
    toolsets=[mcp_server]
)
```

## Lifecycle Management

Always use context managers for proper cleanup:

```python
# Option 1: Agent context manager (manages all toolsets)
async with agent:
    result = await agent.run(message)

# Option 2: Individual server context
async with server:
    # Server is now connected
    tools = await server.list_tools()
```

## Error Handling

```python
from pydantic_ai.exceptions import ModelRetry, UnexpectedModelBehavior

try:
    async with agent:
        result = await agent.run(message)
except ModelRetry as e:
    print(f"Model requested retry: {e}")
except UnexpectedModelBehavior as e:
    print(f"Unexpected behavior: {e}")
```

## Best Practices

1. **Always use async context managers** - Ensures proper cleanup
2. **Set appropriate timeouts** - Prevent hanging on slow servers
3. **Validate server connectivity** - Check before user interactions
4. **Handle tool errors gracefully** - Tools can fail at runtime
5. **Use environment variables** - Don't hardcode credentials

## Key Classes

| Class | Purpose |
|-------|---------|
| `MCPServerStdio` | Connect to subprocess-based MCP servers |
| `MCPServerStreamableHTTP` | Connect to HTTP-based MCP servers |
| `load_mcp_servers` | Load servers from config file |
| `Agent` | Main agent class with toolsets support |

## References

- [Pydantic AI MCP Client Docs](https://ai.pydantic.dev/mcp/client/)
- [Model Context Protocol Specification](https://modelcontextprotocol.io/)
- [Ollama OpenAI Compatibility](https://ollama.com/blog/openai-compatibility)
