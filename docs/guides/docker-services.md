# Docker Services Guide

> **Complete guide to running and testing all Docker services**

---

## Table of Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Service Profiles](#service-profiles)
- [Individual Services](#individual-services)
- [Testing Each Service](#testing-each-service)
- [Sample Use Cases](#sample-use-cases)
- [Troubleshooting](#troubleshooting)

---

## Overview

The Local LLM Research Agent runs as a set of Docker services under the `local-agent-ai-stack` project.

### Services Summary

| Service | Container | Port(s) | Description |
|---------|-----------|---------|-------------|
| **mssql** | `local-agent-mssql` | 1433 | SQL Server 2022 database |
| **redis-stack** | `local-agent-redis` | 6379, 8001* | Redis + Vector Search + RedisInsight |
| **agent-ui** | `local-agent-streamlit-ui` | 8501 | Streamlit web interface |
| **api** | `local-agent-api` | 8000 | FastAPI backend with RAG |
| **agent-cli** | `local-agent-cli` | - | Interactive CLI chat |
| **mssql-tools** | `local-agent-mssql-tools` | - | Database initialization |

> *RedisInsight port is configurable via `REDIS_INSIGHT_PORT`

---

## Prerequisites

1. **Docker Desktop** installed and running
2. **Ollama** running on host with a model pulled:
   ```bash
   ollama pull qwen2.5:7b-instruct
   ```
3. **Environment file** (`.env`) configured at project root
4. **Docker volumes** created:
   ```bash
   docker volume create local-llm-mssql-data
   docker volume create local-llm-redis-data
   ```

---

## Quick Start

### First Time Setup

```bash
# 1. Create volumes (one time only)
docker volume create local-llm-mssql-data
docker volume create local-llm-redis-data

# 2. Start core services
docker-compose -f docker/docker-compose.yml --env-file .env up -d

# 3. Initialize database with sample data
docker-compose -f docker/docker-compose.yml --env-file .env --profile init up mssql-tools

# 4. Verify all services are healthy
docker ps -a --filter name=local-agent
```

### Start Everything (Full Stack)

```bash
docker-compose -f docker/docker-compose.yml --env-file .env --profile full up -d
```

### Stop Everything

```bash
# Stop containers (preserves data)
docker-compose -f docker/docker-compose.yml down

# Stop and DELETE all data (destructive!)
docker-compose -f docker/docker-compose.yml down -v
```

---

## Service Profiles

Profiles allow you to start different combinations of services:

| Profile | Command | Services Started |
|---------|---------|------------------|
| **Default** | `up -d` | mssql, redis-stack, agent-ui |
| **API** | `--profile api up -d` | + api |
| **CLI** | `--profile cli run agent-cli` | + agent-cli |
| **Full** | `--profile full up -d` | mssql, redis-stack, agent-ui, api |
| **Init** | `--profile init up mssql-tools` | + mssql-tools (for DB setup) |

### Examples

```bash
# Default: Core services + Web UI
docker-compose -f docker/docker-compose.yml --env-file .env up -d

# Full stack: Everything including FastAPI
docker-compose -f docker/docker-compose.yml --env-file .env --profile full up -d

# Add API to running services
docker-compose -f docker/docker-compose.yml --env-file .env --profile api up -d

# Interactive CLI session
docker-compose -f docker/docker-compose.yml --env-file .env --profile cli run --rm agent-cli
```

---

## Individual Services

### 1. SQL Server (mssql)

**Purpose:** Primary database for research analytics data.

**Connection Details:**
| Setting | Value |
|---------|-------|
| Server | `localhost,1433` |
| Database | `ResearchAnalytics` |
| Username | `sa` |
| Password | See `MSSQL_SA_PASSWORD` in `.env` |
| Trust Certificate | Yes |

**Start:**
```bash
docker-compose -f docker/docker-compose.yml --env-file .env up -d mssql
```

**Test Connection:**
```bash
# From host (requires sqlcmd installed)
sqlcmd -S localhost,1433 -U sa -P "LocalLLM@2024!" -C -Q "SELECT @@VERSION"

# From inside container
docker exec local-agent-mssql /opt/mssql-tools18/bin/sqlcmd \
  -S localhost -U sa -P "$MSSQL_SA_PASSWORD" -C -Q "SELECT name FROM sys.databases"
```

**Sample Queries:**
```sql
-- List all tables
SELECT TABLE_NAME FROM ResearchAnalytics.INFORMATION_SCHEMA.TABLES;

-- Count researchers
SELECT COUNT(*) AS TotalResearchers FROM Researchers;

-- Top funded projects
SELECT TOP 5 p.ProjectName, SUM(f.Amount) as TotalFunding
FROM Projects p
JOIN Funding f ON p.ProjectId = f.ProjectId
GROUP BY p.ProjectName
ORDER BY TotalFunding DESC;
```

---

### 2. Redis Stack (redis-stack)

**Purpose:** Vector search, caching, and session storage for RAG pipeline.

**Connection Details:**
| Setting | Value |
|---------|-------|
| URL | `redis://localhost:6379` |
| RedisInsight GUI | `http://localhost:8001` (or `REDIS_INSIGHT_PORT`) |

**Start:**
```bash
docker-compose -f docker/docker-compose.yml --env-file .env up -d redis-stack
```

**Test Connection:**
```bash
# Ping test
docker exec local-agent-redis redis-cli PING
# Expected: PONG

# Check info
docker exec local-agent-redis redis-cli INFO server | head -10

# List keys (if any exist)
docker exec local-agent-redis redis-cli KEYS "*"
```

**Access RedisInsight GUI:**
1. Open browser to `http://localhost:8001` (or your configured `REDIS_INSIGHT_PORT`)
2. Click "Add Redis Database"
3. Use: Host=`localhost`, Port=`6379`

**Sample Redis Commands:**
```bash
# Set a test key
docker exec local-agent-redis redis-cli SET test:key "Hello World"

# Get the key
docker exec local-agent-redis redis-cli GET test:key

# Check vector search module is loaded
docker exec local-agent-redis redis-cli MODULE LIST
```

---

### 3. Streamlit UI (agent-ui)

**Purpose:** Web-based chat interface for interacting with the research agent.

**Access:** `http://localhost:8501`

**Start:**
```bash
docker-compose -f docker/docker-compose.yml --env-file .env up -d agent-ui
```

**Test:**
```bash
# Check health
curl http://localhost:8501/_stcore/health

# View logs
docker logs local-agent-streamlit-ui -f
```

**Sample Use Cases:**
1. Open `http://localhost:8501` in browser
2. Try these queries:
   - "What tables are in the database?"
   - "Show me the top 5 researchers by salary"
   - "How many active projects are there?"
   - "Which department has the highest budget?"

---

### 4. FastAPI Backend (api)

**Purpose:** REST API for programmatic access, RAG pipeline, and document management.

**Access:**
| Endpoint | URL |
|----------|-----|
| API Docs (Swagger) | `http://localhost:8000/docs` |
| ReDoc | `http://localhost:8000/redoc` |
| Health Check | `http://localhost:8000/api/health/live` |
| OpenAPI Spec | `http://localhost:8000/openapi.json` |

**Start:**
```bash
docker-compose -f docker/docker-compose.yml --env-file .env --profile api up -d
# Or with full profile:
docker-compose -f docker/docker-compose.yml --env-file .env --profile full up -d
```

**Test:**
```bash
# Health check
curl http://localhost:8000/api/health/live

# Ready check (all dependencies)
curl http://localhost:8000/api/health/ready

# API documentation
curl http://localhost:8000/openapi.json | jq '.info'
```

**Sample API Calls:**
```bash
# Chat with the agent
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What tables are in the database?"}'

# List available MCP tools
curl http://localhost:8000/api/mcp/tools

# Upload a document for RAG
curl -X POST http://localhost:8000/api/documents/upload \
  -F "file=@mydocument.pdf"

# Search documents
curl "http://localhost:8000/api/documents/search?query=machine+learning"
```

---

### 5. Interactive CLI (agent-cli)

**Purpose:** Command-line chat interface for terminal-based interaction.

**Start (Interactive):**
```bash
docker-compose -f docker/docker-compose.yml --env-file .env --profile cli run --rm agent-cli
```

**Sample Session:**
```
🤖 Local LLM Research Agent
Type 'help' for commands, 'quit' to exit

You: What tables are in the database?
Agent: The database contains the following tables:
- Departments (8 records)
- Researchers (23 records)
- Projects (14 records)
...

You: Show me researchers in the AI department
Agent: [Query results displayed]

You: export json
✅ Exported to chat_20241210_143022.json

You: quit
```

**CLI Commands:**
| Command | Description |
|---------|-------------|
| `help` | Show all commands |
| `clear` | Clear conversation |
| `status` | Show connection status |
| `cache` | Show cache statistics |
| `cache-clear` | Clear response cache |
| `export json` | Export conversation to JSON |
| `export csv` | Export to CSV |
| `export md` | Export to Markdown |
| `history` | List saved sessions |
| `history save` | Save current session |
| `quit` | Exit the CLI |

---

### 6. Database Initialization (mssql-tools)

**Purpose:** One-time database setup with schema and sample data.

**Run:**
```bash
docker-compose -f docker/docker-compose.yml --env-file .env --profile init up mssql-tools
```

**What it does:**
1. Executes `01-create-database.sql` - Creates ResearchAnalytics database
2. Executes `02-create-schema.sql` - Creates all tables and views
3. Executes `03-seed-data.sql` - Inserts sample research data

**Verify:**
```bash
# Check tables were created
docker exec local-agent-mssql /opt/mssql-tools18/bin/sqlcmd \
  -S localhost -U sa -P "$MSSQL_SA_PASSWORD" -C \
  -Q "SELECT TABLE_NAME FROM ResearchAnalytics.INFORMATION_SCHEMA.TABLES"
```

---

## Testing Each Service

### Quick Health Check Script

Run this to verify all services are working:

```bash
echo "=== Checking Container Status ==="
docker ps -a --filter name=local-agent --format "table {{.Names}}\t{{.Status}}"

echo -e "\n=== SQL Server Test ==="
docker exec local-agent-mssql /opt/mssql-tools18/bin/sqlcmd \
  -S localhost -U sa -P "LocalLLM@2024!" -C \
  -Q "SELECT COUNT(*) as TableCount FROM ResearchAnalytics.INFORMATION_SCHEMA.TABLES"

echo -e "\n=== Redis Test ==="
docker exec local-agent-redis redis-cli PING

echo -e "\n=== Streamlit UI Test ==="
curl -s http://localhost:8501/_stcore/health && echo "OK" || echo "FAILED"

echo -e "\n=== FastAPI Test (if running) ==="
curl -s http://localhost:8000/api/health/live && echo "" || echo "Not running (use --profile api)"
```

---

## Sample Use Cases

### Use Case 1: Data Exploration via Web UI

1. Start services: `docker-compose -f docker/docker-compose.yml --env-file .env up -d`
2. Open `http://localhost:8501`
3. Ask: "What is the schema of the Researchers table?"
4. Ask: "Show me all researchers earning over $100,000"
5. Export results: Click export button or type `export csv`

### Use Case 2: API Integration

1. Start with API: `docker-compose -f docker/docker-compose.yml --env-file .env --profile api up -d`
2. View docs at `http://localhost:8000/docs`
3. Use the API:
   ```python
   import requests

   response = requests.post(
       "http://localhost:8000/api/chat",
       json={"message": "How many projects are currently active?"}
   )
   print(response.json())
   ```

### Use Case 3: RAG Document Analysis

1. Start full stack: `docker-compose -f docker/docker-compose.yml --env-file .env --profile full up -d`
2. Upload documents via API:
   ```bash
   curl -X POST http://localhost:8000/api/documents/upload \
     -F "file=@research_paper.pdf"
   ```
3. Query with context:
   ```bash
   curl -X POST http://localhost:8000/api/chat \
     -H "Content-Type: application/json" \
     -d '{"message": "Summarize the uploaded research paper", "use_rag": true}'
   ```

### Use Case 4: Batch Scripting via CLI

```bash
# Run queries non-interactively
echo "SELECT COUNT(*) FROM Researchers" | docker-compose -f docker/docker-compose.yml --env-file .env --profile cli run --rm agent-cli

# Or mount a script
docker run --rm -v $(pwd)/queries.txt:/queries.txt \
  --network local-agent-network \
  local-agent-ai-stack-agent-cli python -m src.cli.chat < /queries.txt
```

---

## Troubleshooting

### Container Won't Start

```bash
# Check logs
docker logs local-agent-mssql
docker logs local-agent-redis
docker logs local-agent-streamlit-ui
docker logs local-agent-api

# Check health status
docker inspect local-agent-mssql --format='{{.State.Health.Status}}'
```

### SQL Server Connection Issues

| Symptom | Cause | Solution |
|---------|-------|----------|
| "Login failed for user 'sa'" | Wrong password | Check `MSSQL_SA_PASSWORD` in `.env` |
| "Cannot connect" | Container not healthy | Wait 30s or check logs |
| "Certificate error" | Missing trust flag | Use `Trust Server Certificate=true` |

### Redis Connection Issues

```bash
# Check if Redis is accepting connections
docker exec local-agent-redis redis-cli PING

# Check module list (should include search)
docker exec local-agent-redis redis-cli MODULE LIST
```

### Port Conflicts

```bash
# Check what's using a port
netstat -an | findstr :8001
netstat -an | findstr :1433

# Change ports in .env
REDIS_INSIGHT_PORT=8008
API_PORT=8080
STREAMLIT_PORT=8502
```

### Rebuild from Scratch

```bash
# Stop everything and remove volumes
docker-compose -f docker/docker-compose.yml down -v

# Remove volumes
docker volume rm local-llm-mssql-data local-llm-redis-data

# Recreate volumes
docker volume create local-llm-mssql-data
docker volume create local-llm-redis-data

# Start fresh
docker-compose -f docker/docker-compose.yml --env-file .env up -d
docker-compose -f docker/docker-compose.yml --env-file .env --profile init up mssql-tools
```

---

## Environment Variables Reference

| Variable | Default | Description |
|----------|---------|-------------|
| `MSSQL_SA_PASSWORD` | `LocalLLM@2024!` | SQL Server SA password |
| `MSSQL_VOLUME_NAME` | `local-llm-mssql-data` | SQL Server volume name |
| `REDIS_VOLUME_NAME` | `local-llm-redis-data` | Redis volume name |
| `REDIS_PORT` | `6379` | Redis server port |
| `REDIS_INSIGHT_PORT` | `8001` | RedisInsight GUI port |
| `API_PORT` | `8000` | FastAPI backend port |
| `STREAMLIT_PORT` | `8501` | Streamlit UI port |
| `OLLAMA_HOST` | `http://host.docker.internal:11434` | Ollama server URL |
| `OLLAMA_MODEL` | `qwen2.5:7b-instruct` | LLM model to use |
| `LLM_PROVIDER` | `ollama` | LLM provider (ollama/foundry_local) |

---

*Last Updated: December 2025* (Phase 2.1)
