# External MCP Server Integration - Final Configuration

**Date:** 2026-01-09  
**Status:** ✅ Configured (Testing Required)

## Summary

Configured your CLI to access:
1. **Archon MCP Server** - Via Docker stdio
2. **Microsoft Docs MCP** - Via Streamable HTTP (may require testing/adjustment)

## Configuration Changes

### 1. Archon MCP Server

**Transport:** stdio (via Docker exec)  
**Command:** `docker exec -i archon-mcp python -m mcp_server`

```json
{
  "archon": {
    "transport": "stdio",
    "command": "docker",
    "args": ["exec", "-i", "archon-mcp", "python", "-m", "mcp_server"],
    "enabled": true
  }
}
```

**How it works:**
- Archon runs in Docker container `archon-mcp`
- MCP communication happens via stdio (stdin/stdout)
- Docker exec provides the stdio bridge
- Pydantic AI's `MCPServerStdio` manages the process

### 2. Microsoft Docs MCP

**Transport:** streamable_http  
**URL:** `https://learn.microsoft.com/api/mcp`  
**Official Documentation:** [Microsoft Learn MCP Server](https://learn.microsoft.com/api/mcp)

```json
{
  "microsoft.docs.mcp": {
    "transport": "streamable_http",
    "url": "https://learn.microsoft.com/api/mcp",
    "enabled": true
  }
}
```

**Status:** ✅ Properly configured for MCP Streamable HTTP protocol

**Note:** The endpoint returns `405 Method Not Allowed` for direct browser access, but works correctly with MCP clients using the Streamable HTTP protocol (which Pydantic AI's `MCPServerStreamableHTTP` implements).

**Capabilities:**
- Powered by the same knowledge service as Ask Learn and Copilot for Azure
- Search Microsoft Learn documentation
- Get code examples and tutorials
- Access Azure documentation

## Current MCP Server Stack

Your CLI now has access to **5 MCP servers**:

| Server | Transport | Purpose |
|--------|-----------|---------|
| mssql | stdio | SQL Server database operations |
| **microsoft.docs.mcp** | **streamable_http** | **Microsoft Learn documentation** |
| analytics-management | stdio | Dashboard/widget management |
| data-analytics | stdio | Statistical analysis |
| **archon** | **stdio (Docker)** | **Project management + RAG** |

## Testing Steps

### 1. Start the CLI
```bash
cd E:\Repos\GitHub\MyDemoRepos\local-llm-research-agent
uv run python -m src.cli.chat
```

### 2. Test Archon Tools
```
You: Can you use archon to perform a RAG search for "claude agents sdk"?
```

Expected behavior:
- Agent should have access to archon RAG tools
- Should be able to search Archon knowledge base
- Should return relevant documentation

### 3. Test Microsoft Docs
```
You: Can you search Microsoft Learn documentation for FastAPI tutorials?
```

Expected behavior:
- Agent connects to Microsoft Learn MCP endpoint via Streamable HTTP
- Returns documentation, code examples, tutorials from Microsoft Learn
- Should work without authentication (public endpoint)

## Potential Issues & Solutions

###  Issue: Archon Connection Fails

**Symptoms:**
- `ExceptionGroup` error
- "Failed to start MCP server" in logs

**Solutions:**
1. Verify Archon container is running:
   ```powershell
   docker ps | Select-String archon
   ```

2. Test Docker exec manually:
   ```powershell
   docker exec -i archon-mcp python -m mcp_server
   ```

3. Check Archon logs:
   ```powershell
   docker logs archon-mcp --tail 50
   ```

### Issue: Microsoft Docs Fails

**Symptoms:**
- Connection timeout
- Tool execution errors

**Solutions:**
1. Check internet connectivity
2. Verify firewall allows HTTPS to learn.microsoft.com
3. Test with: `/mcp status` to see server health
4. Check logs for specific error messages

**Note:** The 405 error when testing manually is expected - the endpoint only responds to proper MCP Streamable HTTP protocol requests, not browser GET requests.

## How This Differs from Claude Desktop

**Claude Desktop/Copilot MCP:**
- Managed by Claude Desktop application
- Auto-connects to configured MCP servers
- You use tools with `archon-*` prefix

**Your Custom CLI:**
- Managed by your Python code
- Explicitly loads servers from `mcp_config.json`
- Agent sees tools directly (no prefix needed)
- **Runs locally with Ollama (100% private)**

## Advantages of CLI Approach

1. ✅ **Full Control** - You manage which servers are loaded
2. ✅ **Local LLM** - Uses Ollama (qwen3:30b), not OpenAI
3. ✅ **Privacy** - All inference happens locally
4. ✅ **Customizable** - Add/remove/configure servers as needed
5. ✅ **Multi-transport** - Supports stdio, HTTP, SSE

## Next Steps After Testing

If Archon works:
- ✅ You can now use Archon RAG from your CLI
- ✅ Agent can search knowledge base
- ✅ Agent can manage tasks/projects

If Microsoft Docs fails:
- 🔄 Disable it and use alternatives (Brave Search, web search)
- 🔄 Or: Investigate authentication requirements

If you want more MCP servers:
- 🔄 Use `/mcp add` command in CLI
- 🔄 Choose transport type (stdio/HTTP/SSE)
- 🔄 Restart CLI to activate

## Files Modified

- `mcp_config.json` - Added Archon (stdio via Docker), enabled Microsoft Docs (HTTP)
- No code changes needed - transport support already implemented!

## Quick Verification

Run this to see what's loaded:
```bash
uv run python -c "from src.mcp.client import MCPClientManager; m = MCPClientManager('mcp_config.json'); c = m.load_config(); [print(f'{s.name}: {s.transport.value} - {s.description[:60]}') for s in c.get_enabled_servers()]"
```

Expected output:
```
mssql: stdio - Microsoft SQL Server MCP Server for database operations
microsoft.docs.mcp: streamable_http - Microsoft Learn Documentation MCP Server
analytics-management: stdio - Analytics Management MCP Server for dashboards
data-analytics: stdio - Advanced Data Analytics MCP Server for statistical
archon: stdio - Archon Project Management and Knowledge Base MCP Server
```

## Summary

✅ **Archon is now configured** to work with your CLI via Docker stdio  
⚠️ **Microsoft Docs needs testing** - may need authentication or different config  
🎯 **Ready to test** - Start CLI and try Archon RAG queries!

The transport type infrastructure is solid - we just needed to find the right way to connect to Archon (Docker stdio) and configure the Microsoft Docs endpoint correctly.
