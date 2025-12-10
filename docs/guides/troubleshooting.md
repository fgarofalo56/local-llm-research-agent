# Troubleshooting Guide

> **Comprehensive troubleshooting guide for the Local LLM Research Agent**

---

## Table of Contents

- [Quick Diagnostics](#quick-diagnostics)
- [LLM Provider Issues](#llm-provider-issues)
  - [Ollama Issues](#ollama-issues)
  - [Foundry Local Issues](#foundry-local-issues)
- [Database Issues](#database-issues)
  - [Connection Issues](#connection-issues)
  - [Authentication Issues](#authentication-issues)
  - [Azure SQL Issues](#azure-sql-issues)
- [MCP Server Issues](#mcp-server-issues)
- [Agent Issues](#agent-issues)
- [CLI Issues](#cli-issues)
- [Streamlit Issues](#streamlit-issues)
- [Performance Issues](#performance-issues)
- [Cache and Rate Limiting](#cache-and-rate-limiting)
- [Diagnostic Commands](#diagnostic-commands)
- [Getting Help](#getting-help)

---

## Quick Diagnostics

Run this comprehensive health check to identify issues:

### All-in-One Health Check

```bash
# Windows PowerShell
echo "=== System Diagnostics ===" `
  && echo "" `
  && echo "--- Python Environment ---" `
  && python --version `
  && echo "" `
  && echo "--- Ollama Status ---" `
  && curl -s http://localhost:11434/api/tags 2>$null || echo "Ollama not running" `
  && echo "" `
  && echo "--- Foundry Local Status ---" `
  && curl -s http://127.0.0.1:55588/v1/models 2>$null || echo "Foundry Local not running" `
  && echo "" `
  && echo "--- Docker Containers ---" `
  && docker ps --format "{{.Names}}: {{.Status}}" 2>$null | Select-String "llm" `
  && echo "" `
  && echo "--- Environment File ---" `
  && if (Test-Path .env) { echo ".env exists" } else { echo ".env MISSING" }
```

```bash
# Linux/macOS
echo "=== System Diagnostics ===" && \
echo "" && \
echo "--- Python Environment ---" && \
python --version && \
echo "" && \
echo "--- Ollama Status ---" && \
(curl -s http://localhost:11434/api/tags | head -c 100 || echo "Ollama not running") && \
echo "" && \
echo "--- Foundry Local Status ---" && \
(curl -s http://127.0.0.1:55588/v1/models | head -c 100 || echo "Foundry Local not running") && \
echo "" && \
echo "--- Docker Containers ---" && \
docker ps --format "{{.Names}}: {{.Status}}" 2>/dev/null | grep llm && \
echo "" && \
echo "--- Environment File ---" && \
[ -f .env ] && echo ".env exists" || echo ".env MISSING"
```

### Component Status Table

| Component | Check Command | Expected Result |
|-----------|---------------|-----------------|
| Python | `python --version` | 3.11+ |
| Ollama | `curl localhost:11434/api/tags` | JSON with models |
| Foundry Local | `curl 127.0.0.1:55588/v1/models` | JSON with models |
| Docker | `docker ps` | Containers running |
| SQL Server | `docker logs local-llm-mssql` | No errors |
| MCP Server | `node $MCP_MSSQL_PATH` | Server starts |
| .env file | `cat .env` | Configuration exists |

---

## LLM Provider Issues

### Ollama Issues

#### Ollama Not Running

**Symptoms:**
- `Connection refused` errors
- Agent cannot process queries
- `curl: (7) Failed to connect`

**Solutions:**

```bash
# Start Ollama (Windows/Mac - from app)
# Or Linux:
ollama serve

# Check status
curl http://localhost:11434/api/tags

# Restart systemd service (Linux)
sudo systemctl restart ollama
sudo systemctl status ollama
```

#### Model Not Found

**Symptoms:**
- `model 'xyz' not found` error
- Agent fails to initialize

**Solutions:**

```bash
# List available models
ollama list

# Pull required model
ollama pull qwen2.5:7b-instruct

# Verify model works
ollama run qwen2.5:7b-instruct "Hello"

# Update .env
OLLAMA_MODEL=qwen2.5:7b-instruct
```

#### Model Doesn't Support Tool Calling

**Symptoms:**
- Agent says "I don't have database tools"
- SQL queries not executed

**Solution:** Use a tool-capable model:

| Supported Models | Command |
|------------------|---------|
| `qwen2.5:7b-instruct` | `ollama pull qwen2.5:7b-instruct` |
| `llama3.1:8b` | `ollama pull llama3.1:8b` |
| `mistral:7b-instruct` | `ollama pull mistral:7b-instruct` |

#### Out of Memory (OOM)

**Symptoms:**
- Ollama crashes during inference
- `CUDA out of memory` errors
- System becomes unresponsive

**Solutions:**

| Option | Command/Action |
|--------|----------------|
| Use smaller model | `ollama pull qwen2.5:3b-instruct` |
| Use quantized model | `ollama pull qwen2.5:7b-instruct-q4_K_M` |
| Close other apps | Free up VRAM |
| CPU-only mode | `OLLAMA_NUM_GPU=0 ollama serve` |

#### Slow Responses

**Symptoms:**
- Long wait times (>30s)
- Queries timeout

**Solutions:**

```bash
# Pre-load model to avoid cold start
ollama run qwen2.5:7b-instruct ""

# Check GPU utilization
ollama ps

# Use faster model
OLLAMA_MODEL=mistral:7b-instruct
```

---

### Foundry Local Issues

#### SDK Not Installed

**Symptoms:**
- `ModuleNotFoundError: No module named 'foundry_local'`

**Solution:**

```bash
pip install foundry-local-sdk
```

#### Connection Refused

**Symptoms:**
- Cannot connect to `http://127.0.0.1:55588`

**Solutions:**

```python
# Ensure model is started
from foundry_local import FoundryLocalManager
manager = FoundryLocalManager("phi-4")
print(manager.endpoint)
```

```bash
# Check if port is in use
# Windows
netstat -ano | findstr 55588

# Linux/Mac
lsof -i :55588
```

#### Model Download Failed

**Symptoms:**
- Download errors or timeouts

**Solutions:**

```bash
# Check internet connection
ping huggingface.co

# Clear cache and retry
# Windows
del %LOCALAPPDATA%\FoundryLocal\models\* /q

# Linux/Mac
rm -rf ~/.local/share/FoundryLocal/models/*
```

#### Auto-Start Not Working

**Symptoms:**
- Model doesn't start when `FOUNDRY_AUTO_START=true`

**Solutions:**

```bash
# Verify .env settings
LLM_PROVIDER=foundry_local
FOUNDRY_AUTO_START=true
FOUNDRY_MODEL=phi-4

# Check SDK is installed
pip show foundry-local-sdk
```

---

## Database Issues

### Connection Issues

#### Container Not Starting

**Symptoms:**
- `docker compose up` fails
- Container immediately exits

**Solutions:**

```bash
# Check Docker logs
docker logs local-llm-mssql

# Remove old container
docker rm -f local-llm-mssql

# Remove volume (WARNING: deletes data)
docker volume rm local-llm-mssql-data

# Restart fresh
cd docker
docker compose up -d
```

#### Connection Refused

**Symptoms:**
- Cannot connect to `localhost:1433`
- `Connection refused` or `timeout`

**Solutions:**

| Check | Solution |
|-------|----------|
| Port in use | Stop other SQL Server instances |
| Container health | Wait for healthy status (30-60s) |
| Firewall | Allow port 1433 |

```bash
# Check port availability
# Windows
netstat -ano | findstr 1433

# Linux/Mac
lsof -i :1433

# Wait for container health
docker compose ps
docker inspect local-llm-mssql --format='{{.State.Health.Status}}'
```

### Authentication Issues

#### SQL Authentication Failed

**Symptoms:**
- `Login failed for user 'sa'`

**Solutions:**

```bash
# Verify password matches
cat .env | grep SQL_PASSWORD
docker exec local-llm-mssql env | grep MSSQL_SA_PASSWORD

# Reset container with correct password
cd docker
docker compose down -v
docker compose up -d
```

#### Windows Authentication Failed

**Symptoms:**
- `Login failed` with Windows Auth

**Solutions:**

```bash
# Verify configuration
SQL_AUTH_TYPE=windows
SQL_USERNAME=
SQL_PASSWORD=

# Ensure running on domain-joined machine
# Check Kerberos/NTLM configuration
```

#### Azure AD Authentication Failed

**Symptoms:**
- `AADSTS` error codes
- Token acquisition failed

**Solutions by Auth Type:**

**Interactive Auth (`azure_ad_interactive`):**
```bash
# Ensure browser access
# Check Azure AD permissions for user
SQL_AUTH_TYPE=azure_ad_interactive
```

**Service Principal (`azure_ad_service_principal`):**
```bash
# Verify credentials
AZURE_TENANT_ID=your-tenant-guid
AZURE_CLIENT_ID=your-client-guid
AZURE_CLIENT_SECRET=your-secret

# Check app registration permissions in Azure Portal
# Ensure "Azure SQL Database" permission granted
```

**Managed Identity (`azure_ad_managed_identity`):**
```bash
# Only works on Azure-hosted resources (VM, App Service)
# Verify managed identity is enabled
# Check database user created for managed identity

# For user-assigned identity, specify client ID:
AZURE_CLIENT_ID=user-assigned-identity-client-id
```

**Default Credential (`azure_ad_default`):**
```bash
# Try Azure CLI login first
az login

# Then use default credential
SQL_AUTH_TYPE=azure_ad_default
```

### Azure SQL Issues

#### Cannot Connect to Azure SQL

**Symptoms:**
- Connection timeout to `.database.windows.net`

**Solutions:**

```bash
# Check server firewall
# Add client IP in Azure Portal > SQL Server > Networking

# Verify encryption settings
SQL_ENCRYPT=true
SQL_TRUST_SERVER_CERTIFICATE=false

# Check DNS resolution
nslookup your-server.database.windows.net
```

#### Azure AD Permission Denied

**Symptoms:**
- `The server principal is not able to access the database`

**Solution:**

```sql
-- In Azure SQL, create user for Azure AD identity
CREATE USER [your-app-name] FROM EXTERNAL PROVIDER;
ALTER ROLE db_datareader ADD MEMBER [your-app-name];
-- Add db_datawriter if not using readonly mode
```

---

## MCP Server Issues

#### Server Not Found

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

#### Node.js Version Issues

**Symptoms:**
- Syntax errors in MCP server
- `Unexpected token` errors

**Solutions:**

```bash
# Check Node.js version (need 18+)
node --version

# Update Node.js
# Windows: Download from nodejs.org
# Mac: brew upgrade node
# Linux: nvm install 18
```

#### MCP Connection Timeout

**Symptoms:**
- `MCP operation timed out`
- Tools not available

**Solutions:**

```bash
# Increase timeout
MCP_TIMEOUT=60

# Test MCP server directly
node $MCP_MSSQL_PATH
```

#### Tool Calls Failing

**Symptoms:**
- `Tool execution failed`
- SQL errors from MCP

**Error Reference:**

| Error | Cause | Fix |
|-------|-------|-----|
| Invalid object | Table doesn't exist | Check table name |
| Permission denied | User lacks access | Check SQL permissions |
| Syntax error | Invalid query | Review generated SQL |
| Readonly violation | Write in readonly mode | Set `MCP_MSSQL_READONLY=false` |

---

## Agent Issues

#### Agent Won't Initialize

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

#### No Tools Available

**Symptoms:**
- Agent says "I don't have access to database tools"
- Empty tool list

**Solutions:**

```bash
# Check MCP configuration
cat mcp_config.json

# Verify MCP server starts
node $MCP_MSSQL_PATH

# Enable debug logging
DEBUG=true uv run python -m src.cli.chat
```

#### Wrong Provider Selected

**Symptoms:**
- Using Ollama when Foundry expected (or vice versa)

**Solution:**

```bash
# Check .env
LLM_PROVIDER=ollama  # or foundry_local

# Override at runtime
uv run python -m src.cli.chat --provider ollama
```

---

## CLI Issues

#### Command Not Found

**Symptoms:**
- `llm-chat: command not found`

**Solutions:**

```bash
# Install package in development mode
pip install -e .

# Or run directly
uv run python -m src.cli.chat
```

#### Streaming Not Working

**Symptoms:**
- Output appears all at once

**Solution:**

```bash
# Enable streaming
uv run python -m src.cli.chat --stream
```

#### History Not Saving

**Symptoms:**
- `history save` fails

**Solutions:**

```bash
# Check write permissions
ls -la ~/.local/share/local-llm-research-agent/

# Create directory if missing
mkdir -p ~/.local/share/local-llm-research-agent/history
```

---

## Streamlit Issues

#### Streamlit Won't Start

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

#### Session State Issues

**Symptoms:**
- Conversation resets unexpectedly

**Solutions:**

```bash
# Clear browser cache
# Or use incognito mode

# Check for widget key conflicts in logs
```

---

## Performance Issues

### Slow Queries

**Symptoms:**
- Long wait times for results
- Timeouts on complex queries

**Optimization Table:**

| Bottleneck | Diagnosis | Solution |
|------------|-----------|----------|
| LLM inference | High CPU/GPU | Use smaller model |
| SQL execution | Slow queries | Add database indexes |
| MCP latency | Tool call delays | Check network |
| Cold start | First query slow | Pre-load model |

### High Memory Usage

**Solutions:**

```bash
# Monitor memory
docker stats local-llm-mssql

# Use smaller LLM model
OLLAMA_MODEL=qwen2.5:3b-instruct

# Limit SQL Server memory
# Edit docker-compose.yml:
# MSSQL_MEMORY_LIMIT_MB=2048
```

### GPU Not Utilized

**Solutions:**

```bash
# Check Ollama GPU support
ollama ps  # Should show GPU info

# Verify CUDA (NVIDIA)
nvidia-smi

# Check Foundry Local
# GPU auto-detected
```

---

## Cache and Rate Limiting

### Cache Not Working

**Symptoms:**
- Repeated queries not faster
- Cache stats show no hits

**Solutions:**

```bash
# Verify cache enabled
CACHE_ENABLED=true

# Check cache stats in CLI
cache

# Clear and retry
cache-clear
```

### Rate Limiting Blocking Requests

**Symptoms:**
- `Rate limit exceeded` errors

**Solutions:**

```bash
# Adjust rate limit settings
RATE_LIMIT_ENABLED=true
RATE_LIMIT_RPM=60  # Requests per minute
RATE_LIMIT_BURST=10

# Or disable temporarily
RATE_LIMIT_ENABLED=false
```

---

## Diagnostic Commands

### Complete System Check Script

```bash
#!/bin/bash
echo "=== Local LLM Research Agent Diagnostics ==="
echo "Generated: $(date)"
echo ""

echo "--- Environment ---"
[ -f .env ] && echo ".env file: EXISTS" || echo ".env file: MISSING"
echo "Python: $(python --version 2>&1)"
echo "Node.js: $(node --version 2>&1)"
echo "Docker: $(docker --version 2>&1)"

echo ""
echo "--- LLM Providers ---"
echo "Ollama:"
curl -s http://localhost:11434/api/tags 2>/dev/null | head -c 200 || echo "  Not running"
echo ""
echo "Foundry Local:"
curl -s http://127.0.0.1:55588/v1/models 2>/dev/null | head -c 200 || echo "  Not running"

echo ""
echo "--- Docker Containers ---"
docker ps --format "table {{.Names}}\t{{.Status}}" 2>/dev/null | grep -E "(NAMES|llm)"

echo ""
echo "--- SQL Server ---"
docker exec local-llm-mssql /opt/mssql-tools18/bin/sqlcmd \
  -S localhost -U sa -P "LocalLLM@2024!" -No \
  -Q "SELECT @@VERSION" 2>/dev/null | head -1 || echo "Not accessible"

echo ""
echo "--- Configuration Summary ---"
grep -E "^(LLM_PROVIDER|OLLAMA_|FOUNDRY_|SQL_|MCP_)" .env 2>/dev/null | \
  sed 's/PASSWORD=.*/PASSWORD=***HIDDEN***/'

echo ""
echo "=== End Diagnostics ==="
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

## Getting Help

### Before Asking for Help

1. Run the diagnostic commands above
2. Check this troubleshooting guide
3. Review the [Configuration Guide](configuration.md)
4. Search existing [GitHub Issues](https://github.com/yourusername/local-llm-research-agent/issues)

### Information to Include

| Information | How to Get It |
|-------------|---------------|
| Error message | Copy full stack trace |
| OS version | `uname -a` or Windows version |
| Python version | `python --version` |
| Docker version | `docker --version` |
| Ollama version | `ollama --version` |
| Provider in use | Check `LLM_PROVIDER` in .env |
| Auth type | Check `SQL_AUTH_TYPE` in .env |
| `.env` settings | Redact passwords! |

### Getting Support

- **GitHub Issues:** [Report a bug](https://github.com/yourusername/local-llm-research-agent/issues/new)
- **Discussions:** [Ask questions](https://github.com/yourusername/local-llm-research-agent/discussions)

---

## Error Code Reference

### Common Error Codes

| Error | Component | Meaning | Solution |
|-------|-----------|---------|----------|
| ECONNREFUSED | Network | Service not running | Start the service |
| ENOENT | Filesystem | File not found | Check path configuration |
| ETIMEDOUT | Network | Connection timeout | Check firewall/network |
| OOM | Memory | Out of memory | Use smaller model |
| 401 | Auth | Unauthorized | Check credentials |
| 403 | Auth | Forbidden | Check permissions |
| AADSTS50001 | Azure AD | App not found | Check client ID |
| AADSTS7000215 | Azure AD | Invalid secret | Regenerate secret |
| AADSTS90002 | Azure AD | Tenant not found | Check tenant ID |

---

*Last Updated: December 2024*
