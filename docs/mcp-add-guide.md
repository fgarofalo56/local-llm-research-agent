# /mcp add - Interactive MCP Server Wizard

## Overview

Yes! The `/mcp add` command provides an **interactive wizard** to add new MCP servers. It's designed to be user-friendly with templates for common server types.

## How to Use

1. In the CLI, type: `/mcp add`
2. Follow the wizard prompts
3. Restart the chat to activate the new server

## Supported MCP Server Types

The wizard supports 5 types of MCP servers:

### 1. MSSQL (SQL Server)
**Protocol:** Stdio-based MCP  
**What it does:** Connect to Microsoft SQL Server databases  
**Example use case:** Query SQL Server databases, run analytics

**Typical setup:**
- Command: `node`
- Args: `/path/to/SQL-AI-samples/MssqlMcp/Node/dist/index.js`
- Environment variables: SERVER_NAME, DATABASE_NAME, TRUST_SERVER_CERTIFICATE

### 2. PostgreSQL
**Protocol:** Stdio-based MCP  
**What it does:** Connect to PostgreSQL databases  
**Example use case:** Query Postgres databases, data analysis

**Typical setup:**
- Command: `node` or `python`
- Args: Path to PostgreSQL MCP server script
- Environment variables: POSTGRES_HOST, POSTGRES_PORT, POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD

### 3. MongoDB
**Protocol:** Stdio-based MCP  
**What it does:** Connect to MongoDB databases  
**Example use case:** Query MongoDB collections, document operations

**Typical setup:**
- Command: `node` or `python`
- Args: Path to MongoDB MCP server script
- Environment variables: MONGODB_URI, MONGODB_DB

### 4. Brave Search (Pre-configured Template)
**Protocol:** Stdio-based MCP  
**What it does:** Web search capabilities via Brave Search API  
**Example use case:** Real-time web searches, fact-checking, current events

**Special features:**
- **One-click setup!** Uses a pre-configured template
- Only requires: `BRAVE_API_KEY` environment variable
- Get your API key: https://brave.com/search/api/

**How to add:**
1. Get Brave API key from https://brave.com/search/api/
2. Set environment variable: `BRAVE_API_KEY=your_key_here`
3. Run `/mcp add` and select option 4
4. Done! No additional configuration needed

### 5. Custom (Any MCP Server)
**Protocol:** Stdio-based MCP  
**What it does:** Add any custom MCP server  
**Example use cases:** 
- Python-based MCP servers (like analytics-management, data-analytics)
- Custom Node.js MCP servers
- Any stdio-based MCP implementation

**Setup wizard prompts:**
1. **Server name** - Unique identifier (e.g., "my-analytics-server")
2. **Command** - Executable command (e.g., "node", "python", "uv run")
3. **Arguments** - Space-separated args (e.g., "server.js" or "-m my_mcp_server")
4. **Read-only mode** - y/n (restricts write operations)
5. **Description** - Optional description for documentation

## MCP Protocol Support

**Currently Supported:**
- ✅ **Stdio-based MCP servers** - MCP servers that communicate via standard input/output
  - Node.js MCP servers (`node script.js`)
  - Python MCP servers (`python -m mcp_server` or `uv run`)
  - Any executable that implements stdio-based MCP protocol

**Not Yet Supported:**
- ❌ **HTTP-based MCP servers** - MCP servers that use HTTP/REST APIs
  - These are detected and logged but skipped during initialization
  - Example: `microsoft.docs.mcp` (currently in config but not functional)

## Example Workflow

### Adding a Custom Python MCP Server

```
▸ You: /mcp add

✧ Add MCP Server

Select server type:
  1. MSSQL - SQL Server database
  2. PostgreSQL - PostgreSQL database
  3. MongoDB - MongoDB database
  4. Brave Search - Web search
  5. Custom - Custom MCP server

Choice [5]: 5
Server name (unique): my-custom-server
Command (e.g., 'node', 'python') [node]: uv run
Arguments (space-separated): python -m src.mcp.my_server
Read-only mode? [n]: n
Description (optional): My custom analytics server

✓ Added server: my-custom-server
ℹ Restart chat to activate the new server
```

### Adding Brave Search (Quick Setup)

```
▸ You: /mcp add

✧ Add MCP Server

Select server type:
  1. MSSQL - SQL Server database
  2. PostgreSQL - PostgreSQL database
  3. MongoDB - MongoDB database
  4. Brave Search - Web search
  5. Custom - Custom MCP server

Choice [5]: 4

ℹ Using Brave Search template
ℹ Set BRAVE_API_KEY environment variable before use

✓ Added Brave Search server
ℹ Restart chat to activate
```

## Configuration Storage

All MCP server configurations are stored in:
- **File:** `mcp_config.json` (project root)
- **Format:** JSON with Pydantic validation
- **Environment variables:** Supports `${VAR}` and `${VAR:-default}` syntax

## After Adding a Server

1. **Restart the CLI:** Exit and restart `uv run python -m src.cli.chat`
2. **Verify it loaded:** Run `/mcp` to see the new server
3. **Check status:** Run `/mcp status <server_name>` for details
4. **Enable/Disable:** Use `/mcp enable <name>` or `/mcp disable <name>`

## Troubleshooting

**Server shows as enabled but not loading?**
- Check that the command path is correct
- Ensure environment variables are set (if needed)
- Look at logs for error messages
- Try `/mcp status <name>` for diagnostic info

**HTTP-based MCP server not working?**
- HTTP servers are detected but not yet supported
- Only stdio-based servers are currently functional
- You'll see: "HTTP-based MCP servers not yet supported" in logs

**Server name conflicts?**
- Each server must have a unique name
- Use `/mcp` to see existing server names
- Remove old servers with `/mcp remove <name>` if needed

## Advanced: Creating Your Own MCP Server

Want to create a custom MCP server? You need:

1. **Implement the MCP protocol** (stdio-based)
2. **Define tools** with names, descriptions, and parameters
3. **Handle tool calls** and return results
4. **Package as executable** (Node.js script, Python module, etc.)

**Example Python MCP server structure:**
```python
# my_mcp_server.py
from mcp import Server
from mcp.server.stdio import stdio_server

server = Server("my-server")

@server.tool()
async def my_tool(param: str) -> str:
    """Tool description."""
    return f"Result: {param}"

async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
```

## Summary

✅ **Yes, it's a wizard!** - Interactive prompts guide you through setup  
✅ **5 server types supported** - MSSQL, PostgreSQL, MongoDB, Brave Search, Custom  
✅ **Stdio-based MCP protocol only** - HTTP servers detected but not yet functional  
✅ **One-click Brave Search** - Pre-configured template for web search  
✅ **Custom servers welcome** - Add any stdio-based MCP server  
✅ **Stored in mcp_config.json** - Easy to edit manually if needed  
✅ **Environment variable support** - Use `${VAR}` syntax for secrets
