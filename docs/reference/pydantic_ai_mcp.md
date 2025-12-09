# 🤖 Pydantic AI MCP Integration Reference

> **Complete guide to integrating MCP servers with Pydantic AI agents**

---

## 📑 Table of Contents

- [Overview](#-overview)
- [Installation](#-installation)
- [MCP Server Types](#-mcp-server-types)
- [Agent Integration](#-agent-integration)
- [Ollama Integration](#-ollama-integration)
- [Configuration](#-configuration)
- [Lifecycle Management](#-lifecycle-management)
- [Error Handling](#-error-handling)
- [Best Practices](#-best-practices)
- [Resources](#-resources)

---

## 🎯 Overview

Pydantic AI provides native support for the Model Context Protocol (MCP) through the `pydantic-ai[mcp]` extra. This enables AI agents to connect to MCP servers and use their tools seamlessly.

### Key Features

| Feature | Status | Description |
|---------|--------|-------------|
| Stdio Servers | ✅ | Connect via subprocess |
| HTTP Servers | ✅ | Connect via HTTP |
| Config Loading | ✅ | Load from JSON files |
| Tool Discovery | ✅ | Automatic tool registration |
| Async Support | ✅ | Full async/await |

---

## 📦 Installation

### Using pip

```bash
pip install pydantic-ai[mcp]
```

### Using uv

```bash
uv add pydantic-ai[mcp]
```

### Verify Installation

```python
from pydantic_ai.mcp import MCPServerStdio
print("MCP support installed!")
```

---

## 🔌 MCP Server Types

### MCPServerStdio

Connects via standard I/O to a subprocess-based MCP server.

**Best For:** Local MCP servers, development

```python
from pydantic_ai.mcp import MCPServerStdio

server = MCPServerStdio(
    command="node",
    args=["/path/to/server/index.js"],
    env={"KEY": "value"},
    timeout=30
)
```

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `command` | str | ✅ | Executable command |
| `args` | list | ❌ | Command arguments |
| `env` | dict | ❌ | Environment variables |
| `timeout` | int | ❌ | Operation timeout (seconds) |

### MCPServerStreamableHTTP

Connects via HTTP to a running MCP server.

**Best For:** Remote servers, microservices

```python
from pydantic_ai.mcp import MCPServerStreamableHTTP

server = MCPServerStreamableHTTP('http://localhost:8000/mcp')
```

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `url` | str | ✅ | Server HTTP URL |

---

## 🤝 Agent Integration

### Basic Setup

Attach MCP servers to agents via `toolsets`:

```python
from pydantic_ai import Agent
from pydantic_ai.mcp import MCPServerStdio

# Create MCP server
server = MCPServerStdio(
    command="node",
    args=["server.js"],
    timeout=30
)

# Create agent with MCP toolset
agent = Agent(
    model='openai:gpt-4',
    system_prompt="You are a helpful data analyst.",
    toolsets=[server]
)

# Use async context manager
async with agent:
    result = await agent.run("Query the database")
    print(result.output)
```

### Multiple Servers

Connect to multiple MCP servers:

```python
mssql_server = MCPServerStdio(
    command="node",
    args=["/path/to/mssql-mcp/index.js"]
)

filesystem_server = MCPServerStdio(
    command="node",
    args=["/path/to/fs-mcp/index.js"]
)

agent = Agent(
    model='openai:gpt-4',
    toolsets=[mssql_server, filesystem_server]
)
```

---

## 🦙 Ollama Integration

Use Ollama as a local OpenAI-compatible provider:

```python
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.mcp import MCPServerStdio

# Configure Ollama
model = OpenAIModel(
    model_name="qwen2.5:7b-instruct",
    base_url="http://localhost:11434/v1",
    api_key="ollama"  # Required but not validated
)

# Create MCP server
mcp_server = MCPServerStdio(
    command="node",
    args=["/path/to/mssql-mcp/index.js"],
    env={
        "SERVER_NAME": "localhost",
        "DATABASE_NAME": "ResearchAnalytics"
    }
)

# Create agent
agent = Agent(
    model=model,
    system_prompt="You are a SQL data analyst. Help users query databases.",
    toolsets=[mcp_server]
)
```

### Recommended Models for Tool Calling

| Model | Size | Tool Calling | Notes |
|-------|------|--------------|-------|
| `qwen2.5:7b-instruct` | 4.4GB | ✅ Excellent | Recommended |
| `llama3.1:8b` | 4.7GB | ✅ Good | Alternative |
| `mistral:7b-instruct` | 4.1GB | ✅ Good | Lightweight |
| `codellama:7b` | 3.8GB | ⚠️ Limited | Code-focused |

---

## ⚙️ Configuration

### Loading from Config File

Load servers from a JSON configuration file:

```python
from pydantic_ai.mcp import load_mcp_servers

# Load servers from config
servers = load_mcp_servers('mcp_config.json')

# Use with agent
agent = Agent(
    model='openai:gpt-4',
    toolsets=servers
)
```

### Config File Format

The format matches Claude Desktop configuration:

```json
{
  "mcpServers": {
    "mssql": {
      "command": "node",
      "args": ["/path/to/mssql-mcp/index.js"],
      "env": {
        "SERVER_NAME": "localhost",
        "DATABASE_NAME": "ResearchAnalytics",
        "TRUST_SERVER_CERTIFICATE": "true"
      }
    },
    "filesystem": {
      "command": "node",
      "args": ["/path/to/fs-mcp/index.js"],
      "env": {
        "ALLOWED_PATHS": "/data,/reports"
      }
    }
  }
}
```

### Environment Variable Expansion

Variables in config are expanded from the environment:

| Syntax | Description | Example |
|--------|-------------|---------|
| `${VAR}` | Required variable | `${SQL_SERVER_HOST}` |
| `${VAR:-default}` | With default value | `${PORT:-1433}` |

```json
{
  "env": {
    "SERVER_NAME": "${SQL_SERVER_HOST}",
    "DATABASE_NAME": "${SQL_DATABASE_NAME:-master}",
    "PASSWORD": "${SQL_PASSWORD}"
  }
}
```

---

## 🔄 Lifecycle Management

### Context Manager Pattern

Always use context managers for proper cleanup:

```python
# ✅ Recommended: Agent context manager
async with agent:
    result = await agent.run(message)
```

### Manual Server Management

For fine-grained control:

```python
# Individual server context
async with server:
    # Server is connected
    tools = await server.list_tools()
    print(f"Available tools: {[t.name for t in tools]}")
```

### Multiple Conversations

```python
async with agent:
    # Multiple runs within same context
    result1 = await agent.run("List all tables")
    result2 = await agent.run("Describe the Users table")
    result3 = await agent.run("Show top 10 users")
```

---

## ⚠️ Error Handling

### Exception Types

| Exception | Cause | Handling |
|-----------|-------|----------|
| `ModelRetry` | Model requested retry | May auto-retry |
| `UnexpectedModelBehavior` | Invalid model response | Log and retry |
| `TimeoutError` | Operation timeout | Increase timeout |
| `ConnectionError` | Server connection failed | Check server |

### Error Handling Pattern

```python
from pydantic_ai.exceptions import ModelRetry, UnexpectedModelBehavior

try:
    async with agent:
        result = await agent.run(message)
except ModelRetry as e:
    print(f"Model requested retry: {e}")
    # Handle retry logic
except UnexpectedModelBehavior as e:
    print(f"Unexpected model behavior: {e}")
    # Log and handle gracefully
except TimeoutError:
    print("Operation timed out")
    # Increase timeout or simplify query
except Exception as e:
    print(f"Unexpected error: {e}")
    # Generic error handling
```

### Graceful Degradation

```python
async def safe_query(agent, message):
    """Query with fallback handling."""
    try:
        async with agent:
            result = await agent.run(message)
            return result.output
    except Exception as e:
        return f"Unable to process query: {e}"
```

---

## 🏆 Best Practices

### Development Guidelines

| Practice | Priority | Description |
|----------|----------|-------------|
| Use context managers | 🔴 High | Always for cleanup |
| Set timeouts | 🔴 High | Prevent hanging |
| Validate connectivity | 🟡 Medium | Check before use |
| Handle errors gracefully | 🟡 Medium | User-friendly messages |
| Use environment variables | 🔴 High | Never hardcode secrets |

### Code Quality

```python
# ✅ Good: Environment variables for config
import os

server = MCPServerStdio(
    command="node",
    args=[os.getenv("MCP_MSSQL_PATH")],
    env={
        "SERVER_NAME": os.getenv("SQL_SERVER_HOST"),
        "DATABASE_NAME": os.getenv("SQL_DATABASE_NAME")
    },
    timeout=int(os.getenv("MCP_TIMEOUT", "30"))
)

# ❌ Bad: Hardcoded values
server = MCPServerStdio(
    command="node",
    args=["/hardcoded/path/index.js"],
    env={
        "PASSWORD": "secret123"  # Never do this!
    }
)
```

### Testing Pattern

```python
async def test_mcp_connectivity():
    """Test MCP server is accessible."""
    async with server:
        tools = await server.list_tools()
        assert len(tools) > 0, "No tools available"
        print(f"✅ Connected. {len(tools)} tools available.")
```

---

## 📊 Key Classes Reference

| Class | Purpose | Import |
|-------|---------|--------|
| `MCPServerStdio` | Subprocess-based servers | `pydantic_ai.mcp` |
| `MCPServerStreamableHTTP` | HTTP-based servers | `pydantic_ai.mcp` |
| `load_mcp_servers` | Load from config file | `pydantic_ai.mcp` |
| `Agent` | Main agent class | `pydantic_ai` |
| `OpenAIModel` | OpenAI-compatible models | `pydantic_ai.models.openai` |

---

## 📚 Resources

### Official Documentation

- 📖 [Pydantic AI MCP Client Docs](https://ai.pydantic.dev/mcp/client/)
- 📘 [Model Context Protocol Specification](https://modelcontextprotocol.io/)
- 🦙 [Ollama OpenAI Compatibility](https://ollama.com/blog/openai-compatibility)
- 📕 [Pydantic AI GitHub](https://github.com/pydantic/pydantic-ai)

### Related Guides

- [Getting Started](../guides/getting-started.md)
- [Configuration Reference](../guides/configuration.md)
- [MSSQL MCP Tools](mssql_mcp_tools.md)

---

*Last Updated: December 2024*
