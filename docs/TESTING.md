# Testing Guide - Universal Agent

## Quick Start (30 seconds)

```bash
# Quick verification test
uv run python test_cli_quick.py
```

**Expected output:** Three successful tests showing the agent can answer general questions and SQL questions.

---

## Test Scenarios

### 1. Quick Test (2 minutes)
**Purpose:** Verify core functionality fast

```bash
uv run python test_cli_quick.py
```

**Tests:**
- ✓ Agent with NO tools (general questions)
- ✓ Agent with SQL tools (general questions)
- ✓ Agent with SQL tools (SQL queries)

### 2. Full Test Suite (5 minutes)
**Purpose:** Comprehensive testing with Rich UI

```bash
uv run python test_universal_agent.py
```

**Tests:**
- General questions without tools
- Universal questions with SQL tools
- Multi-MCP server management
- Error handling with invalid servers
- Enable/disable server functionality

### 3. Interactive CLI (Manual Testing)
**Purpose:** Test the actual user interface

```bash
uv run python -m src.cli.chat
```

**Test prompts to try:**
```
# General questions (no SQL needed)
What is 2+2?
Explain Python in one sentence
List the first 10 Fibonacci numbers

# SQL questions (will use database tools)
What tables are in the database?
Show me the top 5 researchers
Describe the Projects table

# Exit
/quit
```

### 4. Streamlit Web UI (Visual Testing)
**Purpose:** Test web interface

```bash
uv run streamlit run src/ui/streamlit_app.py
```

Open: http://localhost:8501

**Test in browser:**
- Ask general questions
- Ask SQL questions
- Check conversation history
- Test different settings

### 5. MCP Server Management (Backend Testing)
**Purpose:** Verify multi-MCP infrastructure

```bash
# List configured servers
uv run python -c "
from src.mcp.client import MCPClientManager
mgr = MCPClientManager()
for s in mgr.list_servers():
    print(f'{s.name}: {s.server_type.value}, enabled={s.enabled}')
"

# Test active toolsets
uv run python -c "
from src.mcp.client import MCPClientManager
mgr = MCPClientManager()
toolsets = mgr.get_active_toolsets()
print(f'Loaded {len(toolsets)} active MCP toolsets')
"
```

---

## What Was Changed?

### Before (SQL-only)
- Agent only worked with SQL Server queries
- Crashed on non-SQL questions
- Single MCP server (hardcoded)
- No multi-server support

### After (Universal Assistant)
- ✅ Answers ANY question type
- ✅ Graceful error handling
- ✅ Multiple simultaneous MCP servers
- ✅ Dynamic server management
- ✅ Works with 0+ tools loaded

---

## Key Features Tested

### 1. Universal Question Handling
```python
# Now works WITHOUT requiring SQL tools
agent = ResearchAgent(mcp_servers=[])
response = await agent.chat("What is Python?")
# Returns: "Python is a high-level programming language..."
```

### 2. Multi-MCP Support
```python
# Load multiple servers simultaneously
agent = ResearchAgent(mcp_servers=["mssql", "analytics-management"])
# Agent has access to tools from BOTH servers
```

### 3. Graceful Degradation
```python
# If a server fails to load, agent continues
agent = ResearchAgent(mcp_servers=["mssql", "nonexistent"])
# Logs warning but still works with available tools
```

### 4. Dynamic Server Management
```python
manager = MCPClientManager()
manager.add_server(brave_search_config)
manager.enable_server("brave_search")
manager.disable_server("analytics-management")
toolsets = manager.get_active_toolsets()  # Only enabled servers
```

---

## Troubleshooting

### Test fails with "No module named 'src'"
```bash
# Make sure you're in project root
cd E:\Repos\GitHub\MyDemoRepos\local-llm-research-agent
uv run python test_cli_quick.py
```

### Ollama connection errors
```bash
# Verify Ollama is running
curl http://localhost:11434/api/tags

# Check model is available
ollama list | grep qwen3:30b
```

### SQL Server connection errors
```bash
# Verify SQL Server is running
docker ps | grep mssql

# Test connection
sqlcmd -S localhost,1433 -U sa -P "LocalLLM@2024!" -Q "SELECT @@VERSION"
```

### MCP server loading warnings
Check the log output for:
- `mcp_server_loaded` - Server loaded successfully ✅
- `skipping_http_server` - HTTP servers not yet supported (expected)
- `mcp_toolset_load_failed` - Check server configuration

---

## Next Steps

After verifying tests pass:

1. **Review code changes:**
   - `src/agent/prompts.py` - Universal system prompts
   - `src/agent/core.py` - Multi-toolset support
   - `src/mcp/config.py` - Configuration models (NEW)
   - `src/mcp/client.py` - Enhanced manager

2. **Continue implementation:**
   - `/mcp` CLI commands for server management
   - Web search integration
   - RAG search with hybrid scoring
   - Thinking mode with Shift+Tab

3. **Documentation:**
   - Update README.md
   - Add usage examples
   - Create architecture diagrams

---

## Success Criteria

✅ **All tests should show:**
- Agent answers general questions without SQL tools
- Agent uses SQL tools only when appropriate
- Multiple MCP servers load successfully
- Failed servers don't break the agent
- Enable/disable operations work

If all tests pass, the foundation is solid for the next phase!
