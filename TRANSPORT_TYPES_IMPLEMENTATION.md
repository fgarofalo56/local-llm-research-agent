# MCP Transport Types Implementation

**Date:** 2026-01-09  
**Status:** ✅ Complete  
**Issue:** [Critical] MCP transport support was incomplete - only stdio was supported

## Problem Identified

The user discovered that our MCP implementation only supported **stdio transport** (subprocess-based), when the MCP specification defines **three transport types**:

1. **Stdio** - subprocess communication (command + args + env)
2. **Streamable HTTP** - HTTP endpoints with chunked responses (production standard)
3. **SSE** (Server-Sent Events) - legacy, deprecated but still used

**Impact:** HTTP-based MCP servers (like microsoft.docs.mcp, archon) were being silently skipped during loading.

## Changes Implemented

### 1. Configuration Models (`src/mcp/config.py`)

**Added:**
- `TransportType` enum with STDIO, STREAMABLE_HTTP, SSE values
- `transport: TransportType` field to `MCPServerConfig` (defaults to stdio)
- `url: str | None` field for HTTP/SSE transports
- `headers: dict[str, str]` field for HTTP authentication

**Enhanced:**
- `@model_validator` to enforce transport-specific requirements:
  - Stdio requires `command` field
  - HTTP/SSE require `url` field
- `from_dict()` with auto-detection for backward compatibility:
  - If `command` present → stdio
  - If `url` present → streamable_http
  - Otherwise → defaults to stdio

**Example configs:**
```python
# Stdio transport
MCPServerConfig(
    name="mssql",
    transport=TransportType.STDIO,
    command="node",
    args=["server.js"],
    env={"KEY": "value"}
)

# HTTP transport
MCPServerConfig(
    name="docs",
    transport=TransportType.STREAMABLE_HTTP,
    url="https://mcp.azure-api.net/v1",
    headers={"Authorization": "Bearer token"}
)
```

### 2. MCP Client Manager (`src/mcp/client.py`)

**Added imports:**
```python
from pydantic_ai.mcp import MCPServerStdio, MCPServerStreamableHTTP, MCPServerSSE
from src.mcp.config import TransportType
```

**Rewrote `_load_server()` method:**
- Branched logic based on `config.transport` field
- Creates appropriate Pydantic AI server class:
  - `TransportType.STDIO` → `MCPServerStdio(command, args, env)`
  - `TransportType.STREAMABLE_HTTP` → `MCPServerStreamableHTTP(url, headers)`
  - `TransportType.SSE` → `MCPServerSSE(url, headers)`
- Resolves environment variables for all transports
- Enhanced logging to show transport type

**Updated type hints:**
- `_servers: dict[str, MCPServerStdio | MCPServerStreamableHTTP | MCPServerSSE]`
- `get_active_toolsets()` return type updated

### 3. Configuration File (`mcp_config.json`)

**Updated all servers with `transport` field:**
```json
{
  "mssql": {
    "transport": "stdio",
    "command": "node",
    "args": ["${MCP_MSSQL_PATH}"],
    "env": {...}
  },
  "microsoft.docs.mcp": {
    "transport": "streamable_http",
    "url": "https://mcp.azure-api.net/v1",
    "headers": {},
    "enabled": false
  },
  "archon": {
    "transport": "streamable_http",
    "url": "http://localhost:3000/mcp",
    "headers": {},
    "enabled": false
  }
}
```

### 4. CLI Wizard (`src/cli/mcp_commands.py`)

**Enhanced `/mcp add` command:**

1. **Transport Type Selection:** New step asks user to choose:
   - Stdio (local subprocess)
   - Streamable HTTP (production)
   - SSE (legacy)

2. **Branched Configuration Flow:**
   - **Stdio path:** Asks for command, args, env vars
   - **HTTP/SSE path:** Asks for URL, headers

3. **Validation:** Ensures required fields for each transport type

**Example user flow:**
```
Select transport type:
  1. Stdio - Local subprocess (command + args)
  2. Streamable HTTP - HTTP endpoint (production)
  3. SSE - Server-Sent Events (legacy)

Transport [1/2/3]: 2

Server URL (http:// or https://): https://api.example.com/mcp

HTTP headers (optional, format: Header-Name: value):
Header: Authorization: Bearer ${API_KEY}
Header: 

✅ Added streamable_http server: example
```

### 5. Test Coverage

**Created `test_transport_types.py`:**
- Tests all three transport type configs
- Validates transport-specific field requirements
- Tests backward compatibility (auto-detection)
- Verifies mcp_config.json loads correctly

**Created `test_cli_transports.py`:**
- Tests MCP client manager loads correct server classes
- Tests agent initialization with mixed transports
- Tests system prompt generation includes MCP info

**Results:**
```
✅ PASS - Config Models
✅ PASS - MCP Config File  
✅ PASS - Backward Compatibility
✅ PASS - MCP Loading
✅ PASS - Agent Initialization
✅ PASS - System Prompt Generation
```

## Backward Compatibility

**Legacy configs without `transport` field automatically detected:**
- Config with `command` field → stdio
- Config with `url` field → streamable_http
- Config with neither → defaults to stdio

**No breaking changes for existing configurations.**

## Files Modified

| File | Lines Changed | Summary |
|------|--------------|---------|
| `src/mcp/config.py` | ~80 | Added TransportType enum, updated MCPServerConfig model, validation |
| `src/mcp/client.py` | ~60 | Rewrote _load_server() to support all transports, updated imports |
| `src/cli/mcp_commands.py` | ~120 | Enhanced /mcp add wizard with transport selection |
| `mcp_config.json` | ~10 | Added transport field to all servers |

## Files Created

| File | Purpose |
|------|---------|
| `test_transport_types.py` | Unit tests for transport type support |
| `test_cli_transports.py` | Integration tests for CLI with transports |
| `TRANSPORT_TYPES_IMPLEMENTATION.md` | This document |

## Known Limitations

1. **SSE transport support:** Fully implemented but SSE is deprecated per MCP spec
2. **HTTP authentication:** Basic header support only, no OAuth flow
3. **No HTTP server examples:** microsoft.docs.mcp and archon disabled (endpoints may not exist)

## Next Steps

1. ✅ **DONE:** Implement transport type support
2. ✅ **DONE:** Update CLI wizard
3. ✅ **DONE:** Test with stdio servers
4. 🔄 **TODO:** Find/test with actual HTTP MCP server
5. 🔄 **TODO:** Update documentation (`docs/mcp-add-guide.md`)
6. 🔄 **TODO:** Implement thinking mode (Shift+Tab toggle)
7. 🔄 **TODO:** Integrate web search (Brave Search MCP + built-in)
8. 🔄 **TODO:** Implement RAG search with SQL Server 2025 vectors

## References

- **MCP Specification:** Transport types (stdio, streamable HTTP, SSE)
- **Pydantic AI MCP:** `MCPServerStdio`, `MCPServerStreamableHTTP`, `MCPServerSSE`
- **GitHub Issue:** User identified missing HTTP transport support
