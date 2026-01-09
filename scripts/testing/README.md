# Integration Testing Scripts

Integration and system-level test scripts for MCP, transports, and agent functionality.

## Scripts

### MCP Testing
- `test_mcp_commands.py` - Test MCP server command execution
- `test_mcp_context.py` - Test MCP context management
- `test_agent_mcp_visibility.py` - Verify agent can see MCP tools
- `test_agent_tools.py` - Test agent tool calling

### Transport Testing
- `test_transport_types.py` - Test stdio, HTTP, SSE transports
- `test_cli_transports.py` - CLI with different transport types
- `test_http_sse_servers.py` - HTTP and SSE server testing
- `test_universal_agent.py` - Universal agent with all transports

### Session Management
- `test_session_fix.py` - Verify persistent MCP sessions
- `test_cli_session_debug.py` - Debug CLI session behavior

### Quick Tests
- `test_cli_quick.py` - Quick CLI functionality check
- `test_tool_visibility.py` - Tool visibility verification

## Usage

```bash
# Run individual test
uv run python scripts/testing/test_session_fix.py

# Run with pytest (if pytest-compatible)
uv run pytest scripts/testing/test_session_fix.py -v

# Run from inside directory
cd scripts/testing
uv run python test_session_fix.py
```

## Difference from tests/

| Directory | Purpose | Style |
|-----------|---------|-------|
| `tests/` | Unit & integration tests | Formal pytest suite, fixtures, mocks |
| `scripts/testing/` | System-level testing | Standalone scripts, full stack, debug output |
| `examples/` | Usage demonstrations | Educational, best practices |

## When to Use

- Testing full MCP server integration
- Verifying transport implementations work
- Debugging session management issues
- Testing with real databases and services
- Manual verification of complex scenarios

## Note

These scripts typically require:
- Docker services running (SQL Server, Redis)
- Ollama running with models pulled
- MCP servers configured in mcp_config.json
