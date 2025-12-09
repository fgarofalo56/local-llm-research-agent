# 🔧 Troubleshooting Guide

> **Common issues and solutions for the Local LLM Research Agent**

---

## 📑 Table of Contents

- [Quick Diagnostics](#-quick-diagnostics)
- [Ollama Issues](#-ollama-issues)
- [Database Issues](#-database-issues)
- [MCP Server Issues](#-mcp-server-issues)
- [Agent Issues](#-agent-issues)
- [Performance Issues](#-performance-issues)
- [Getting Help](#-getting-help)

---

## 🔍 Quick Diagnostics

Run these commands to quickly diagnose common issues:

### System Health Check

```bash
# Check Ollama
curl http://localhost:11434/api/tags

# Check Docker
docker ps | grep local-llm

# Check SQL Server connection
docker exec -it local-llm-mssql /opt/mssql-tools18/bin/sqlcmd \
  -S localhost -U sa -P "LocalLLM@2024!" -No -Q "SELECT 1"

# Check Python environment
python --version
uv pip list | grep pydantic
```

### Status Summary

| Component | Check Command | Expected Result |
|-----------|---------------|-----------------|
| Ollama | `curl localhost:11434` | JSON response |
| Docker | `docker ps` | Container running |
| SQL Server | `docker logs local-llm-mssql` | No errors |
| MCP Server | `node $MCP_MSSQL_PATH` | Server starts |

---

## 🦙 Ollama Issues

### Ollama Not Running

**Symptoms:**
- `Connection refused` errors
- Agent cannot process queries

**Solutions:**

```bash
# Start Ollama service
ollama serve

# Or restart Ollama app (Windows/Mac)
# Quit and reopen Ollama from system tray/menu bar
```

### Model Not Found

**Symptoms:**
- `model not found` error
- Agent fails to initialize

**Solutions:**

```bash
# List available models
ollama list

# Pull required model
ollama pull qwen2.5:7b-instruct

# Verify model works
ollama run qwen2.5:7b-instruct "Hello"
```

### Out of Memory

**Symptoms:**
- Ollama crashes during inference
- `CUDA out of memory` errors

**Solutions:**

| Option | Description |
|--------|-------------|
| Use smaller model | `ollama pull mistral:7b` |
| Close other apps | Free up VRAM |
| Reduce context | Set `num_ctx: 4096` |

```bash
# Try a smaller model
OLLAMA_MODEL=mistral:7b-instruct

# Or quantized version
ollama pull qwen2.5:7b-instruct-q4_K_M
```

### Slow Response

**Symptoms:**
- Long wait times for responses
- Queries timeout

**Solutions:**

```bash
# Check if GPU is being used
ollama ps

# Increase timeout in .env
OLLAMA_TIMEOUT=180

# Pre-load model
ollama run qwen2.5:7b-instruct ""
```

---

## 🗄️ Database Issues

### Container Not Starting

**Symptoms:**
- `docker compose up` fails
- Container immediately exits

**Solutions:**

```bash
# Check Docker logs
docker logs local-llm-mssql

# Common fixes:
# 1. Remove old container
docker rm -f local-llm-mssql

# 2. Remove volume (WARNING: deletes data)
docker volume rm local-llm-mssql-data

# 3. Restart fresh
cd docker
docker compose up -d
```

### Connection Refused

**Symptoms:**
- Cannot connect to `localhost:1433`
- `Connection refused` or `timeout`

**Solutions:**

| Check | Solution |
|-------|----------|
| Port in use | Stop other SQL Server instances |
| Container health | Wait for healthy status |
| Firewall | Allow port 1433 |

```bash
# Check if port 1433 is in use
netstat -an | grep 1433

# Check container health
docker inspect local-llm-mssql --format='{{.State.Health.Status}}'

# Wait for healthy (may take 30-60 seconds)
docker compose ps
```

### Authentication Failed

**Symptoms:**
- `Login failed for user 'sa'`
- Password errors

**Solutions:**

```bash
# Verify password in .env matches Docker
cat .env | grep SQL_PASSWORD
docker exec local-llm-mssql env | grep MSSQL_SA_PASSWORD

# Reset password (recreate container)
cd docker
docker compose down -v
MSSQL_SA_PASSWORD="NewPassword123!" docker compose up -d
```

### Database Not Found

**Symptoms:**
- `Cannot open database 'ResearchAnalytics'`
- Empty database

**Solutions:**

```bash
# Run initialization scripts
cd docker
docker compose --profile init up mssql-tools

# Verify database exists
docker exec -it local-llm-mssql /opt/mssql-tools18/bin/sqlcmd \
  -S localhost -U sa -P "LocalLLM@2024!" -No \
  -Q "SELECT name FROM sys.databases"
```

---

## 🔌 MCP Server Issues

### Server Not Found

**Symptoms:**
- `ENOENT` file not found error
- MCP server won't start

**Solutions:**

```bash
# Verify path exists
ls -la $MCP_MSSQL_PATH

# Check .env path is correct
cat .env | grep MCP_MSSQL_PATH

# Rebuild if needed
cd /path/to/SQL-AI-samples/MssqlMcp/Node
npm install
npm run build
```

### Node.js Version Issues

**Symptoms:**
- Syntax errors in MCP server
- `Unexpected token` errors

**Solutions:**

```bash
# Check Node.js version (need 18+)
node --version

# Update Node.js if needed
# Windows: Download from nodejs.org
# Mac: brew upgrade node
# Linux: nvm install 18
```

### MCP Connection Timeout

**Symptoms:**
- `MCP operation timed out`
- Tools not available

**Solutions:**

```bash
# Increase timeout in .env
MCP_TIMEOUT=60

# Test MCP server directly
node $MCP_MSSQL_PATH
# Should start without errors
```

### Tool Calls Failing

**Symptoms:**
- `Tool execution failed`
- SQL errors from MCP

**Solutions:**

| Error | Cause | Fix |
|-------|-------|-----|
| Invalid object | Table doesn't exist | Check table name |
| Permission denied | User lacks access | Check SQL user permissions |
| Syntax error | Invalid query | Review generated SQL |

```bash
# Enable debug logging
DEBUG=true uv run python -m src.cli.chat
```

---

## 🤖 Agent Issues

### Agent Won't Initialize

**Symptoms:**
- Import errors
- Configuration errors at startup

**Solutions:**

```bash
# Reinstall dependencies
uv sync --reinstall

# Check Python version
python --version  # Need 3.11+

# Verify .env exists
ls -la .env
```

### No Tools Available

**Symptoms:**
- Agent says "I don't have access to database tools"
- Empty tool list

**Solutions:**

```bash
# Check MCP configuration
cat mcp_config.json

# Verify MCP server starts
node $MCP_MSSQL_PATH

# Check environment variables are loaded
DEBUG=true uv run python -m src.cli.chat
```

### Incorrect SQL Generation

**Symptoms:**
- Agent generates wrong queries
- Syntax errors in SQL

**Solutions:**

| Issue | Solution |
|-------|----------|
| Wrong table names | Ask "What tables exist?" first |
| Wrong column names | Ask "Describe the [table] table" |
| Complex query fails | Break into simpler questions |

> 💡 **Tip:** Provide context in your questions: "Query the **Researchers** table to find..."

### Streamlit Won't Start

**Symptoms:**
- `streamlit: command not found`
- Port already in use

**Solutions:**

```bash
# Install Streamlit
uv pip install streamlit

# Use different port
STREAMLIT_PORT=8502 uv run streamlit run src/ui/streamlit_app.py

# Or specify port directly
uv run streamlit run src/ui/streamlit_app.py --server.port 8502
```

---

## ⚡ Performance Issues

### Slow Queries

**Symptoms:**
- Long wait times for results
- Timeouts on complex queries

**Optimization Table:**

| Bottleneck | Diagnosis | Solution |
|------------|-----------|----------|
| LLM inference | High CPU/GPU | Use smaller model |
| SQL execution | Slow queries | Add indexes |
| MCP latency | Tool call delays | Check network |

```bash
# Enable timing logs
DEBUG=true LOG_LEVEL=DEBUG uv run python -m src.cli.chat
```

### High Memory Usage

**Symptoms:**
- System becomes unresponsive
- Out of memory errors

**Solutions:**

```bash
# Monitor memory
docker stats local-llm-mssql

# Reduce SQL Server memory
docker compose down
# Edit docker-compose.yml to add:
# MSSQL_MEMORY_LIMIT_MB=2048

# Use smaller LLM model
OLLAMA_MODEL=mistral:7b-instruct
```

### GPU Not Utilized

**Symptoms:**
- High CPU usage
- GPU shows 0% utilization

**Solutions:**

```bash
# Check Ollama GPU support
ollama ps  # Should show GPU info

# Verify CUDA (NVIDIA)
nvidia-smi

# Reinstall Ollama with GPU support if needed
```

---

## 📊 Diagnostic Commands

### Complete System Check

```bash
#!/bin/bash
echo "=== System Diagnostics ==="

echo -e "\n--- Ollama ---"
curl -s http://localhost:11434/api/tags | jq '.models[].name' 2>/dev/null || echo "Ollama not running"

echo -e "\n--- Docker ---"
docker ps --format "{{.Names}}: {{.Status}}" | grep llm

echo -e "\n--- SQL Server ---"
docker exec local-llm-mssql /opt/mssql-tools18/bin/sqlcmd \
  -S localhost -U sa -P "LocalLLM@2024!" -No \
  -Q "SELECT @@VERSION" 2>/dev/null | head -1 || echo "SQL Server not accessible"

echo -e "\n--- Python ---"
python --version
pip show pydantic-ai 2>/dev/null | grep Version || echo "pydantic-ai not installed"

echo -e "\n--- Environment ---"
[ -f .env ] && echo ".env file exists" || echo ".env file MISSING"
```

### Log Collection

```bash
# Collect logs for debugging
mkdir -p debug-logs

# Docker logs
docker logs local-llm-mssql > debug-logs/mssql.log 2>&1

# Run agent with debug logging
DEBUG=true LOG_LEVEL=DEBUG uv run python -m src.cli.chat 2>&1 | tee debug-logs/agent.log
```

---

## ❓ Getting Help

### Before Asking for Help

1. ✅ Run the diagnostic commands above
2. ✅ Check this troubleshooting guide
3. ✅ Review the [Configuration Guide](configuration.md)
4. ✅ Search existing [GitHub Issues](https://github.com/fgarofalo56/local-llm-research-agent/issues)

### Information to Include

When reporting issues, provide:

| Information | How to Get It |
|-------------|---------------|
| Error message | Copy full stack trace |
| OS version | `uname -a` or Windows version |
| Python version | `python --version` |
| Docker version | `docker --version` |
| Ollama version | `ollama --version` |
| `.env` settings | Redact passwords! |

### Getting Support

- **GitHub Issues:** [Report a bug](https://github.com/fgarofalo56/local-llm-research-agent/issues/new)
- **Discussions:** [Ask questions](https://github.com/fgarofalo56/local-llm-research-agent/discussions)

---

*Last Updated: December 2024*
