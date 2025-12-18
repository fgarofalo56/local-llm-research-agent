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
| **mssql** | `local-agent-mssql` | 1433 | SQL Server 2022 (sample database) |
| **mssql-backend** | `local-agent-mssql-backend` | 1434 | SQL Server 2025 (backend + native vectors) |
| **redis-stack** | `local-agent-redis` | 6379, 8001* | Redis (caching + vector fallback) |
| **agent-ui** | `local-agent-streamlit-ui` | 8501 | Streamlit web interface |
| **api** | `local-agent-api` | 8000 | FastAPI backend with RAG |
| **agent-cli** | `local-agent-cli` | - | Interactive CLI chat |
| **mssql-tools** | `local-agent-mssql-tools` | - | Sample database initialization |
| **mssql-backend-tools** | `local-agent-mssql-backend-tools` | - | Backend database initialization |
| **superset** | `local-agent-superset` | 8088 | Apache Superset BI platform |

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
   docker volume create local-llm-backend-data
   docker volume create local-llm-redis-data
   ```

---

## Quick Start

### First Time Setup

```bash
# 1. Create volumes (one time only)
docker volume create local-llm-mssql-data
docker volume create local-llm-backend-data
docker volume create local-llm-redis-data

# 2. Start core services
docker-compose -f docker/docker-compose.yml --env-file .env up -d

# 3. Initialize databases with sample and backend data
docker-compose -f docker/docker-compose.yml --env-file .env --profile init up mssql-tools
docker-compose -f docker/docker-compose.yml --env-file .env --profile init up mssql-backend-tools

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
| **Superset** | `--profile superset up -d` | + superset |
| **Full** | `--profile full up -d` | mssql, redis-stack, agent-ui, api, superset |
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

### 1. SQL Server 2022 - Sample Database (mssql)

**Purpose:** Sample database for research analytics demo data.

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

### 1b. SQL Server 2025 - Backend Database (mssql-backend)

**Purpose:** Backend database for application state and native vector storage using SQL Server 2025's VECTOR type.

**Connection Details:**
| Setting | Value |
|---------|-------|
| Server | `localhost,1434` |
| Database | `LLM_BackEnd` |
| Username | `sa` |
| Password | See `MSSQL_SA_PASSWORD` in `.env` |
| Trust Certificate | Yes |

**Start:**
```bash
docker-compose -f docker/docker-compose.yml --env-file .env up -d mssql-backend
```

**Test Connection:**
```bash
# From host (requires sqlcmd installed)
sqlcmd -S localhost,1434 -U sa -P "LocalLLM@2024!" -C -Q "SELECT @@VERSION"

# From inside container
docker exec local-agent-mssql-backend /opt/mssql-tools18/bin/sqlcmd \
  -S localhost -U sa -P "$MSSQL_SA_PASSWORD" -C -Q "SELECT name FROM sys.databases"
```

**Database Schemas:**
| Schema | Purpose |
|--------|---------|
| `app` | Application state tables (conversations, dashboards, etc.) |
| `vectors` | Vector storage tables using native VECTOR(768) type |

**Sample Queries:**
```sql
-- List all tables in LLM_BackEnd
SELECT TABLE_SCHEMA, TABLE_NAME FROM LLM_BackEnd.INFORMATION_SCHEMA.TABLES;

-- Check vector index
SELECT * FROM vectors.document_chunks_index;

-- Search documents using native vector distance
EXEC vectors.SearchDocuments @query_vector = @embedding, @top_n = 5;
```

**Key Features:**
- **Native VECTOR(768) type** - No external vector database needed
- **VECTOR_DISTANCE function** - Cosine similarity built into SQL Server
- **Stored procedures** - Optimized vector search operations

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

### 7. Apache Superset (superset)

**Purpose:** Enterprise BI platform with SQL Lab, dashboards, and scheduled reports.

**Access:**
| Setting | Value |
|---------|-------|
| URL | `http://localhost:8088` |
| Username | `admin` |
| Password | See `SUPERSET_ADMIN_PASSWORD` in `.env` |

**Start:**
```bash
# Start Superset with dependencies
docker-compose -f docker/docker-compose.yml --env-file .env --profile superset up -d

# Wait for initialization (~60 seconds)
docker logs -f local-agent-superset

# Configure SQL Server connection
python scripts/setup_superset.py
```

**Test:**
```bash
# Health check
curl http://localhost:8088/health

# View logs
docker logs local-agent-superset -f
```

**Features:**
- **SQL Lab**: Full SQL IDE for data exploration
- **40+ Charts**: Extensive visualization library
- **Dashboards**: Drag-and-drop dashboard builder
- **Scheduled Reports**: Email reports on schedule
- **Embedding**: Embed dashboards in React app

For detailed usage, see [superset-guide.md](../superset-guide.md).

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

echo -e "\n=== Superset Test (if running) ==="
curl -s http://localhost:8088/health && echo "OK" || echo "Not running (use --profile superset)"
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

### Database Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `MSSQL_SA_PASSWORD` | `LocalLLM@2024!` | SQL Server SA password |
| `MSSQL_VOLUME_NAME` | `local-llm-mssql-data` | Sample database volume name |
| `BACKEND_VOLUME_NAME` | `local-llm-backend-data` | Backend database volume name |
| `SQL_SERVER_HOST` | `localhost` | Sample database host |
| `SQL_SERVER_PORT` | `1433` | Sample database port |
| `SQL_DATABASE_NAME` | `ResearchAnalytics` | Sample database name |

### Backend Database (SQL Server 2025)

| Variable | Default | Description |
|----------|---------|-------------|
| `BACKEND_DB_HOST` | `localhost` | Backend database host |
| `BACKEND_DB_PORT` | `1434` | Backend database port |
| `BACKEND_DB_NAME` | `LLM_BackEnd` | Backend database name |
| `BACKEND_DB_TRUST_CERT` | `true` | Trust self-signed certificates |

### Vector Store Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `VECTOR_STORE_TYPE` | `mssql` | Vector store: `mssql` (primary) or `redis` (fallback) |
| `VECTOR_DIMENSIONS` | `768` | Embedding dimensions (768 for nomic-embed-text) |

### Redis Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `REDIS_VOLUME_NAME` | `local-llm-redis-data` | Redis volume name |
| `REDIS_PORT` | `6379` | Redis server port |
| `REDIS_INSIGHT_PORT` | `8001` | RedisInsight GUI port |
| `REDIS_URL` | `redis://localhost:6379` | Redis connection URL |

### Application Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `API_PORT` | `8000` | FastAPI backend port |
| `STREAMLIT_PORT` | `8501` | Streamlit UI port |
| `OLLAMA_HOST` | `http://host.docker.internal:11434` | Ollama server URL |
| `OLLAMA_MODEL` | `qwen2.5:7b-instruct` | LLM model to use |
| `LLM_PROVIDER` | `ollama` | LLM provider (ollama/foundry_local) |

### Superset Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `SUPERSET_SECRET_KEY` | (generated) | Superset session encryption key |
| `SUPERSET_ADMIN_PASSWORD` | `LocalLLM@2024!` | Superset admin password |
| `SUPERSET_PORT` | `8088` | Superset web UI port |
| `SUPERSET_VOLUME_NAME` | `local-llm-superset-data` | Superset data volume name |

---

*Last Updated: December 2025*
