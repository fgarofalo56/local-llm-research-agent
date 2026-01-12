# Streamlit UI Testing Guide

## Fix Applied

The Streamlit UI chat was failing because it wasn't properly managing MCP server sessions. This has been fixed by adding `async with agent:` context managers, matching the CLI implementation pattern.

## Changes Made

**File:** `src/ui/streamlit_app.py`

### Streaming Mode (line 611-627)
Added context manager wrapper:
```python
async def stream_response():
    nonlocal full_response
    # Establish MCP session for this conversation
    async with agent:
        async for chunk in agent.chat_stream(prompt):
            full_response += chunk
            status_placeholder.empty()
            response_placeholder.markdown(full_response + "▌")
```

### Non-Streaming Mode (line 628-638)
Added context manager wrapper:
```python
async def chat_with_session():
    # Establish MCP session for this conversation
    async with agent:
        return await agent.chat_with_details(prompt)

detailed_response = run_async(chat_with_session())
```

## Testing Instructions

### Quick Start (Automated)

1. **Check system status:**
   ```bash
   check-status.bat
   ```

2. **Start all services:**
   ```bash
   start-all.bat
   ```
   This will:
   - Check if Ollama is running (prompt to start if not)
   - Start Docker services (SQL Server 2022/2025 + Redis)
   - Wait for services to initialize

3. **Run Streamlit UI:**
   ```bash
   test-streamlit.bat
   ```
   This will launch Streamlit at http://localhost:8501

### Manual Testing Steps

#### Step 1: Start Ollama
```bash
# In a separate terminal
ollama serve

# Verify it's running
curl http://localhost:11434/api/tags
```

#### Step 2: Start Docker Services
```bash
# From project root
docker-compose -f docker\docker-compose.yml --env-file .env up -d

# Verify containers are running
docker ps --filter "name=local-agent"
```

Expected containers:
- `local-agent-mssql` (port 1433) - Sample database
- `local-agent-mssql-backend` (port 1434) - Backend database
- `local-agent-redis` (port 6379) - Cache + vectors

#### Step 3: Run Streamlit
```bash
uv run streamlit run src\ui\streamlit_app.py
```

Access at: http://localhost:8501

### Test Cases

#### Test 1: Basic Chat (Non-Streaming)
1. Uncheck "Streaming responses" in sidebar
2. Send message: "Hello, can you help me?"
3. ✅ Should get a response without errors
4. ✅ Response should appear all at once

#### Test 2: Streaming Chat
1. Check "Streaming responses" in sidebar
2. Send message: "What can you do?"
3. ✅ Should see response stream in character by character
4. ✅ Should see cursor (▌) while streaming
5. ✅ Should see token usage stats at the end

#### Test 3: Database Query (MCP Tools)
**Prerequisites:** Docker SQL Server must be running

1. Send message: "What tables are in the database?"
2. ✅ Should list tables from ResearchAnalytics DB
3. ✅ No errors about MCP connections
4. ✅ Response should include table names

Example expected response:
```
The database contains the following tables:
- Departments
- Researchers
- Projects
- Publications
- Datasets
- Experiments
- Funding
- Equipment
```

#### Test 4: Complex Database Query
1. Send message: "Show me the top 5 researchers by publication count"
2. ✅ Should execute SQL query via MCP
3. ✅ Should return results with names and counts
4. ✅ Should complete without errors

#### Test 5: Provider Selection
1. Change provider in sidebar (if Foundry Local is available)
2. Click "Apply Settings"
3. Send message: "Test message"
4. ✅ Should work with new provider
5. ✅ Should show correct provider in sidebar

#### Test 6: Cache Functionality
1. Enable "Response caching" in sidebar
2. Send message: "What is 2+2?"
3. Note the response time
4. Send same message again
5. ✅ Second response should be instant (cached)
6. ✅ Cache stats should show hit rate > 0

#### Test 7: Error Handling
1. Stop Ollama (Ctrl+C in terminal)
2. Try to send a message in Streamlit
3. ✅ Should show clear error message
4. ✅ UI should remain responsive
5. Restart Ollama
6. ✅ Next message should work

### Verification Checklist

- [ ] Ollama is running (port 11434)
- [ ] Docker services are running (ports 1433, 1434, 6379)
- [ ] Streamlit starts without import errors
- [ ] Can send messages in non-streaming mode
- [ ] Can send messages in streaming mode
- [ ] Database queries work (MCP tools execute)
- [ ] Token usage stats display correctly
- [ ] Provider selection works
- [ ] Cache functionality works
- [ ] Error messages are clear and helpful
- [ ] UI remains responsive after errors

### Troubleshooting

#### "Ollama is not available"
```bash
# Start Ollama
ollama serve

# Check it's responding
curl http://localhost:11434/api/tags
```

#### "MCP not configured"
Check `.env` file has:
```
MCP_MSSQL_PATH=E:/path/to/SQL-AI-samples/MssqlMcp/Node/dist/index.js
```

#### "Database connection failed"
```bash
# Check SQL Server containers
docker ps | findstr mssql

# Restart if needed
docker-compose -f docker\docker-compose.yml --env-file .env restart mssql
```

#### Import errors
```bash
# Reinstall dependencies
uv sync

# Or with pip
pip install -r requirements.txt
```

#### Port conflicts
```bash
# Check what's using the ports
netstat -an | findstr "1433 1434 8501 11434"

# Kill processes if needed, then restart
```

### Performance Expectations

- **Startup time:** 2-3 seconds for Streamlit
- **First message:** 2-5 seconds (MCP initialization)
- **Subsequent messages:** 1-3 seconds
- **Streaming chunks:** ~20 characters every 0.1s
- **Cached responses:** < 100ms

### Success Criteria

✅ **PASS** if:
- Chat works in both streaming and non-streaming modes
- Database queries execute successfully via MCP tools
- No errors in Streamlit console
- Token usage displays correctly
- Cache functionality works
- Provider switching works

❌ **FAIL** if:
- Chat hangs or times out
- MCP connection errors appear
- Database queries don't work
- Errors in Streamlit console
- UI becomes unresponsive

## Automated Test Scripts

Three batch scripts are provided for Windows:

1. **check-status.bat** - Check if all services are running
2. **start-all.bat** - Start Docker services and check Ollama
3. **test-streamlit.bat** - Launch Streamlit UI with checks

### Usage Example
```bash
# Terminal 1: Start Ollama
ollama serve

# Terminal 2: Start services and Streamlit
start-all.bat
test-streamlit.bat
```

## Integration with CLI

The fix aligns Streamlit with the CLI implementation:

**CLI pattern** (`src/cli/chat.py` line 348):
```python
async with agent:
    while True:
        # Chat loop with persistent MCP sessions
```

**Streamlit pattern** (now fixed):
```python
async with agent:
    result = await agent.chat_stream(message)
```

Both now properly manage MCP server lifecycles.

## Next Steps After Testing

If testing is successful:
1. Update README.md with testing instructions
2. Add integration tests for Streamlit UI
3. Document the context manager pattern in CLAUDE.md
4. Create example video/screenshots of working UI

## Reporting Issues

If you encounter issues:
1. Run `check-status.bat` and share output
2. Check Streamlit console for errors
3. Check Docker logs: `docker logs local-agent-mssql`
4. Check Ollama logs in the terminal where it's running
5. Share the full error message and stack trace
