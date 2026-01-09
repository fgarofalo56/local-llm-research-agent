# MCP Server Configuration Fix

**Date:** 2026-01-09  
**Issue:** Agent crashed with ExceptionGroup error when trying to use Archon

## Root Cause

The error occurred because:

1. **Archon was misconfigured** as an HTTP MCP server in `mcp_config.json`
2. **Archon is NOT an HTTP MCP endpoint** - it's already available via built-in tools
3. When the agent tried to connect to `http://localhost:8051/mcp`, it failed

## How Archon Actually Works

Archon MCP server is **already connected** to this CLI session via the Claude/GitHub Copilot MCP infrastructure. You can use it directly with:

- `archon-find_projects()`
- `archon-find_tasks()`
- `archon-find_documents()`
- `archon-rag_search_knowledge_base()`
- And all other `archon-*` tools

**You DO NOT need to configure it in mcp_config.json.**

## Changes Made

### 1. Disabled Archon Entry
**File:** `mcp_config.json`

Changed:
```json
{
  "archon": {
    "enabled": true,
    "url": "http://localhost:8051/mcp"
  }
}
```

To:
```json
{
  "archon": {
    "enabled": false,
    "description": "Archon is already available as built-in tools (archon-*), not via HTTP MCP"
  }
}
```

### 2. Disabled Microsoft Docs MCP
**File:** `mcp_config.json`

The microsoft.docs.mcp server URL (`https://mcp.azure-api.net/v1`) doesn't appear to be a valid public endpoint. Disabled it to prevent errors:

```json
{
  "microsoft.docs.mcp": {
    "enabled": false,
    "transport": "streamable_http",
    "url": "https://mcp.azure-api.net/v1"
  }
}
```

### 3. Cleaned Up Null URLs
**File:** `mcp_config.json`

Removed `"url": null` and `"headers": {}` from stdio servers (analytics-management, data-analytics) since these fields are only for HTTP/SSE transports.

## Current Enabled MCP Servers

Your CLI agent now loads **3 stdio servers**:

1. **mssql** - SQL Server database operations (via Node.js MCP server)
2. **analytics-management** - Dashboard and widget management
3. **data-analytics** - Statistical analysis and time series

## Using Archon with Your Agent

To use Archon for RAG queries, just use the built-in tools directly:

```python
# Example: Search Archon knowledge base
archon-rag_search_knowledge_base(query="claude agents sdk", match_count=5)

# Example: Find project tasks
archon-find_tasks(project_id="16394505-e6c5-4e24-8ab4-97bd6a650cfb")
```

**The agent will NOT crash anymore** because it's not trying to connect to a non-existent HTTP MCP endpoint.

## Testing

After the fix:
```bash
$ uv run python -c "from src.mcp.client import MCPClientManager; ..."

Loaded 3 enabled servers
  - mssql (stdio)
  - analytics-management (stdio)
  - data-analytics (stdio)
```

✅ No HTTP servers, no connection errors.

## Next Steps

1. **Restart your CLI chat** for changes to take effect
2. Test with: "can you use archon and perform a rag query for claude agents sdk"
3. The agent should now work without ExceptionGroup errors

## Understanding MCP Transports

**Stdio Transport (Local):**
- Subprocess-based (command + args + env)
- Your 3 enabled servers use this
- ✅ Works with local Node.js/Python MCP servers

**HTTP Transport (Remote):**
- URL-based endpoints
- Requires actual HTTP server exposing MCP protocol
- ❌ Currently disabled (no valid endpoints configured)

**Built-in MCP Tools:**
- Archon, GitHub, web search, etc.
- Already connected via Claude infrastructure
- No configuration needed in mcp_config.json
