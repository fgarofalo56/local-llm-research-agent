# Model Context Protocol (MCP) Documentation

> **Complete guide to setting up and using MCP servers with the Local LLM Research Analytics Tool**

---

## Table of Contents

- [What is MCP?](#what-is-mcp)
- [How This Project Uses MCP](#how-this-project-uses-mcp)
- [Available MCP Servers](#available-mcp-servers)
- [Quick Start](#quick-start)
- [Documentation Structure](#documentation-structure)
- [Resources](#resources)

---

## What is MCP?

The **Model Context Protocol (MCP)** is an open protocol that standardizes how AI applications connect to external data sources and tools. It enables:

- **Standardized tool integration** - One protocol for all tools
- **Language-agnostic** - Servers in any language (Node.js, Python, .NET)
- **Local and remote** - Subprocess or HTTP-based connections
- **Automatic discovery** - AI agents detect available tools automatically

### Key Concepts

| Concept | Description |
|---------|-------------|
| **MCP Server** | Process that exposes tools and resources |
| **MCP Client** | Application that connects to servers (our AI agent) |
| **Tools** | Functions the AI can call (e.g., query database) |
| **Resources** | Data the AI can access (e.g., files, documents) |
| **Prompts** | Pre-defined instructions for the AI |

---

## How This Project Uses MCP

This project leverages MCP to connect local AI agents (powered by Ollama or Foundry Local) with external tools, primarily SQL Server databases.

### Architecture

```
┌─────────────────────┐
│   React Frontend    │
│   (User Interface)  │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│   FastAPI Backend   │
│   (API Server)      │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐      ┌──────────────────────┐
│   Pydantic AI       │◄────►│   Ollama / Foundry   │
│   (Agent Framework) │      │   (Local LLM)        │
└──────────┬──────────┘      └──────────────────────┘
           │
           ▼
┌─────────────────────┐
│   MCP Client        │
│   (pydantic-ai[mcp])│
└──────────┬──────────┘
           │
           ├─────────────────────────────┐
           │                             │
           ▼                             ▼
┌────────────────────┐      ┌───────────────────────┐
│  MSSQL MCP Server  │      │  Other MCP Servers    │
│  (Node.js/Python)  │      │  (Filesystem, etc.)   │
└──────────┬─────────┘      └───────────────────────┘
           │
           ▼
┌────────────────────┐
│   SQL Server DB    │
│   (ResearchAnalytics)│
└────────────────────┘
```

### Integration with Pydantic AI

The project uses **Pydantic AI** as the agent framework with native MCP support:

```python
from pydantic_ai import Agent
from pydantic_ai.mcp import MCPServerStdio

# Create MCP server connection
mssql_server = MCPServerStdio(
    command="node",
    args=["/path/to/mssql-mcp/index.js"],
    env={
        "SERVER_NAME": "localhost",
        "DATABASE_NAME": "ResearchAnalytics"
    }
)

# Create agent with MCP toolset
agent = Agent(
    model=model,
    system_prompt="You are a helpful SQL data analyst.",
    toolsets=[mssql_server]  # MCP server as toolset
)

# Use the agent
async with agent:
    result = await agent.run("What tables are in the database?")
```

---

## Available MCP Servers

### Primary Server: MSSQL MCP Server

| Feature | Details |
|---------|---------|
| **Purpose** | SQL Server database operations |
| **Implementation** | Node.js (primary), Python (experimental) |
| **Tools** | 8 tools (list, query, insert, update, etc.) |
| **Authentication** | SQL, Windows, Azure AD |
| **Status** | ✅ Fully supported |

**Documentation:** [MSSQL Server Setup Guide](mssql-server-setup.md)

### Future Servers

Additional MCP servers can be added for:

- **Filesystem access** - Read/write files, search directories
- **Web search** - Query search engines, fetch web content
- **Email** - Send notifications, read messages
- **Git operations** - Repository management, code search
- **Custom tools** - Domain-specific operations

**Documentation:** [Custom Server Development](custom-server-development.md)

---

## Quick Start

### Prerequisites

1. **Node.js** (v18+) or **Python** (3.11+) depending on server
2. **SQL Server** (local or Azure)
3. **Pydantic AI with MCP support** - `pip install pydantic-ai[mcp]`

### 5-Minute Setup

#### Step 1: Clone MSSQL MCP Server

```bash
git clone https://github.com/Azure-Samples/SQL-AI-samples.git
cd SQL-AI-samples/MssqlMcp/Node
npm install
```

#### Step 2: Configure Environment

Create or update `.env` file:

```bash
# Path to MCP server
MCP_MSSQL_PATH=E:/SQL-AI-samples/MssqlMcp/Node/dist/index.js

# SQL Server connection
SQL_SERVER_HOST=localhost
SQL_DATABASE_NAME=ResearchAnalytics
SQL_AUTH_TYPE=sql
SQL_USERNAME=sa
SQL_PASSWORD=YourPassword

# Security
SQL_TRUST_SERVER_CERTIFICATE=true
MCP_MSSQL_READONLY=false
```

#### Step 3: Test Connection

```bash
# Start SQL Server (Docker)
docker-compose -f docker/docker-compose.yml --env-file .env up -d mssql

# Test MCP server
node E:/SQL-AI-samples/MssqlMcp/Node/dist/index.js
```

#### Step 4: Run the Application

```bash
# Start backend API
uv run uvicorn src.api.main:app --reload

# Start frontend
cd frontend && npm run dev
```

**Troubleshooting?** See [Troubleshooting Guide](troubleshooting.md)

---

## Documentation Structure

### For Users

| Document | Purpose | Audience |
|----------|---------|----------|
| **README.md** (this file) | Overview and quick start | All users |
| **[mssql-server-setup.md](mssql-server-setup.md)** | Detailed MSSQL setup | Developers, admins |
| **[troubleshooting.md](troubleshooting.md)** | Common issues and fixes | All users |

### For Developers

| Document | Purpose | Audience |
|----------|---------|----------|
| **[custom-server-development.md](custom-server-development.md)** | Creating new MCP servers | Advanced developers |
| **[../reference/pydantic_ai_mcp.md](../reference/pydantic_ai_mcp.md)** | Pydantic AI MCP API reference | Developers |
| **[../reference/mssql_mcp_tools.md](../reference/mssql_mcp_tools.md)** | MSSQL tools reference | Developers |

---

## Configuration Files

### mcp_config.json

The project uses a JSON configuration file compatible with Claude Desktop format:

```json
{
  "mcpServers": {
    "mssql": {
      "command": "node",
      "args": ["${MCP_MSSQL_PATH}"],
      "env": {
        "SERVER_NAME": "${SQL_SERVER_HOST}",
        "DATABASE_NAME": "${SQL_DATABASE_NAME}",
        "TRUST_SERVER_CERTIFICATE": "${SQL_TRUST_SERVER_CERTIFICATE}",
        "READONLY": "${MCP_MSSQL_READONLY}",
        "AUTH_TYPE": "${SQL_AUTH_TYPE}",
        "SQL_USERNAME": "${SQL_USERNAME}",
        "SQL_PASSWORD": "${SQL_PASSWORD}"
      }
    }
  }
}
```

**Environment variable expansion:**
- `${VAR}` - Required variable from `.env`
- `${VAR:-default}` - Variable with default value

---

## Security Considerations

### Best Practices

| Practice | Priority | Recommendation |
|----------|----------|----------------|
| **Read-only mode** | 🔴 High | Use `READONLY=true` for exploration |
| **Least privilege** | 🔴 High | Grant minimum SQL permissions |
| **Environment variables** | 🔴 High | Never hardcode credentials |
| **Local execution** | 🟡 Medium | Keep MCP servers local when possible |
| **Audit logging** | 🟡 Medium | Monitor tool usage |

### Read-Only Mode

Enable safe exploration without data modification:

```bash
# In .env
MCP_MSSQL_READONLY=true
```

**Blocked operations:**
- `insert_data`
- `update_data`
- `drop_table`
- `create_table`
- `create_index`

**Allowed operations:**
- `list_tables`
- `describe_table`
- `read_data`

---

## Performance Tips

### Connection Pooling

MCP servers use connection pools. Configure for your workload:

```bash
# Environment variables for server performance
MCP_TIMEOUT=30          # Operation timeout (seconds)
SQL_POOL_SIZE=10        # Connection pool size
```

### Caching

Enable response caching to reduce LLM calls:

```bash
CACHE_ENABLED=true
CACHE_MAX_SIZE=100
CACHE_TTL_SECONDS=3600
```

---

## Resources

### Official Documentation

- [Model Context Protocol Specification](https://modelcontextprotocol.io/)
- [Pydantic AI MCP Client Guide](https://ai.pydantic.dev/mcp/client/)
- [MSSQL MCP Server Blog Post](https://devblogs.microsoft.com/azure-sql/introducing-mssql-mcp-server/)
- [Azure-Samples/SQL-AI-samples](https://github.com/Azure-Samples/SQL-AI-samples)

### Project Documentation

- [Getting Started Guide](../guides/getting-started.md)
- [Configuration Reference](../guides/configuration.md)
- [API Documentation](../api/)
- [Main README](../../README.md)

### Community

- [MCP GitHub Discussions](https://github.com/modelcontextprotocol/specification/discussions)
- [Pydantic AI Discussions](https://github.com/pydantic/pydantic-ai/discussions)

---

## Next Steps

1. **New users:** Follow the [Quick Start](#quick-start) above
2. **Setup MSSQL:** Read [MSSQL Server Setup Guide](mssql-server-setup.md)
3. **Troubleshooting:** Check [Troubleshooting Guide](troubleshooting.md)
4. **Build custom servers:** See [Custom Server Development](custom-server-development.md)

---

**Need help?** Check the troubleshooting guide or open an issue on GitHub.

*Last Updated: December 2024*
