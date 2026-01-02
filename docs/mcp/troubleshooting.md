# MCP Server Troubleshooting Guide

> **Solutions for common MCP server issues and error messages**

---

## Table of Contents

- [Quick Diagnostics](#quick-diagnostics)
- [Connection Issues](#connection-issues)
- [Authentication Errors](#authentication-errors)
- [Server Startup Problems](#server-startup-problems)
- [Tool Execution Errors](#tool-execution-errors)
- [Performance Issues](#performance-issues)
- [Configuration Problems](#configuration-problems)
- [Platform-Specific Issues](#platform-specific-issues)
- [Advanced Debugging](#advanced-debugging)

---

## Quick Diagnostics

### Health Check Checklist

Run through this checklist first:

```bash
# 1. Check Node.js/Python version
node --version    # Should be v18+ for Node.js servers
python --version  # Should be 3.11+ for Python servers

# 2. Check MCP server file exists
ls "E:\path\to\SQL-AI-samples\MssqlMcp\Node\dist\index.js"  # Windows
ls /path/to/SQL-AI-samples/MssqlMcp/Node/dist/index.js     # Linux/Mac

# 3. Check SQL Server is running (Docker)
docker ps | grep mssql

# 4. Test SQL Server connection
sqlcmd -S localhost -d ResearchAnalytics -U sa -P "LocalLLM@2024!" -Q "SELECT 1"

# 5. Check environment variables loaded
env | grep SQL_    # Linux/Mac
Get-ChildItem Env:SQL_*  # Windows PowerShell

# 6. Test API health
curl http://localhost:8000/api/health

# 7. Check MCP server status
curl http://localhost:8000/api/mcp
```

### Quick Fix Commands

```bash
# Restart SQL Server (Docker)
docker-compose -f docker/docker-compose.yml --env-file .env restart mssql

# Restart API backend
# Press Ctrl+C to stop, then:
uv run uvicorn src.api.main:app --reload

# Clear Python cache
find . -type d -name __pycache__ -exec rm -rf {} +  # Linux/Mac
Get-ChildItem -Recurse -Directory __pycache__ | Remove-Item -Recurse -Force  # Windows

# Rebuild MCP server (Node.js)
cd SQL-AI-samples/MssqlMcp/Node
npm run build
```

---

## Connection Issues

### Error: "MCP_MSSQL_PATH is not set"

**Symptom:**
```
ValueError: MSSQL MCP configuration errors:
  - MCP_MSSQL_PATH is not set
```

**Cause:** Environment variable not configured

**Solution:**

```bash
# 1. Check .env file exists
ls .env

# 2. Add MCP_MSSQL_PATH to .env
echo 'MCP_MSSQL_PATH=E:\SQL-AI-samples\MssqlMcp\Node\dist\index.js' >> .env

# 3. Verify variable is set
grep MCP_MSSQL_PATH .env

# 4. Restart application
```

---

### Error: "MCP_MSSQL_PATH does not exist"

**Symptom:**
```
ValueError: MSSQL MCP configuration errors:
  - MCP_MSSQL_PATH does not exist: E:\path\to\index.js
```

**Cause:**
- Incorrect path
- Server not built
- File deleted

**Solution:**

```bash
# 1. Check if file exists
test -f "$MCP_MSSQL_PATH" && echo "Found" || echo "Not found"  # Linux/Mac
Test-Path $env:MCP_MSSQL_PATH  # Windows PowerShell

# 2. Find the correct path
find ~/SQL-AI-samples -name index.js 2>/dev/null  # Linux/Mac
Get-ChildItem -Path C:\SQL-AI-samples -Recurse -Filter index.js  # Windows

# 3. Rebuild if missing
cd SQL-AI-samples/MssqlMcp/Node
npm install
npm run build

# 4. Verify build succeeded
ls dist/index.js

# 5. Update .env with correct path
# Edit .env and set MCP_MSSQL_PATH to the full absolute path
```

---

### Error: "Connection timeout"

**Symptom:**
```
MCPTimeoutError: MSSQL server connection timed out
```

**Cause:**
- SQL Server not running
- Network issue
- Firewall blocking connection
- Server overloaded

**Solution:**

```bash
# 1. Check SQL Server is running
docker ps -a | grep mssql

# 2. Start SQL Server if stopped
docker-compose -f docker/docker-compose.yml --env-file .env up -d mssql

# 3. Check port is accessible
telnet localhost 1433    # Linux/Mac
Test-NetConnection -ComputerName localhost -Port 1433  # Windows PowerShell

# 4. Increase timeout in .env
echo 'MCP_TIMEOUT=60' >> .env

# 5. Check SQL Server logs
docker logs local-agent-mssql

# 6. Test connection manually
sqlcmd -S localhost -d ResearchAnalytics -U sa -P "LocalLLM@2024!" -Q "SELECT 1"
```

---

### Error: "Connection refused"

**Symptom:**
```
ConnectionError: [Errno 111] Connection refused
```

**Cause:** SQL Server not accepting connections

**Solution:**

```bash
# 1. Verify SQL Server container is running
docker ps | grep mssql

# 2. Check container logs for errors
docker logs local-agent-mssql --tail 50

# 3. Restart SQL Server
docker restart local-agent-mssql

# 4. Wait for startup (check logs)
docker logs -f local-agent-mssql
# Wait for: "SQL Server is now ready for client connections"

# 5. Verify port mapping
docker port local-agent-mssql
# Should show: 1433/tcp -> 0.0.0.0:1433

# 6. Test connection
sqlcmd -S localhost,1433 -U sa -P "LocalLLM@2024!" -Q "SELECT 1"
```

---

## Authentication Errors

### Error: "Login failed for user 'sa'"

**Symptom:**
```
Login failed for user 'sa'. Reason: Password did not match that for the login provided.
```

**Cause:** Incorrect password or username

**Solution:**

```bash
# 1. Check .env file for credentials
grep SQL_USERNAME .env
grep SQL_PASSWORD .env

# 2. Verify Docker container password
grep MSSQL_SA_PASSWORD .env

# 3. Test credentials manually
sqlcmd -S localhost -U sa -P "LocalLLM@2024!" -Q "SELECT 1"

# 4. If password is wrong, reset SQL Server
docker-compose -f docker/docker-compose.yml down -v
docker-compose -f docker/docker-compose.yml --env-file .env up -d mssql

# 5. Wait for startup
sleep 30

# 6. Re-initialize database
docker-compose -f docker/docker-compose.yml --env-file .env --profile init up mssql-tools
```

---

### Error: "Certificate chain was issued by an authority that is not trusted"

**Symptom:**
```
SSL Provider: The certificate chain was issued by an authority that is not trusted
```

**Cause:** Self-signed certificate not trusted

**Solution:**

```bash
# 1. Enable trust for self-signed certificates in .env
SQL_TRUST_SERVER_CERTIFICATE=true

# 2. Verify setting is applied
grep SQL_TRUST_SERVER_CERTIFICATE .env

# 3. For production Azure SQL, use proper certificate
SQL_TRUST_SERVER_CERTIFICATE=false
SQL_ENCRYPT=true

# 4. Restart application
```

---

### Error: "User does not have permission"

**Symptom:**
```
The user does not have permission to perform this action
```

**Cause:** Insufficient SQL Server permissions

**Solution:**

```sql
-- Connect as admin
sqlcmd -S localhost -U sa -P "LocalLLM@2024!"

-- Grant necessary permissions
USE ResearchAnalytics;
GO

-- For read-only access
GRANT SELECT ON SCHEMA::dbo TO [your_user];
GO

-- For read-write access
GRANT INSERT, UPDATE, DELETE ON SCHEMA::dbo TO [your_user];
GO

-- For schema management
GRANT CREATE TABLE, ALTER, DROP ON SCHEMA::dbo TO [your_user];
GO

-- Verify permissions
SELECT * FROM fn_my_permissions(NULL, 'DATABASE');
GO
```

---

### Error: "Azure AD authentication failed"

**Symptom:**
```
Failed to acquire token for Azure AD authentication
```

**Cause:** Azure AD credentials not configured or expired

**Solution:**

```bash
# 1. For interactive auth, ensure Azure CLI is logged in
az login
az account show

# 2. For service principal, verify credentials
echo $AZURE_TENANT_ID
echo $AZURE_CLIENT_ID
echo $AZURE_CLIENT_SECRET

# 3. Test Azure AD token acquisition
az account get-access-token --resource https://database.windows.net/

# 4. Verify service principal has access
az sql server show --name myserver --resource-group mygroup

# 5. Check SQL Server user exists
sqlcmd -S myserver.database.windows.net -d mydb -G -Q "SELECT USER_NAME()"

# 6. If user missing, create in SQL
CREATE USER [your-app-name] FROM EXTERNAL PROVIDER;
ALTER ROLE db_datareader ADD MEMBER [your-app-name];
GO
```

---

## Server Startup Problems

### Error: "Node.js version too old"

**Symptom:**
```
Error: The engine "node" is incompatible with this module. Expected version ">=18.0.0"
```

**Cause:** Node.js version < 18

**Solution:**

```bash
# 1. Check current version
node --version

# 2. Update Node.js
# Option A: Download from https://nodejs.org/

# Option B: Use nvm (recommended)
nvm install 18
nvm use 18
nvm alias default 18

# 3. Verify update
node --version

# 4. Reinstall MCP server dependencies
cd SQL-AI-samples/MssqlMcp/Node
rm -rf node_modules package-lock.json
npm install
npm run build
```

---

### Error: "MODULE_NOT_FOUND"

**Symptom:**
```
Error: Cannot find module '@modelcontextprotocol/sdk'
```

**Cause:** Dependencies not installed

**Solution:**

```bash
# 1. Navigate to MCP server directory
cd SQL-AI-samples/MssqlMcp/Node

# 2. Remove old dependencies
rm -rf node_modules package-lock.json

# 3. Reinstall
npm install

# 4. Verify installation
npm list @modelcontextprotocol/sdk

# 5. Rebuild
npm run build

# 6. Test server
node dist/index.js
```

---

### Error: "Python module not found"

**Symptom:**
```
ModuleNotFoundError: No module named 'mcp'
```

**Cause:** MCP SDK not installed

**Solution:**

```bash
# 1. Activate virtual environment
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# 2. Install dependencies
pip install mcp anthropic-sdk pydantic

# 3. Verify installation
pip list | grep mcp

# 4. Test import
python -c "from mcp.server import Server; print('OK')"
```

---

### Error: "Server process crashed"

**Symptom:**
```
Server process exited unexpectedly with code 1
```

**Cause:**
- Syntax error in server code
- Missing environment variables
- Uncaught exception

**Solution:**

```bash
# 1. Run server directly to see error
node dist/index.js
# or
python server.py

# 2. Enable debug logging
DEBUG=* node dist/index.js

# 3. Check server logs
tail -f logs/mcp-server.log

# 4. Common fixes:
# - Check all required env vars are set
# - Verify file paths are correct
# - Check for syntax errors in custom code

# 5. Test with minimal config
# Comment out custom tools and test basic functionality
```

---

## Tool Execution Errors

### Error: "Tool not found"

**Symptom:**
```
Error: Unknown tool: search_data
```

**Cause:**
- Tool name misspelled
- Server not properly initialized
- Tool not registered

**Solution:**

```bash
# 1. List available tools
curl http://localhost:8000/api/mcp | jq '.servers[].tools'

# 2. Check tool registration in server code
grep "search_data" server.py  # or server.ts

# 3. Verify server is connected
# Check API logs for "mssql_server_connected" message

# 4. Test tools directly via MCP
echo '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}' | node dist/index.js
```

---

### Error: "Tool execution timeout"

**Symptom:**
```
TimeoutError: Tool execution exceeded timeout of 30 seconds
```

**Cause:**
- Complex query taking too long
- Database performance issue
- Network latency

**Solution:**

```bash
# 1. Increase timeout in .env
MCP_TIMEOUT=60

# 2. Optimize query
# Add indexes, use LIMIT, simplify conditions

# 3. Check database performance
sqlcmd -S localhost -U sa -P "LocalLLM@2024!" -Q "
SELECT TOP 10
    qs.execution_count,
    qs.total_elapsed_time / 1000000.0 AS total_elapsed_time_seconds,
    SUBSTRING(qt.text, 1, 200) AS query_text
FROM sys.dm_exec_query_stats qs
CROSS APPLY sys.dm_exec_sql_text(qs.sql_handle) qt
ORDER BY qs.total_elapsed_time DESC;
"

# 4. Monitor active queries
# While query is running:
sqlcmd -S localhost -U sa -P "LocalLLM@2024!" -Q "
SELECT session_id, status, command, wait_type, wait_time
FROM sys.dm_exec_requests
WHERE session_id > 50;
"
```

---

### Error: "Invalid tool arguments"

**Symptom:**
```
ValidationError: 1 validation error for SearchInput
  query
    field required (type=value_error.missing)
```

**Cause:** Missing or invalid input parameters

**Solution:**

```python
# 1. Check tool schema
# Look at inputSchema in tool definition

# 2. Provide all required fields
# Example:
result = await agent.run(
    "Search for files matching pattern *.py in the src directory"
)
# Agent should extract: query="*.py", path="src"

# 3. For custom servers, improve error messages
try:
    input_data = SearchInput(**arguments)
except ValidationError as e:
    return CallToolResult(
        content=[TextContent(
            type="text",
            text=f"Invalid input: {e.errors()}"
        )],
        isError=True
    )
```

---

## Performance Issues

### Problem: Slow responses

**Symptom:** Agent takes 30+ seconds to respond

**Causes and Solutions:**

```bash
# 1. Check if LLM is running locally
curl http://localhost:11434/api/tags  # Ollama
# Ensure model is loaded

# 2. Monitor LLM resource usage
# CPU/GPU should be active during inference

# 3. Check database query performance
# Enable query logging in SQL Server
sqlcmd -S localhost -U sa -P "LocalLLM@2024!" -Q "
DBCC TRACEON(1222, -1);  -- Deadlock tracing
"

# 4. Enable API request logging
LOG_LEVEL=DEBUG

# 5. Profile slow endpoints
# Add timing logs in code:
import time
start = time.time()
# ... operation ...
elapsed = time.time() - start
logger.info(f"Operation took {elapsed:.2f}s")

# 6. Use caching
CACHE_ENABLED=true
CACHE_TTL_SECONDS=3600
```

---

### Problem: High memory usage

**Symptom:** Application using excessive RAM

**Solution:**

```bash
# 1. Check Ollama model size
ollama list

# 2. Use smaller model
OLLAMA_MODEL=qwen2.5:7b-instruct  # Instead of larger models

# 3. Limit connection pool
SQL_POOL_SIZE=5

# 4. Monitor memory usage
docker stats

# 5. Increase Docker memory limit
# In Docker Desktop: Settings > Resources > Memory

# 6. Check for memory leaks
# Monitor over time, restart if growing unbounded
```

---

## Configuration Problems

### Error: "Environment variable not found"

**Symptom:**
```
KeyError: 'SQL_SERVER_HOST'
```

**Cause:** .env file not loaded or variable missing

**Solution:**

```bash
# 1. Verify .env file exists in project root
ls -la .env

# 2. Check variable is defined
grep SQL_SERVER_HOST .env

# 3. Test loading .env
python -c "
from dotenv import load_dotenv
import os
load_dotenv()
print(os.getenv('SQL_SERVER_HOST'))
"

# 4. Ensure .env is in same directory where you run commands
pwd  # Should be project root

# 5. For Docker, verify --env-file flag
docker-compose -f docker/docker-compose.yml --env-file .env config
# Check that variables are substituted
```

---

### Error: "Invalid JSON in mcp_config.json"

**Symptom:**
```
json.JSONDecodeError: Expecting property name enclosed in double quotes
```

**Cause:** Syntax error in JSON file

**Solution:**

```bash
# 1. Validate JSON syntax
python -m json.tool mcp_config.json

# 2. Common issues:
# - Trailing commas
# - Single quotes instead of double quotes
# - Missing brackets/braces
# - Comments (JSON doesn't support comments)

# 3. Use an editor with JSON validation
# VS Code, PyCharm, or online: https://jsonlint.com/

# 4. Example valid format:
cat > mcp_config.json << 'EOF'
{
  "mcpServers": {
    "mssql": {
      "command": "node",
      "args": ["path/to/index.js"],
      "env": {
        "SERVER_NAME": "localhost"
      }
    }
  }
}
EOF
```

---

## Platform-Specific Issues

### Windows: Path with spaces

**Problem:** MCP_MSSQL_PATH has spaces

**Solution:**

```bash
# Use quotes in .env
MCP_MSSQL_PATH="C:\Program Files\SQL-AI-samples\MssqlMcp\Node\dist\index.js"

# Or use short path
# Get short path:
dir /x "C:\Program Files"
# Then use: C:\PROGRA~1\...

# Or avoid spaces by installing to C:\SQL-AI-samples
```

---

### Windows: Backslash escaping

**Problem:** Paths with backslashes not working

**Solution:**

```bash
# Option 1: Use forward slashes (Windows accepts both)
MCP_MSSQL_PATH=C:/SQL-AI-samples/MssqlMcp/Node/dist/index.js

# Option 2: Escape backslashes
MCP_MSSQL_PATH=C:\\SQL-AI-samples\\MssqlMcp\\Node\\dist\\index.js

# Option 3: Use raw string in Python
path = r"C:\SQL-AI-samples\MssqlMcp\Node\dist\index.js"
```

---

### Linux/Mac: Permission denied

**Problem:**
```
PermissionError: [Errno 13] Permission denied: '/path/to/server.py'
```

**Solution:**

```bash
# 1. Make script executable
chmod +x server.py

# 2. Or run with python explicitly
python server.py

# 3. Check file ownership
ls -l server.py

# 4. Fix ownership if needed
sudo chown $USER:$USER server.py
```

---

### Docker: Port already in use

**Problem:**
```
Error: Bind for 0.0.0.0:1433 failed: port is already allocated
```

**Solution:**

```bash
# 1. Find what's using the port
sudo lsof -i :1433  # Linux/Mac
netstat -ano | findstr :1433  # Windows

# 2. Stop the conflicting service
sudo systemctl stop mssql-server  # Linux
net stop MSSQLSERVER  # Windows

# 3. Or change port in docker-compose.yml
ports:
  - "1435:1433"  # Use host port 1435 instead

# Then update .env:
SQL_SERVER_PORT=1435
```

---

## Advanced Debugging

### Enable Full Debug Logging

```bash
# .env
DEBUG=true
LOG_LEVEL=DEBUG
MCP_DEBUG=true

# Run with verbose output
uv run uvicorn src.api.main:app --reload --log-level debug

# Check all logs
tail -f logs/*.log
```

---

### Capture MCP Protocol Messages

```python
# Add to src/mcp/client.py

import sys
import json

class DebugWrapper:
    """Wrapper to log MCP protocol messages."""

    def __init__(self, stream):
        self.stream = stream

    def write(self, data):
        try:
            msg = json.loads(data)
            print(f"[MCP OUT] {json.dumps(msg, indent=2)}", file=sys.stderr)
        except:
            pass
        return self.stream.write(data)

    def read(self, size=-1):
        data = self.stream.read(size)
        try:
            msg = json.loads(data)
            print(f"[MCP IN] {json.dumps(msg, indent=2)}", file=sys.stderr)
        except:
            pass
        return data

# Use in server creation
server = MCPServerStdio(
    command="node",
    args=[path],
    env=env,
    stdin=DebugWrapper(sys.stdin),
    stdout=DebugWrapper(sys.stdout)
)
```

---

### Test MCP Server Isolation

```bash
# Test server standalone
export SERVER_NAME=localhost
export DATABASE_NAME=ResearchAnalytics
export AUTH_TYPE=sql
export SQL_USERNAME=sa
export SQL_PASSWORD="LocalLLM@2024!"
export TRUST_SERVER_CERTIFICATE=true

# Run and test manually
node dist/index.js

# Send test request
echo '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}' | node dist/index.js

# Check response
```

---

### SQL Server Query Profiling

```sql
-- Enable query store
ALTER DATABASE ResearchAnalytics SET QUERY_STORE = ON;
GO

-- View slow queries
SELECT TOP 10
    q.query_id,
    qt.query_sql_text,
    rs.avg_duration/1000.0 AS avg_duration_ms,
    rs.count_executions
FROM sys.query_store_query q
JOIN sys.query_store_query_text qt ON q.query_text_id = qt.query_text_id
JOIN sys.query_store_plan p ON q.query_id = p.query_id
JOIN sys.query_store_runtime_stats rs ON p.plan_id = rs.plan_id
ORDER BY rs.avg_duration DESC;
GO

-- Check active connections
SELECT
    session_id,
    login_name,
    host_name,
    program_name,
    status,
    last_request_start_time
FROM sys.dm_exec_sessions
WHERE is_user_process = 1;
GO
```

---

## Getting More Help

### Collect Diagnostic Information

Before asking for help, collect:

```bash
# 1. Version information
node --version
python --version
ollama --version
docker --version

# 2. Environment variables (sanitized)
env | grep -E "SQL_|MCP_|OLLAMA_" | sed 's/PASSWORD=.*/PASSWORD=***/'

# 3. Configuration files
cat mcp_config.json
cat .env | sed 's/PASSWORD=.*/PASSWORD=***/'

# 4. Recent logs
tail -n 100 logs/api.log
docker logs local-agent-mssql --tail 100

# 5. Health check output
curl http://localhost:8000/api/health
curl http://localhost:8000/api/mcp

# Save all to file
./collect-diagnostics.sh > diagnostics.txt
```

---

### Community Resources

- **GitHub Issues:** [Project Issues](https://github.com/your-repo/issues)
- **MCP Specification:** [modelcontextprotocol.io](https://modelcontextprotocol.io)
- **Pydantic AI Discussions:** [GitHub Discussions](https://github.com/pydantic/pydantic-ai/discussions)

---

## Didn't Find Your Issue?

1. **Check API logs:** `logs/api.log`
2. **Check Docker logs:** `docker logs local-agent-mssql`
3. **Enable debug mode:** Set `DEBUG=true` in `.env`
4. **Test components individually:** SQL Server, MCP server, API
5. **Open an issue:** Include diagnostic information above

---

*Last Updated: December 2024*
