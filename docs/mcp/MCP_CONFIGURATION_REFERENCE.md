# MCP Server Configuration - Quick Reference

## Currently Configured Servers

### Local Servers (Stdio Transport)

**1. MSSQL Server**
- **Command:** `node ${MCP_MSSQL_PATH}`
- **Tools:** list_tables, describe_table, read_data, insert_data, update_data, etc.
- **Database:** ResearchAnalytics on localhost:1433

**2. Analytics Management** 
- **Command:** `uv run python -m src.mcp.analytics_mcp_server`
- **Tools:** Dashboard and widget management
- **Database:** LLM_BackEnd on localhost:1434

**3. Data Analytics**
- **Command:** `uv run python -m src.mcp.data_analytics_mcp_server`
- **Tools:** Statistical analysis, time series, anomaly detection
- **Databases:** ResearchAnalytics (sample data) + LLM_BackEnd (results storage)

**4. Archon (via Docker)**
- **Command:** `docker exec -i archon-mcp python -m mcp_server`
- **Tools:** RAG search, project management, task tracking, document management
- **Container:** archon-mcp (port 8051)

### Remote Server (Streamable HTTP)

**5. Microsoft Learn MCP**
- **URL:** `https://learn.microsoft.com/api/mcp`
- **Transport:** Streamable HTTP (MCP protocol over HTTPS)
- **Tools:** Search Microsoft Learn, get code examples, Azure documentation
- **Authentication:** None required (public endpoint)

## Testing Commands

### Check Configuration
```powershell
cd E:\Repos\GitHub\MyDemoRepos\local-llm-research-agent

# List enabled servers
uv run python -c "from src.mcp.client import MCPClientManager; m = MCPClientManager('mcp_config.json'); [print(f'{s.name}: {s.transport.value}') for s in m.load_config().get_enabled_servers()]"
```

### Start CLI
```powershell
uv run python -m src.cli.chat
```

### CLI Commands
```
/mcp list               # Show all configured servers
/mcp status            # Show server health
/mcp tools             # List all available tools
/mcp tools archon      # List tools for specific server
```

## Example Queries

### Using MSSQL
```
What tables are in the ResearchAnalytics database?
Show me the top 10 researchers by publication count
```

### Using Archon RAG
```
Search the knowledge base for "claude agents sdk"
What documentation do we have about pydantic AI?
Find examples of MCP server implementation
```

### Using Microsoft Learn
```
Search Microsoft Learn for FastAPI tutorials
Find Azure documentation about Container Apps
Get examples of Azure Functions with Python
```

### Using Analytics Tools
```
Create a dashboard to track researcher performance
Analyze publication trends over the last year
Show time series of project funding
```

## Transport Types Explained

### Stdio (Local Subprocess)
- **How:** Spawns local process, communicates via stdin/stdout
- **Use Case:** Local tools, Node.js/Python MCP servers
- **Examples:** mssql, analytics-management, data-analytics, archon (via Docker)
- **Pros:** Fast, secure, full control
- **Cons:** Must be installed locally or accessible via Docker

### Streamable HTTP (Remote Endpoint)
- **How:** HTTP POST requests with MCP protocol
- **Use Case:** Remote services, public APIs, enterprise tools
- **Examples:** Microsoft Learn MCP
- **Pros:** No local installation, scalable, accessible anywhere
- **Cons:** Network dependency, potential latency

### SSE (Legacy, not currently used)
- **How:** Server-Sent Events over HTTP
- **Use Case:** Real-time updates, streaming responses
- **Status:** Deprecated by MCP spec, use Streamable HTTP instead

## Configuration File Location

**File:** `mcp_config.json` (project root)

**Structure:**
```json
{
  "mcpServers": {
    "server-name": {
      "name": "server-name",
      "server_type": "custom",
      "transport": "stdio|streamable_http|sse",
      "command": "...",     // For stdio
      "args": [...],        // For stdio
      "env": {...},         // For stdio
      "url": "...",         // For HTTP/SSE
      "headers": {...},     // For HTTP/SSE
      "enabled": true,
      "timeout": 30
    }
  }
}
```

## Adding New MCP Servers

### Using CLI Wizard
```
/mcp add
```

Follow prompts to:
1. Choose server type (MSSQL, PostgreSQL, Custom, etc.)
2. Choose transport (stdio, streamable_http, sse)
3. Enter connection details (command/URL)
4. Configure options

### Manual Configuration
1. Edit `mcp_config.json`
2. Add server entry under `mcpServers`
3. Restart CLI

## Troubleshooting

### Server Won't Load
1. Check `/mcp status` for error messages
2. Verify command/URL is correct
3. Check logs in CLI output
4. Test manually:
   - Stdio: Run command directly
   - HTTP: Test with curl/httpx

### Tools Not Showing
1. Ensure server is enabled: `"enabled": true`
2. Restart CLI after config changes
3. Check `/mcp tools server-name`

### Archon Connection Issues
1. Verify container is running: `docker ps | Select-String archon`
2. Test manually: `docker exec -i archon-mcp python -m mcp_server`
3. Check container logs: `docker logs archon-mcp`

### Microsoft Learn Connection Issues
1. Check internet connectivity
2. Verify HTTPS access to learn.microsoft.com
3. Test with: `Invoke-WebRequest https://learn.microsoft.com`
4. Check firewall settings

## Best Practices

1. **Keep servers disabled when not in use** - Reduces startup time
2. **Use descriptive names** - Makes tools easier to identify
3. **Set appropriate timeouts** - Longer for remote servers
4. **Document custom servers** - Add good descriptions
5. **Test incrementally** - Enable one server at a time when troubleshooting

## Next Steps

✅ **Configuration is complete** - All 5 servers configured  
🧪 **Ready to test** - Start CLI and try example queries  
📚 **Explore tools** - Use `/mcp tools` to see what's available  
🔧 **Add more servers** - Use `/mcp add` to expand capabilities
