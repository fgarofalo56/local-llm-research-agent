# Troubleshooting Guide

> **Comprehensive troubleshooting guide for the Local LLM Research Agent**

This guide covers 25+ common issues with detailed symptoms, causes, solutions, and debugging commands.

---

## Table of Contents

- [Quick Diagnostics](#quick-diagnostics)
- [Docker & Container Issues](#docker--container-issues)
- [Database Connection Issues](#database-connection-issues)
- [Ollama/LLM Issues](#ollamallm-issues)
- [RAG Pipeline Issues](#rag-pipeline-issues)
- [Frontend Issues](#frontend-issues)
- [General Issues](#general-issues)
- [Diagnostic Scripts](#diagnostic-scripts)
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
  && echo "--- Docker Containers ---" `
  && docker ps --format "{{.Names}}: {{.Status}}" 2>$null | Select-String "agent" `
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
echo "--- Docker Containers ---" && \
docker ps --format "{{.Names}}: {{.Status}}" 2>/dev/null | grep agent && \
echo "" && \
echo "--- Environment File ---" && \
[ -f .env ] && echo ".env exists" || echo ".env MISSING"
```

### Component Status Table

| Component | Check Command | Expected Result |
|-----------|---------------|-----------------|
| Python | `python --version` | 3.11+ |
| Node.js | `node --version` | 18+ |
| Ollama | `curl localhost:11434/api/tags` | JSON with models |
| Docker | `docker ps` | Containers running |
| SQL Server 2022 | `docker logs local-agent-mssql` | No errors |
| SQL Server 2025 | `docker logs local-agent-mssql-backend` | No errors |
| Redis | `docker exec local-agent-redis redis-cli PING` | PONG |
| FastAPI | `curl localhost:8000/api/health` | JSON health status |
| React Frontend | `curl localhost:5173` | HTML response |
| MCP Server | `node $MCP_MSSQL_PATH` | Server starts |
| .env file | `cat .env` | Configuration exists |

---

## Docker & Container Issues

### Problem 1: SQL Server Container Won't Start

**Symptoms:**
- Container exits immediately after starting
- `docker ps` shows container not running
- Error: `Container local-agent-mssql exited with code 1`

**Cause:**
- SA password doesn't meet complexity requirements
- Port 1433 already in use by another SQL Server instance
- Insufficient memory allocated to Docker
- Volume permission issues on Linux

**Solution:**

1. **Check password complexity:**

```bash
# Password must be at least 8 characters with uppercase, lowercase, numbers, and symbols
# Edit .env file:
MSSQL_SA_PASSWORD=YourStrong!Pass123
```

2. **Check port conflicts:**

```bash
# Windows
netstat -ano | findstr 1433

# Linux/Mac
lsof -i :1433

# If port is in use, stop the conflicting service or change port in .env:
SQL_SERVER_PORT=1434
```

3. **Check Docker logs:**

```bash
docker logs local-agent-mssql

# Common error messages:
# "ERROR: The password does not meet SQL Server password policy requirements"
# "ERROR: Setup FAILED copying system data file"
```

4. **Increase Docker memory:**

```bash
# Docker Desktop → Settings → Resources → Memory
# Allocate at least 4GB for SQL Server

# Or in docker-compose.yml, add:
services:
  mssql:
    mem_limit: 4g
```

5. **Fix volume permissions (Linux):**

```bash
# On Linux, SQL Server container runs as user 'mssql' (UID 10001)
sudo chown -R 10001:10001 /var/lib/docker/volumes/local-llm-mssql-data/_data
```

**Debugging Commands:**

```bash
# Remove container and start fresh
docker-compose -f docker/docker-compose.yml down
docker rm -f local-agent-mssql
docker volume rm local-llm-mssql-data

# Create volume with proper permissions
docker volume create local-llm-mssql-data

# Start with logs visible
docker-compose -f docker/docker-compose.yml --env-file .env up mssql

# Check container health
docker inspect local-agent-mssql --format='{{.State.Health.Status}}'
```

---

### Problem 2: Redis Container Connection Refused

**Symptoms:**
- `redis.exceptions.ConnectionError: Error 111 connecting to localhost:6379`
- Health check shows Redis as unhealthy
- FastAPI logs: `Failed to connect to Redis`

**Cause:**
- Redis container not running
- Port conflict on 6379
- Firewall blocking Redis port
- Redis taking time to initialize

**Solution:**

1. **Verify container is running:**

```bash
docker ps | grep redis

# Expected output:
# local-agent-redis   Up 2 minutes (healthy)
```

2. **Check Redis logs:**

```bash
docker logs local-agent-redis

# Look for:
# "Ready to accept connections"
```

3. **Test Redis connection:**

```bash
# From host
docker exec local-agent-redis redis-cli PING
# Expected: PONG

# Test from container network
docker exec local-agent-api redis-cli -h redis-stack PING
```

4. **Check port availability:**

```bash
# Windows
netstat -ano | findstr 6379

# Linux/Mac
lsof -i :6379
```

5. **Restart Redis:**

```bash
docker-compose -f docker/docker-compose.yml restart redis-stack

# Wait 10 seconds for initialization
sleep 10

# Verify health
docker-compose -f docker/docker-compose.yml ps redis-stack
```

**Debugging Commands:**

```bash
# Check Redis configuration
docker exec local-agent-redis redis-cli CONFIG GET *

# Monitor Redis operations
docker exec local-agent-redis redis-cli MONITOR

# Check memory usage
docker exec local-agent-redis redis-cli INFO memory

# Test vector search
docker exec local-agent-redis redis-cli FT._LIST
```

---

### Problem 3: Port Already Allocated

**Symptoms:**
- `Error: port is already allocated`
- Container fails to start with message: `Bind for 0.0.0.0:8001 failed: port is already allocated`

**Cause:**
- Another service using the same port
- Previous container not properly stopped
- Port specified in .env but not loaded by docker-compose

**Solution:**

1. **Find what's using the port:**

```bash
# Windows
netstat -ano | findstr 8001
tasklist /FI "PID eq <PID>"

# Linux/Mac
lsof -i :8001
ps aux | grep <PID>
```

2. **Stop conflicting service:**

```bash
# Find and stop old container
docker ps -a | grep 8001
docker rm -f <container_id>

# Or change port in .env
REDIS_INSIGHT_PORT=8002
```

3. **Critical: Load .env file when running from project root:**

```bash
# ✅ CORRECT - Environment variables loaded
docker-compose -f docker/docker-compose.yml --env-file .env up -d

# ❌ WRONG - Uses default ports, may conflict
docker-compose -f docker/docker-compose.yml up -d
```

4. **Restart with proper env file:**

```bash
# Stop all
docker-compose -f docker/docker-compose.yml down

# Start with env file
docker-compose -f docker/docker-compose.yml --env-file .env up -d
```

**Debugging Commands:**

```bash
# List all port bindings
docker ps --format "table {{.Names}}\t{{.Ports}}"

# Check which env file docker-compose is using
docker-compose -f docker/docker-compose.yml --env-file .env config | grep -A 5 "ports:"

# Test if port is reachable
curl http://localhost:8001
nc -zv localhost 8001
```

---

### Problem 4: Volume Permission Errors

**Symptoms:**
- `mkdir: cannot create directory '/var/opt/mssql/data': Permission denied`
- Container logs show: `Cannot open server error log file`
- SQL Server container exits with code 1

**Cause:**
- SQL Server container runs as non-root user (UID 10001)
- Docker volume has incorrect ownership
- SELinux preventing access (Linux)

**Solution:**

1. **On Linux, fix volume ownership:**

```bash
# Find volume location
docker volume inspect local-llm-mssql-data

# Set proper ownership
sudo chown -R 10001:10001 /var/lib/docker/volumes/local-llm-mssql-data/_data

# Or for the mount point
sudo chown -R 10001:10001 /var/opt/mssql
```

2. **On Windows/Mac (using named volumes):**

```bash
# Remove and recreate volume
docker-compose -f docker/docker-compose.yml down -v
docker volume create local-llm-mssql-data
docker-compose -f docker/docker-compose.yml --env-file .env up -d
```

3. **SELinux issues (RHEL/CentOS/Fedora):**

```bash
# Check if SELinux is enforcing
getenforce

# Add SELinux context
sudo chcon -Rt svirt_sandbox_file_t /var/lib/docker/volumes/local-llm-mssql-data/_data

# Or disable SELinux temporarily (not recommended for production)
sudo setenforce 0
```

**Debugging Commands:**

```bash
# Check volume ownership
docker volume inspect local-llm-mssql-data | grep Mountpoint
ls -la $(docker volume inspect local-llm-mssql-data -f '{{.Mountpoint}}')

# Run container as root temporarily for debugging
docker run -it --rm --entrypoint bash \
  -v local-llm-mssql-data:/var/opt/mssql \
  --user root \
  mcr.microsoft.com/mssql/server:2022-latest

# Inside container
ls -la /var/opt/mssql
chown -R mssql:mssql /var/opt/mssql
```

---

### Problem 5: Container Logs Show "Waiting for Database"

**Symptoms:**
- Init containers (mssql-tools) stuck waiting
- Logs show: `Waiting for database to be ready...`
- Database initialization never completes

**Cause:**
- SQL Server container not fully initialized (takes 30-60 seconds)
- Database not created yet
- Network connectivity issues between containers
- SA password mismatch

**Solution:**

1. **Wait for SQL Server to be healthy:**

```bash
# Check health status
docker inspect local-agent-mssql --format='{{.State.Health.Status}}'

# Should show: healthy (not starting)

# Watch health checks in real-time
watch -n 2 "docker inspect local-agent-mssql --format='{{.State.Health.Status}}'"
```

2. **Check SQL Server is accepting connections:**

```bash
# Test from host
docker exec local-agent-mssql /opt/mssql-tools18/bin/sqlcmd \
  -S localhost -U sa -P "LocalLLM@2024!" -No \
  -Q "SELECT 'Connected' AS Status"

# Should show: Connected
```

3. **Check network connectivity:**

```bash
# From init container, ping SQL Server
docker-compose -f docker/docker-compose.yml run --rm mssql-tools ping mssql

# Check if containers are on same network
docker network inspect local-agent-ai-stack_default
```

4. **Run initialization manually:**

```bash
# Stop stuck container
docker-compose -f docker/docker-compose.yml --profile init stop mssql-tools

# Run initialization manually with debugging
docker-compose -f docker/docker-compose.yml --env-file .env --profile init \
  run --rm mssql-tools /bin/bash

# Inside container, test connection
sqlcmd -S mssql -U sa -P "$MSSQL_SA_PASSWORD" -No -Q "SELECT 1"
```

**Debugging Commands:**

```bash
# View init script execution
docker-compose -f docker/docker-compose.yml --env-file .env --profile init \
  logs -f mssql-tools

# Check which databases exist
docker exec local-agent-mssql /opt/mssql-tools18/bin/sqlcmd \
  -S localhost -U sa -P "LocalLLM@2024!" -No \
  -Q "SELECT name FROM sys.databases"

# Manually run init scripts
docker exec -i local-agent-mssql /opt/mssql-tools18/bin/sqlcmd \
  -S localhost -U sa -P "LocalLLM@2024!" -No \
  < docker/init/01-create-database.sql
```

---

## Database Connection Issues

### Problem 6: SQL Server Authentication Failed

**Symptoms:**
- `Login failed for user 'sa'`
- Error code: 18456
- Application cannot connect to database

**Cause:**
- Password in .env doesn't match password in SQL Server
- Password was changed after initial container creation
- SQL Server not configured for SQL Authentication (Windows Auth only)

**Solution:**

1. **Verify password matches:**

```bash
# Check password in .env
cat .env | grep MSSQL_SA_PASSWORD

# Check password in container
docker exec local-agent-mssql env | grep MSSQL_SA_PASSWORD
```

2. **Password mismatch - Reset everything:**

```bash
# WARNING: This deletes all data
docker-compose -f docker/docker-compose.yml down -v
docker volume rm local-llm-mssql-data
docker volume create local-llm-mssql-data

# Edit .env with new password
# Then start fresh
docker-compose -f docker/docker-compose.yml --env-file .env up -d
```

3. **Test connection with correct password:**

```bash
# From host
docker exec local-agent-mssql /opt/mssql-tools18/bin/sqlcmd \
  -S localhost -U sa -P "YourPassword" -No \
  -Q "SELECT @@VERSION"
```

4. **Enable SQL Authentication (if needed):**

```bash
# SQL Server in containers is pre-configured for SQL Auth
# But for external SQL Server, enable it:
# SQL Server → Properties → Security → SQL Server and Windows Authentication mode
```

**Debugging Commands:**

```bash
# Check SQL Server error log
docker exec local-agent-mssql cat /var/opt/mssql/log/errorlog | grep -i "login failed"

# Example error:
# Login failed for user 'sa'. Reason: Password did not match that for the login provided.

# Test with sqlcmd
docker exec -it local-agent-mssql /opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P "Password"

# Check authentication mode
docker exec local-agent-mssql /opt/mssql-tools18/bin/sqlcmd \
  -S localhost -U sa -P "Password" -No \
  -Q "SELECT SERVERPROPERTY('IsIntegratedSecurityOnly')"
# Should return: 0 (SQL Auth enabled)
```

---

### Problem 7: Database Not Found

**Symptoms:**
- `Cannot open database "ResearchAnalytics" requested by the login`
- Application crashes on startup
- SQL queries fail with database name error

**Cause:**
- Database initialization script didn't run
- Init container failed silently
- Database was deleted

**Solution:**

1. **Check if database exists:**

```bash
docker exec local-agent-mssql /opt/mssql-tools18/bin/sqlcmd \
  -S localhost -U sa -P "LocalLLM@2024!" -No \
  -Q "SELECT name FROM sys.databases"

# Look for: ResearchAnalytics
```

2. **Run initialization if missing:**

```bash
# For sample database
docker-compose -f docker/docker-compose.yml --env-file .env --profile init \
  up mssql-tools

# For backend database
docker-compose -f docker/docker-compose.yml --env-file .env --profile init \
  up mssql-backend-tools
```

3. **Manually create database:**

```bash
# Create ResearchAnalytics database
docker exec local-agent-mssql /opt/mssql-tools18/bin/sqlcmd \
  -S localhost -U sa -P "LocalLLM@2024!" -No \
  -Q "CREATE DATABASE ResearchAnalytics"

# Run all init scripts manually
for script in docker/init/*.sql; do
  echo "Running $script..."
  docker exec -i local-agent-mssql /opt/mssql-tools18/bin/sqlcmd \
    -S localhost -U sa -P "LocalLLM@2024!" -No < "$script"
done
```

**Debugging Commands:**

```bash
# Check init container logs
docker-compose -f docker/docker-compose.yml --profile init logs mssql-tools

# List all databases and their status
docker exec local-agent-mssql /opt/mssql-tools18/bin/sqlcmd \
  -S localhost -U sa -P "LocalLLM@2024!" -No \
  -Q "SELECT name, state_desc, recovery_model_desc FROM sys.databases"

# Check if tables exist in database
docker exec local-agent-mssql /opt/mssql-tools18/bin/sqlcmd \
  -S localhost -U sa -P "LocalLLM@2024!" -d ResearchAnalytics -No \
  -Q "SELECT TABLE_SCHEMA, TABLE_NAME FROM INFORMATION_SCHEMA.TABLES"
```

---

### Problem 8: Connection Timeout

**Symptoms:**
- `A connection attempt failed because the connected party did not properly respond`
- `Timeout expired` errors
- Long waits (30+ seconds) before failure

**Cause:**
- Firewall blocking port 1433/1434
- SQL Server not started yet
- Network configuration issue
- Connection string pointing to wrong host

**Solution:**

1. **Verify SQL Server is running:**

```bash
docker ps | grep mssql

# Should show: Up X minutes (healthy)
```

2. **Check port is accessible:**

```bash
# Windows
Test-NetConnection localhost -Port 1433

# Linux/Mac
nc -zv localhost 1433
telnet localhost 1433
```

3. **Test connection from container network:**

```bash
# If connecting from another container
docker-compose -f docker/docker-compose.yml run --rm api python -c "
import pyodbc
conn = pyodbc.connect(
    'DRIVER={ODBC Driver 18 for SQL Server};'
    'SERVER=mssql,1433;'
    'DATABASE=ResearchAnalytics;'
    'UID=sa;'
    'PWD=LocalLLM@2024!;'
    'TrustServerCertificate=yes;'
)
print('Connected!')
"
```

4. **Increase timeout in connection string:**

```python
# In .env or code
CONNECTION_TIMEOUT=30
LOGIN_TIMEOUT=30

# Connection string
"Server=localhost,1433;Database=ResearchAnalytics;User Id=sa;Password=xxx;TrustServerCertificate=true;Connection Timeout=30;Login Timeout=30"
```

**Debugging Commands:**

```bash
# Check SQL Server error log for connection issues
docker exec local-agent-mssql cat /var/opt/mssql/log/errorlog | tail -50

# Monitor network traffic
docker exec local-agent-mssql netstat -an | grep 1433

# Check firewall (Windows)
netsh advfirewall firewall show rule name=all | findstr 1433

# Check iptables (Linux)
sudo iptables -L -n | grep 1433

# Test with explicit IP instead of localhost
docker exec local-agent-api ping mssql
```

---

### Problem 9: TLS/Certificate Errors

**Symptoms:**
- `SSL Provider: The certificate chain was issued by an authority that is not trusted`
- `Certificate verification failed`
- Connection fails with SSL error

**Cause:**
- SQL Server using self-signed certificate
- `TrustServerCertificate` not set to true
- Encryption settings mismatch

**Solution:**

1. **Trust the server certificate:**

```bash
# In .env file
SQL_TRUST_SERVER_CERTIFICATE=true

# Or in connection string
"TrustServerCertificate=yes"
```

2. **Update ODBC connection strings:**

```python
# Python pyodbc
connection_string = (
    "DRIVER={ODBC Driver 18 for SQL Server};"
    "SERVER=localhost,1433;"
    "DATABASE=ResearchAnalytics;"
    "UID=sa;"
    "PWD=LocalLLM@2024!;"
    "TrustServerCertificate=yes;"  # Add this
)
```

3. **For production with real certificates:**

```bash
# Export certificate from SQL Server
docker exec local-agent-mssql cat /etc/ssl/certs/mssql.pem > mssql-cert.pem

# Import to trusted store (Linux)
sudo cp mssql-cert.pem /usr/local/share/ca-certificates/
sudo update-ca-certificates

# Then use: TrustServerCertificate=no
```

**Debugging Commands:**

```bash
# Check certificate details
docker exec local-agent-mssql openssl s_client -connect localhost:1433 -starttls mssql

# Verify SQL Server encryption settings
docker exec local-agent-mssql /opt/mssql-tools18/bin/sqlcmd \
  -S localhost -U sa -P "LocalLLM@2024!" -N -No \
  -Q "SELECT encrypt_option FROM sys.dm_exec_connections WHERE session_id = @@SPID"

# Test connection with different encryption modes
# No encryption
sqlcmd -S localhost,1433 -U sa -P "Password" -No

# Encrypted but trust cert
sqlcmd -S localhost,1433 -U sa -P "Password" -N -No -C
```

---

## Ollama/LLM Issues

### Problem 10: Ollama Not Running

**Symptoms:**
- `Connection refused` on http://localhost:11434
- Agent fails with: `Failed to connect to Ollama`
- `curl: (7) Failed to connect to localhost port 11434`

**Cause:**
- Ollama service not started
- Port 11434 blocked by firewall
- Ollama crashed

**Solution:**

1. **Check if Ollama is running:**

```bash
# Test connection
curl http://localhost:11434/api/tags

# Expected: JSON list of models
```

2. **Start Ollama:**

```bash
# Windows/Mac: Start Ollama Desktop app
# Or from terminal
ollama serve

# Linux with systemd
sudo systemctl start ollama
sudo systemctl enable ollama  # Auto-start on boot

# Check status
sudo systemctl status ollama
```

3. **Check process is running:**

```bash
# Windows
tasklist | findstr ollama

# Linux/Mac
ps aux | grep ollama
pgrep -fa ollama
```

4. **Check firewall:**

```bash
# Windows: Allow port 11434 in Windows Firewall
netsh advfirewall firewall add rule name="Ollama" dir=in action=allow protocol=TCP localport=11434

# Linux: ufw
sudo ufw allow 11434/tcp

# Linux: firewalld
sudo firewall-cmd --permanent --add-port=11434/tcp
sudo firewall-cmd --reload
```

**Debugging Commands:**

```bash
# Check Ollama version
ollama --version

# List installed models
ollama list

# Check logs (Linux systemd)
sudo journalctl -u ollama -f

# Check port binding
# Windows
netstat -ano | findstr 11434

# Linux/Mac
lsof -i :11434

# Test model manually
ollama run qwen2.5:7b-instruct "Hello, are you working?"
```

---

### Problem 11: Model Not Found

**Symptoms:**
- `Error: model 'qwen2.5:7b-instruct' not found`
- Agent initialization fails
- Ollama returns 404 error

**Cause:**
- Model not pulled/downloaded
- Model name typo in .env
- Model deleted from Ollama storage

**Solution:**

1. **Check available models:**

```bash
ollama list

# Example output:
# NAME                    ID            SIZE
# qwen2.5:7b-instruct    abc123        4.7GB
```

2. **Pull the model:**

```bash
# Pull recommended model
ollama pull qwen2.5:7b-instruct

# Or alternative models
ollama pull llama3.1:8b
ollama pull mistral:7b-instruct

# Check progress
# Model download shows progress bar
```

3. **Verify model name in .env:**

```bash
# Check .env
cat .env | grep OLLAMA_MODEL

# Should match exactly:
OLLAMA_MODEL=qwen2.5:7b-instruct

# Common typos:
# ❌ qwen25:7b-instruct
# ❌ qwen2.5:7b
# ✅ qwen2.5:7b-instruct
```

4. **Test model directly:**

```bash
# Run model manually
ollama run qwen2.5:7b-instruct "Say hello"

# Check model info
ollama show qwen2.5:7b-instruct
```

**Debugging Commands:**

```bash
# List all model versions
ollama list | grep qwen

# Get model details
curl http://localhost:11434/api/show -d '{"name":"qwen2.5:7b-instruct"}'

# Check model file location
# Linux/Mac
ls -lh ~/.ollama/models/

# Windows
dir %USERPROFILE%\.ollama\models\

# Delete and re-download model
ollama rm qwen2.5:7b-instruct
ollama pull qwen2.5:7b-instruct
```

---

### Problem 12: Out of GPU Memory

**Symptoms:**
- `CUDA out of memory` error
- Ollama process crashes
- System becomes unresponsive
- Model loads then crashes

**Cause:**
- Model too large for available VRAM
- Other applications using GPU
- Memory fragmentation
- Multiple models loaded

**Solution:**

1. **Check GPU memory:**

```bash
# NVIDIA
nvidia-smi

# Look for memory usage:
# |  N  Name           Persistence-M| Bus-Id        Disp.A | Volatile Uncorr. ECC |
# |  0  RTX 5090       Off          | 00000000:01   On     |                  N/A |
# |  Memory-Usage: 28000MiB / 32000MiB

# AMD
rocm-smi
```

2. **Use smaller model:**

```bash
# In .env, switch to smaller model
OLLAMA_MODEL=qwen2.5:3b-instruct  # ~2GB VRAM

# Or quantized version
OLLAMA_MODEL=llama3.1:8b-q4_K_M  # ~4.5GB vs 8GB
```

3. **Close other GPU applications:**

```bash
# Find GPU processes
# NVIDIA
nvidia-smi

# Kill GPU process (if safe)
kill <PID>
```

4. **Use CPU-only mode:**

```bash
# Set environment variable
OLLAMA_NUM_GPU=0 ollama serve

# Or in .env
OLLAMA_NUM_GPU=0
```

5. **Limit GPU layers:**

```bash
# Load only some layers on GPU
OLLAMA_NUM_GPU_LAYERS=20 ollama serve
```

**Debugging Commands:**

```bash
# Monitor GPU memory in real-time
watch -n 1 nvidia-smi

# Check Ollama GPU usage
ollama ps

# Example output:
# NAME                 ID       SIZE    PROCESSOR    UNTIL
# qwen2.5:7b-instruct  abc123   4.7GB   100% GPU     4 minutes from now

# Clear loaded models
curl -X POST http://localhost:11434/api/unload -d '{"name":"qwen2.5:7b-instruct"}'

# Restart Ollama service
sudo systemctl restart ollama
```

---

### Problem 13: Slow Inference Speed

**Symptoms:**
- Responses take 30+ seconds
- Tokens/second very low (<10 tok/s)
- Queries timeout
- Model loading takes forever

**Cause:**
- Model running on CPU instead of GPU
- Large model for available hardware
- Cold start (model not pre-loaded)
- Thermal throttling

**Solution:**

1. **Verify GPU is being used:**

```bash
ollama ps

# Should show: "100% GPU" not "CPU"
# Example:
# NAME                 PROCESSOR
# qwen2.5:7b-instruct  100% GPU ✅
# qwen2.5:7b-instruct  CPU ❌
```

2. **Pre-load model to avoid cold start:**

```bash
# Load model into memory
ollama run qwen2.5:7b-instruct ""

# Model stays loaded for 5 minutes by default
# Check with:
ollama ps
```

3. **Use faster model:**

```bash
# Switch to smaller/faster model
OLLAMA_MODEL=mistral:7b-instruct  # Often faster than Llama

# Or quantized
OLLAMA_MODEL=qwen2.5:7b-q4_K_M
```

4. **Increase keep-alive time:**

```bash
# Keep model loaded longer
OLLAMA_KEEP_ALIVE=30m

# Or in Modelfile
FROM qwen2.5:7b-instruct
PARAMETER keep_alive 30m
```

5. **Check for thermal throttling:**

```bash
# Monitor GPU temperature
nvidia-smi -q -d TEMPERATURE

# GPU should be <85°C
# If thermal throttling, improve cooling
```

**Debugging Commands:**

```bash
# Benchmark inference speed
time ollama run qwen2.5:7b-instruct "Count from 1 to 10"

# Check GPU utilization during inference
watch -n 0.5 nvidia-smi

# Test with minimal prompt
curl http://localhost:11434/api/generate -d '{
  "model": "qwen2.5:7b-instruct",
  "prompt": "Hi",
  "stream": false
}'

# Check system load
top
htop

# Monitor Ollama logs for performance warnings
journalctl -u ollama -f | grep -i "slow\|performance"
```

---

## RAG Pipeline Issues

### Problem 14: Document Upload Fails

**Symptoms:**
- File upload returns 500 error
- Error: `Failed to process document`
- Upload progress bar freezes
- File appears in uploads but status is "failed"

**Cause:**
- File too large (exceeds MAX_UPLOAD_SIZE_MB)
- Unsupported file format
- Corrupted file
- Upload directory doesn't exist or lacks permissions
- PDF is encrypted or password-protected

**Solution:**

1. **Check file size:**

```bash
# In .env, increase max size if needed
MAX_UPLOAD_SIZE_MB=100  # Default: 50

# Check file size
ls -lh data/uploads/

# For files over limit, compress or split
```

2. **Verify file format is supported:**

```python
# Supported formats: .pdf, .docx, .txt, .md, .html
# Check file extension
file document.pdf
```

3. **Check upload directory exists:**

```bash
# Create upload directory if missing
mkdir -p data/uploads

# Check permissions
ls -ld data/uploads

# Should be writable by application user
chmod 755 data/uploads
```

4. **Test with small sample file:**

```bash
# Create test file
echo "Test document content" > test.txt

# Upload via API
curl -X POST http://localhost:8000/api/documents \
  -F "file=@test.txt"
```

5. **Check for PDF encryption:**

```bash
# Install pdfinfo (poppler-utils)
pdfinfo document.pdf | grep Encrypted

# If encrypted: "Encrypted: yes"
# Solution: Remove password or use unencrypted version
```

**Debugging Commands:**

```bash
# Check FastAPI logs for detailed error
docker-compose -f docker/docker-compose.yml logs api | grep -i "upload\|document"

# Example error logs:
# "ValueError: PDF is encrypted and cannot be read"
# "UnicodeDecodeError: 'utf-8' codec can't decode"
# "FileNotFoundError: [Errno 2] No such file or directory"

# Test document processor directly
docker-compose -f docker/docker-compose.yml run --rm api python -c "
from src.rag.document_processor import DocumentProcessor
from pathlib import Path

processor = DocumentProcessor()
text, pages = processor._extract_pdf_text(Path('/app/data/uploads/test.pdf'))
print(f'Extracted {pages} pages, {len(text)} characters')
"

# Check disk space
df -h data/uploads

# Monitor upload in real-time
tail -f logs/api.log | grep document_upload
```

---

### Problem 15: Embedding Generation Errors

**Symptoms:**
- Document status stuck at "processing"
- Error: `Failed to generate embeddings`
- Ollama embedding request times out
- Vector store insert fails

**Cause:**
- Embedding model not available in Ollama
- Ollama not running
- Text chunks too large
- Out of memory during embedding

**Solution:**

1. **Verify embedding model exists:**

```bash
# Check if embedding model is available
ollama list | grep embed

# Pull if missing
ollama pull nomic-embed-text

# Test embedding model
ollama run nomic-embed-text "test"
```

2. **Check .env configuration:**

```bash
# Verify embedding model name
cat .env | grep EMBEDDING_MODEL

# Should be:
EMBEDDING_MODEL=nomic-embed-text

# Alternative embedding models:
# EMBEDDING_MODEL=all-minilm  # Smaller, faster
# EMBEDDING_MODEL=mxbai-embed-large  # Higher quality
```

3. **Test embedding generation:**

```bash
# Test via API
curl http://localhost:11434/api/embeddings -d '{
  "model": "nomic-embed-text",
  "prompt": "Test embedding"
}'

# Should return vector of 768 dimensions
```

4. **Reduce chunk size if too large:**

```bash
# In .env
CHUNK_SIZE=500  # Reduce from 1000
CHUNK_OVERLAP=50
```

5. **Check Ollama memory:**

```bash
# Monitor during embedding
ollama ps
nvidia-smi  # If using GPU
```

**Debugging Commands:**

```bash
# Check document processing status in database
docker exec local-agent-mssql-backend /opt/mssql-tools18/bin/sqlcmd \
  -S localhost -U sa -P "LocalLLM@2024!" -d LLM_BackEnd -No \
  -Q "SELECT id, filename, status, error_message FROM app.documents ORDER BY uploaded_at DESC"

# Test embedding pipeline
docker-compose -f docker/docker-compose.yml run --rm api python -c "
from src.rag.embedder import OllamaEmbedder

embedder = OllamaEmbedder()
vector = embedder.embed('Test document chunk')
print(f'Generated vector with {len(vector)} dimensions')
"

# Check for errors in logs
docker-compose -f docker/docker-compose.yml logs api | grep -i "embedding\|vector"

# Monitor embedding API calls
curl -N http://localhost:11434/api/embeddings -d '{
  "model": "nomic-embed-text",
  "prompt": "Long text chunk here..."
}' | jq '.embedding | length'
```

---

### Problem 16: Vector Search Returns No Results

**Symptoms:**
- RAG search returns empty results
- Query documents endpoint returns 0 matches
- Relevant documents exist but aren't found

**Cause:**
- Embeddings not indexed in vector store
- Vector store type mismatch (MSSQL vs Redis)
- Search similarity threshold too strict
- Vector dimensions mismatch
- Database connection to wrong SQL Server instance

**Solution:**

1. **Verify documents are indexed:**

```bash
# Check SQL Server vector store
docker exec local-agent-mssql-backend /opt/mssql-tools18/bin/sqlcmd \
  -S localhost -U sa -P "LocalLLM@2024!" -d LLM_BackEnd -No \
  -Q "SELECT COUNT(*) as total_chunks FROM vectors.document_chunks"

# Check Redis vector store (if using Redis)
docker exec local-agent-redis redis-cli FT._LIST
docker exec local-agent-redis redis-cli FT.INFO idx:documents
```

2. **Check vector store configuration:**

```bash
# In .env
VECTOR_STORE_TYPE=mssql  # or "redis"
VECTOR_DIMENSIONS=768    # Must match embedding model

# Verify embedding model dimensions
# nomic-embed-text = 768
# all-minilm = 384
# mxbai-embed-large = 1024
```

3. **Adjust search parameters:**

```bash
# Lower similarity threshold
RAG_TOP_K=10  # Return more results
RAG_MIN_SIMILARITY=0.5  # Lower threshold (default: 0.7)
```

4. **Re-index documents:**

```bash
# Delete and re-upload documents
curl -X DELETE http://localhost:8000/api/documents/{document_id}

# Re-upload
curl -X POST http://localhost:8000/api/documents \
  -F "file=@document.pdf"
```

5. **Test vector search directly:**

```bash
# Generate test embedding
curl http://localhost:11434/api/embeddings -d '{
  "model": "nomic-embed-text",
  "prompt": "What is machine learning?"
}' > query_vector.json

# Search in SQL Server
docker exec local-agent-mssql-backend /opt/mssql-tools18/bin/sqlcmd \
  -S localhost -U sa -P "LocalLLM@2024!" -d LLM_BackEnd -No \
  -Q "SELECT TOP 5 chunk_id, chunk_text,
      VECTOR_DISTANCE('cosine', embedding, <vector>) as similarity
      FROM vectors.document_chunks
      ORDER BY similarity DESC"
```

**Debugging Commands:**

```bash
# Check if embeddings exist
docker exec local-agent-mssql-backend /opt/mssql-tools18/bin/sqlcmd \
  -S localhost -U sa -P "LocalLLM@2024!" -d LLM_BackEnd -No \
  -Q "SELECT document_id, chunk_id,
      LEN(CAST(embedding AS VARCHAR(MAX))) as embedding_size
      FROM vectors.document_chunks"

# Verify vector dimensions
docker exec local-agent-mssql-backend /opt/mssql-tools18/bin/sqlcmd \
  -S localhost -U sa -P "LocalLLM@2024!" -d LLM_BackEnd -No \
  -Q "SELECT TOP 1 embedding.Length() as dimensions FROM vectors.document_chunks"

# Test similarity calculation
curl -X POST http://localhost:8000/api/documents/search -H "Content-Type: application/json" -d '{
  "query": "machine learning algorithms",
  "top_k": 10
}'

# Check for indexing errors
docker-compose -f docker/docker-compose.yml logs api | grep -i "vector\|index\|embed"
```

---

## Frontend Issues

### Problem 17: React Frontend Won't Start

**Symptoms:**
- `npm run dev` fails
- Port 5173 already in use
- Build errors on startup
- Blank page in browser

**Cause:**
- Dependencies not installed
- Port conflict
- Node.js version too old
- Build cache corruption

**Solution:**

1. **Install dependencies:**

```bash
cd frontend
npm install

# If errors, clear cache and reinstall
npm cache clean --force
rm -rf node_modules package-lock.json
npm install
```

2. **Check Node.js version:**

```bash
node --version

# Required: 18+
# Update if needed:
# - Windows: Download from nodejs.org
# - Mac: brew upgrade node
# - Linux: nvm install 18
```

3. **Fix port conflict:**

```bash
# Check what's using port 5173
# Windows
netstat -ano | findstr 5173

# Linux/Mac
lsof -i :5173

# Kill process or use different port
# In frontend/.env.local
VITE_PORT=5174
```

4. **Clear build cache:**

```bash
cd frontend
rm -rf dist .vite node_modules/.vite
npm run dev
```

**Debugging Commands:**

```bash
# Check for build errors
cd frontend
npm run dev -- --debug

# Test Vite config
npm run dev -- --host 0.0.0.0 --port 5173

# Check dependencies
npm list --depth=0

# Verify proxy configuration
cat vite.config.ts | grep proxy

# Test API connection
curl http://localhost:8000/api/health

# Check browser console (F12) for errors
# Common errors:
# - "Failed to fetch" → API not running
# - "CORS error" → Proxy misconfigured
# - "Module not found" → Missing dependency
```

---

### Problem 18: WebSocket Connection Failed

**Symptoms:**
- Chat messages don't stream in real-time
- Connection status shows "Disconnected"
- Browser console: `WebSocket connection to 'ws://localhost:8000/ws/agent/...' failed`
- Messages appear all at once instead of streaming

**Cause:**
- FastAPI backend not running
- WebSocket endpoint path incorrect
- Proxy not forwarding WebSocket connections
- CORS issues

**Solution:**

1. **Verify FastAPI is running:**

```bash
# Check API health
curl http://localhost:8000/api/health

# Check WebSocket endpoint exists
curl http://localhost:8000/docs
# Look for /ws/agent/{conversation_id}
```

2. **Test WebSocket connection:**

```bash
# Install wscat
npm install -g wscat

# Test WebSocket
wscat -c ws://localhost:8000/ws/agent/test-123

# Should connect and accept messages
```

3. **Check Vite proxy configuration:**

```typescript
// frontend/vite.config.ts
export default defineConfig({
  server: {
    proxy: {
      '/ws': {
        target: 'http://localhost:8000',
        ws: true,  // ← Must be true for WebSocket
        changeOrigin: true,
      },
    },
  },
})
```

4. **Verify WebSocket URL in frontend:**

```typescript
// frontend/src/api/client.ts
const wsUrl = `ws://localhost:8000/ws/agent/${conversationId}`
// Not: `ws://localhost:5173/ws/...`
```

**Debugging Commands:**

```bash
# Monitor WebSocket connections on backend
docker-compose -f docker/docker-compose.yml logs -f api | grep -i websocket

# Check active WebSocket connections
# In FastAPI app, add logging:
logger.info(f"WebSocket client connected: {client_id}")

# Test from browser console (F12)
const ws = new WebSocket('ws://localhost:8000/ws/agent/test-123');
ws.onopen = () => console.log('Connected');
ws.onerror = (e) => console.error('Error:', e);
ws.onmessage = (e) => console.log('Message:', e.data);
ws.send(JSON.stringify({message: 'Hello'}));

# Check nginx/proxy logs if using reverse proxy
tail -f /var/log/nginx/access.log | grep ws
```

---

### Problem 19: API Connection Refused (CORS Error)

**Symptoms:**
- Browser console: `Access to fetch at 'http://localhost:8000/api/...' has been blocked by CORS policy`
- API requests fail with network error
- Red CORS errors in DevTools Network tab

**Cause:**
- FastAPI CORS middleware not configured
- Origin mismatch (localhost vs 127.0.0.1)
- Vite proxy not working

**Solution:**

1. **Check FastAPI CORS configuration:**

```python
# src/api/main.py should have:
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

2. **Use consistent origin:**

```bash
# Always use localhost, not 127.0.0.1
# ✅ http://localhost:5173
# ❌ http://127.0.0.1:5173
```

3. **Verify Vite proxy:**

```typescript
// frontend/vite.config.ts
server: {
  proxy: {
    '/api': {
      target: 'http://localhost:8000',
      changeOrigin: true,
    },
  },
}
```

4. **Test without proxy:**

```bash
# Temporarily allow all origins (development only!)
# In src/api/main.py:
allow_origins=["*"]

# Restart API
docker-compose -f docker/docker-compose.yml restart api
```

**Debugging Commands:**

```bash
# Check CORS headers in response
curl -I http://localhost:8000/api/health \
  -H "Origin: http://localhost:5173"

# Should include:
# Access-Control-Allow-Origin: http://localhost:5173
# Access-Control-Allow-Credentials: true

# Test preflight request (OPTIONS)
curl -X OPTIONS http://localhost:8000/api/health \
  -H "Origin: http://localhost:5173" \
  -H "Access-Control-Request-Method: GET" \
  -v

# Check browser DevTools Network tab:
# 1. Look for OPTIONS request before actual request
# 2. Check Response Headers for Access-Control-*
# 3. Check Console for exact CORS error message
```

---

## General Issues

### Problem 20: Environment Variables Not Loading

**Symptoms:**
- Application uses default values instead of .env values
- Error: `KeyError: 'OLLAMA_MODEL'`
- Services connect to wrong ports
- Passwords don't match

**Cause:**
- .env file missing
- .env file in wrong location
- .env file not loaded by application
- Docker Compose not finding .env

**Solution:**

1. **Verify .env exists:**

```bash
ls -la .env

# Should be in project root:
# E:\Repos\GitHub\MyDemoRepos\local-llm-research-agent\.env
```

2. **Check .env format:**

```bash
# No spaces around =
# ✅ OLLAMA_MODEL=qwen2.5:7b-instruct
# ❌ OLLAMA_MODEL = qwen2.5:7b-instruct

# No quotes needed (usually)
# ✅ SQL_PASSWORD=MyPass123!
# ❌ SQL_PASSWORD="MyPass123!"  # Only if password contains spaces

# Check for common errors
cat .env | grep "= \| ="
```

3. **Load .env in Docker Compose:**

```bash
# Always use --env-file when running from project root
docker-compose -f docker/docker-compose.yml --env-file .env up -d

# Or run from docker/ directory
cd docker
docker-compose up -d  # .env is discovered automatically here
```

4. **Load .env in Python:**

```python
# Verify python-dotenv is loading .env
from dotenv import load_dotenv
import os

load_dotenv()
print(os.getenv('OLLAMA_MODEL'))  # Should print model name, not None
```

**Debugging Commands:**

```bash
# Check which variables are loaded
set | grep OLLAMA  # Windows CMD
env | grep OLLAMA  # Linux/Mac/PowerShell

# Test docker-compose config
docker-compose -f docker/docker-compose.yml --env-file .env config | grep -A 5 "environment:"

# Check variables inside container
docker exec local-agent-api env | grep OLLAMA

# Verify .env file contents
cat .env | grep -v "^#" | grep -v "^$"  # Show non-empty, non-comment lines

# Check for hidden characters (BOM, etc.)
file .env
# Should say: ASCII text

# Check line endings
dos2unix -info .env  # Should be LF, not CRLF on Linux
```

---

### Problem 21: Import Errors (ModuleNotFoundError)

**Symptoms:**
- `ModuleNotFoundError: No module named 'pydantic_ai'`
- Application crashes on import
- Error: `cannot import name 'X' from 'Y'`

**Cause:**
- Dependencies not installed
- Virtual environment not activated
- Wrong Python version
- Package version mismatch

**Solution:**

1. **Install dependencies:**

```bash
# Using uv (recommended)
uv sync

# Or using pip
pip install -r requirements.txt

# Force reinstall
uv sync --reinstall
```

2. **Activate virtual environment:**

```bash
# Check if venv is activated
which python  # Should point to project .venv

# Activate manually
# Windows
.venv\Scripts\activate

# Linux/Mac
source .venv/bin/activate

# Or use uv run
uv run python -m src.main
```

3. **Check Python version:**

```bash
python --version

# Required: 3.11+
# If wrong version, use pyenv or install correct Python
```

4. **Clear Python cache:**

```bash
# Remove cached bytecode
find . -type d -name __pycache__ -exec rm -rf {} +
find . -type f -name "*.pyc" -delete

# Clear pip cache
pip cache purge
```

**Debugging Commands:**

```bash
# Check installed packages
pip list | grep pydantic

# Verify package location
python -c "import pydantic_ai; print(pydantic_ai.__file__)"

# Check sys.path
python -c "import sys; print('\n'.join(sys.path))"

# Test import directly
python -c "from src.agent.core import ResearchAgent; print('OK')"

# Check for conflicting packages
pip check

# Show dependency tree
pipdeptree -p pydantic-ai
```

---

### Problem 22: Test Failures

**Symptoms:**
- `pytest` fails with errors
- Tests pass locally but fail in CI
- Database tests fail with connection errors
- Async tests hang

**Cause:**
- Test database not configured
- Fixtures not set up correctly
- Async event loop issues
- Missing test dependencies

**Solution:**

1. **Install test dependencies:**

```bash
# Install with test extras
pip install -e ".[test]"

# Or using uv
uv sync --extra test
```

2. **Configure test database:**

```bash
# In .env.test
SQL_DATABASE_NAME=ResearchAnalytics_Test
BACKEND_DB_NAME=LLM_BackEnd_Test

# Create test databases
docker exec local-agent-mssql /opt/mssql-tools18/bin/sqlcmd \
  -S localhost -U sa -P "LocalLLM@2024!" -No \
  -Q "CREATE DATABASE ResearchAnalytics_Test"
```

3. **Run tests with correct markers:**

```bash
# Run unit tests only (fast, no dependencies)
pytest -m unit

# Run integration tests (requires services)
pytest -m integration

# Skip slow tests
pytest -m "not slow"

# Run with verbose output
pytest -v --tb=short
```

4. **Fix async test issues:**

```python
# tests/conftest.py
import pytest
import asyncio

@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()
```

**Debugging Commands:**

```bash
# Run specific test with debugging
pytest tests/test_agent.py::test_agent_responds -v -s

# Show all print statements
pytest -v -s

# Stop on first failure
pytest -x

# Run tests in parallel (if pytest-xdist installed)
pytest -n auto

# Generate coverage report
pytest --cov=src --cov-report=html
open htmlcov/index.html

# Check for test collection errors
pytest --collect-only

# Run with maximum verbosity
pytest -vv --tb=long --show-capture=all
```

---

### Problem 23: Alembic Migration Errors

**Symptoms:**
- `alembic upgrade head` fails
- Error: `Target database is not up to date`
- Migration generates empty file
- Conflict between migrations

**Cause:**
- Database not initialized
- Migration history out of sync
- Multiple migration heads
- Schema manually modified

**Solution:**

1. **Check migration status:**

```bash
# Show current version
alembic current

# Show all migrations
alembic history

# Check for multiple heads
alembic heads
```

2. **Initialize database:**

```bash
# Stamp database with current version
alembic stamp head

# Or start from scratch
alembic upgrade head
```

3. **Fix multiple heads:**

```bash
# Merge heads
alembic merge heads -m "merge migrations"
alembic upgrade head
```

4. **Reset migration history:**

```bash
# WARNING: Only for development!
# Drop all tables
docker exec local-agent-mssql-backend /opt/mssql-tools18/bin/sqlcmd \
  -S localhost -U sa -P "LocalLLM@2024!" -d LLM_BackEnd -No \
  -Q "EXEC sp_MSforeachtable 'DROP TABLE ?'"

# Delete alembic_version table
docker exec local-agent-mssql-backend /opt/mssql-tools18/bin/sqlcmd \
  -S localhost -U sa -P "LocalLLM@2024!" -d LLM_BackEnd -No \
  -Q "DROP TABLE alembic_version"

# Run migrations fresh
alembic upgrade head
```

**Debugging Commands:**

```bash
# Generate migration with SQL output
alembic upgrade head --sql

# Show SQL for specific migration
alembic upgrade abc123:def456 --sql

# Downgrade one version
alembic downgrade -1

# Check migration file syntax
python -m py_compile alembic/versions/abc123_migration.py

# Verify database schema
docker exec local-agent-mssql-backend /opt/mssql-tools18/bin/sqlcmd \
  -S localhost -U sa -P "LocalLLM@2024!" -d LLM_BackEnd -No \
  -Q "SELECT TABLE_SCHEMA, TABLE_NAME FROM INFORMATION_SCHEMA.TABLES ORDER BY TABLE_SCHEMA, TABLE_NAME"

# Check alembic version table
docker exec local-agent-mssql-backend /opt/mssql-tools18/bin/sqlcmd \
  -S localhost -U sa -P "LocalLLM@2024!" -d LLM_BackEnd -No \
  -Q "SELECT * FROM alembic_version"
```

---

### Problem 24: MCP Server Won't Start

**Symptoms:**
- Error: `ENOENT: no such file or directory`
- MCP tools not available in agent
- Agent says "I don't have database tools"
- Connection timeout to MCP server

**Cause:**
- MCP_MSSQL_PATH incorrect or missing
- Node.js not installed or wrong version
- MCP server dependencies not installed
- Environment variables not passed to MCP server

**Solution:**

1. **Verify MCP path exists:**

```bash
# Check path in .env
cat .env | grep MCP_MSSQL_PATH

# Verify file exists
ls -la $MCP_MSSQL_PATH

# Example correct path:
# Windows: E:\SQL-AI-samples\MssqlMcp\Node\dist\index.js
# Linux: /home/user/SQL-AI-samples/MssqlMcp/Node/dist/index.js
```

2. **Install/rebuild MCP server:**

```bash
# Clone if not exists
git clone https://github.com/Azure-Samples/SQL-AI-samples.git
cd SQL-AI-samples/MssqlMcp/Node

# Install dependencies
npm install

# Build
npm run build

# Verify build output
ls -la dist/index.js
```

3. **Check Node.js version:**

```bash
node --version

# Required: v18 or higher
# Update if needed
```

4. **Test MCP server directly:**

```bash
# Run MCP server manually
node $MCP_MSSQL_PATH

# Should not exit immediately
# Press Ctrl+C to stop
```

5. **Check MCP configuration:**

```json
// mcp_config.json
{
  "mcpServers": {
    "mssql": {
      "command": "node",
      "args": ["E:\\path\\to\\dist\\index.js"],  // Use full path
      "env": {
        "SERVER_NAME": "localhost",
        "DATABASE_NAME": "ResearchAnalytics",
        "TRUST_SERVER_CERTIFICATE": "true"
      }
    }
  }
}
```

**Debugging Commands:**

```bash
# Test MCP server with environment variables
export SERVER_NAME=localhost
export DATABASE_NAME=ResearchAnalytics
export TRUST_SERVER_CERTIFICATE=true
node $MCP_MSSQL_PATH

# Check if MCP server can connect to SQL Server
node -e "
const { Client } = require('pg');  // Example test
console.log('Testing SQL Server connection...');
"

# Run agent with MCP debugging
DEBUG=mcp:* uv run python -m src.cli.chat

# Check MCP server logs in application
docker-compose -f docker/docker-compose.yml logs api | grep -i mcp

# Test tool execution
uv run python -c "
import asyncio
from src.mcp.client import get_mcp_client

async def test():
    async with get_mcp_client() as client:
        tools = await client.list_tools()
        print(f'Available tools: {[t.name for t in tools]}')

asyncio.run(test())
"
```

---

### Problem 25: High CPU/Memory Usage

**Symptoms:**
- System becomes slow
- CPU at 100% for extended periods
- Memory usage growing over time
- Application crashes with OOM

**Cause:**
- Large model loaded in memory
- Memory leak in application
- Too many concurrent requests
- No connection pooling
- Embedding generation for large documents

**Solution:**

1. **Monitor resource usage:**

```bash
# Check overall system
top
htop

# Check Docker containers
docker stats

# Check specific process
ps aux | grep ollama
ps aux | grep python
```

2. **Use smaller LLM model:**

```bash
# In .env, switch to smaller model
OLLAMA_MODEL=qwen2.5:3b-instruct  # 2GB vs 7GB

# Or quantized
OLLAMA_MODEL=qwen2.5:7b-q4_K_M  # ~4GB vs 7GB
```

3. **Limit concurrent requests:**

```python
# In FastAPI main.py, add rate limiting
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter

@app.on_event("startup")
async def startup():
    await FastAPILimiter.init(redis)

@app.post("/api/agent/chat", dependencies=[Depends(RateLimiter(times=10, seconds=60))])
```

4. **Configure connection pooling:**

```python
# In database configuration
engine = create_async_engine(
    connection_string,
    pool_size=5,           # Max connections
    max_overflow=10,       # Extra connections
    pool_pre_ping=True,    # Verify connections
    pool_recycle=3600,     # Recycle after 1 hour
)
```

5. **Optimize document processing:**

```bash
# Process documents in smaller chunks
CHUNK_SIZE=500  # Smaller chunks
RAG_BATCH_SIZE=10  # Process 10 chunks at a time
```

**Debugging Commands:**

```bash
# Profile Python application
uv run python -m cProfile -o profile.stats -m src.main
python -m pstats profile.stats

# Check for memory leaks with memray
pip install memray
memray run -o output.bin python -m src.main
memray flamegraph output.bin

# Monitor Ollama memory
watch -n 1 "ollama ps && nvidia-smi"

# Check database connection pool
docker exec local-agent-mssql-backend /opt/mssql-tools18/bin/sqlcmd \
  -S localhost -U sa -P "LocalLLM@2024!" -d LLM_BackEnd -No \
  -Q "SELECT DB_NAME(dbid) as DB, COUNT(*) as Connections
      FROM sys.sysprocesses
      GROUP BY DB_NAME(dbid)"

# Find slow queries
docker exec local-agent-mssql-backend /opt/mssql-tools18/bin/sqlcmd \
  -S localhost -U sa -P "LocalLLM@2024!" -d LLM_BackEnd -No \
  -Q "SELECT TOP 10
      total_worker_time/execution_count as avg_cpu,
      total_elapsed_time/execution_count as avg_time,
      SUBSTRING(text, 1, 100) as query_text
      FROM sys.dm_exec_query_stats
      CROSS APPLY sys.dm_exec_sql_text(sql_handle)
      ORDER BY avg_cpu DESC"

# Check for memory leaks in FastAPI
curl http://localhost:8000/api/health/metrics

# Force garbage collection
uv run python -c "import gc; gc.collect(); print('GC done')"
```

---

## Diagnostic Scripts

### Complete System Check Script

Save as `diagnose.sh` and run with `bash diagnose.sh`:

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
echo "Ollama: $(ollama --version 2>&1 || echo 'Not installed')"

echo ""
echo "--- LLM Providers ---"
echo "Ollama:"
curl -s http://localhost:11434/api/tags 2>/dev/null | head -c 200 || echo "  Not running"
echo ""

echo ""
echo "--- Docker Containers ---"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null | grep -E "(NAMES|agent)"

echo ""
echo "--- SQL Server 2022 (Sample) ---"
docker exec local-agent-mssql /opt/mssql-tools18/bin/sqlcmd \
  -S localhost -U sa -P "${MSSQL_SA_PASSWORD:-LocalLLM@2024!}" -No \
  -Q "SELECT @@VERSION" 2>/dev/null | head -1 || echo "Not accessible"

echo ""
echo "--- SQL Server 2025 (Backend) ---"
docker exec local-agent-mssql-backend /opt/mssql-tools18/bin/sqlcmd \
  -S localhost -U sa -P "${MSSQL_SA_PASSWORD:-LocalLLM@2024!}" -No \
  -Q "SELECT @@VERSION" 2>/dev/null | head -1 || echo "Not accessible"

echo ""
echo "--- Redis ---"
docker exec local-agent-redis redis-cli PING 2>/dev/null || echo "Not accessible"

echo ""
echo "--- FastAPI ---"
curl -s http://localhost:8000/api/health 2>/dev/null | jq -r '.status // "Not accessible"' || echo "Not accessible"

echo ""
echo "--- React Frontend ---"
curl -s -o /dev/null -w "%{http_code}" http://localhost:5173 2>/dev/null || echo "Not accessible"

echo ""
echo "--- Configuration Summary ---"
grep -E "^(LLM_PROVIDER|OLLAMA_|SQL_|MCP_|VECTOR_)" .env 2>/dev/null | \
  sed 's/PASSWORD=.*/PASSWORD=***HIDDEN***/' || echo "No .env file"

echo ""
echo "=== End Diagnostics ==="
```

### Log Collection Script

Save as `collect-logs.sh`:

```bash
#!/bin/bash
LOGDIR="debug-logs-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$LOGDIR"

echo "Collecting logs to $LOGDIR..."

# Docker logs
docker logs local-agent-mssql > "$LOGDIR/mssql.log" 2>&1
docker logs local-agent-mssql-backend > "$LOGDIR/mssql-backend.log" 2>&1
docker logs local-agent-redis > "$LOGDIR/redis.log" 2>&1
docker logs local-agent-api > "$LOGDIR/api.log" 2>&1
docker logs local-agent-frontend > "$LOGDIR/frontend.log" 2>&1

# System info
docker ps > "$LOGDIR/docker-ps.txt"
docker stats --no-stream > "$LOGDIR/docker-stats.txt"

# Configuration (sanitized)
cat .env | sed 's/PASSWORD=.*/PASSWORD=***/' > "$LOGDIR/env.txt" 2>/dev/null

# Health check
curl -s http://localhost:8000/api/health | jq . > "$LOGDIR/health.json" 2>/dev/null

echo "Logs collected in $LOGDIR/"
tar czf "$LOGDIR.tar.gz" "$LOGDIR"
echo "Archive created: $LOGDIR.tar.gz"
```

---

## Getting Help

### Before Asking for Help

1. Run the diagnostic script above
2. Check this troubleshooting guide for your issue
3. Review the [Configuration Guide](configuration.md)
4. Search existing [GitHub Issues](https://github.com/yourusername/local-llm-research-agent/issues)

### Information to Include

When reporting an issue, include:

| Information | How to Get It |
|-------------|---------------|
| Error message | Full stack trace from logs |
| OS version | `uname -a` (Linux/Mac) or `winver` (Windows) |
| Python version | `python --version` |
| Docker version | `docker --version` |
| Node.js version | `node --version` |
| Ollama version | `ollama --version` |
| LLM provider | Check `LLM_PROVIDER` in .env |
| Container status | `docker ps` |
| Recent logs | Run `collect-logs.sh` script |
| Configuration | `.env` settings (redact passwords!) |

### Getting Support

- **GitHub Issues:** [Report a bug](https://github.com/yourusername/local-llm-research-agent/issues/new?template=bug_report.md)
- **Discussions:** [Ask questions](https://github.com/yourusername/local-llm-research-agent/discussions)
- **Documentation:** [Read the docs](https://github.com/yourusername/local-llm-research-agent/tree/main/docs)

### Tips for Effective Bug Reports

1. **Be specific:** Include exact error messages
2. **Be complete:** Provide full context (what you were doing, what you expected)
3. **Be concise:** Use code blocks and formatting
4. **Be safe:** Never share passwords or API keys
5. **Be helpful:** Include what you've already tried

---

## Error Code Reference

### Common Error Codes

| Error Code | Component | Meaning | Solution |
|-----------|-----------|---------|----------|
| ECONNREFUSED | Network | Service not running | Start the service |
| ENOENT | Filesystem | File not found | Check path configuration |
| ETIMEDOUT | Network | Connection timeout | Check firewall/network |
| EADDRINUSE | Network | Port already in use | Stop conflicting service |
| OOM | Memory | Out of memory | Use smaller model |
| 401 | HTTP | Unauthorized | Check credentials |
| 403 | HTTP | Forbidden | Check permissions |
| 404 | HTTP | Not found | Check URL/endpoint |
| 500 | HTTP | Internal server error | Check server logs |
| 18456 | SQL Server | Login failed | Check SQL credentials |
| 4060 | SQL Server | Cannot open database | Database doesn't exist |
| 233 | SQL Server | Connection init failed | Server not ready |

---

*Last Updated: December 2025*
*Covers 25 common issues with detailed solutions*
