# 🐳 Docker Setup for Local LLM Research Agent

> **SQL Server 2022 + Redis Stack + Research Agent Services**

All services are organized under the `local-agent-ai-stack` Docker Compose project.

---

## 📑 Table of Contents

- [Quick Start](#-quick-start)
- [Services](#-services)
- [Connection Details](#-connection-details)
- [Sample Database](#-sample-database)
- [Files](#-files)
- [Common Commands](#-common-commands)
- [Customization](#-customization)
- [Troubleshooting](#-troubleshooting)
- [Sample Queries](#-sample-queries)

---

## 📦 Services

| Service | Container Name | Port | Profile | Description |
|---------|---------------|------|---------|-------------|
| **mssql** | `local-agent-mssql` | 1433 | default | SQL Server 2022 database |
| **redis-stack** | `local-agent-redis` | 6379, 8001* | default | Redis with vector search + RedisInsight |
| **mssql-tools** | `local-agent-mssql-tools` | - | `init` | Database initialization scripts |
| **agent-ui** | `local-agent-streamlit-ui` | 8501 | default | Streamlit web interface |
| **agent-cli** | `local-agent-cli` | - | `cli` | Interactive CLI chat |
| **api** | `local-agent-api` | 8000 | `api` | FastAPI backend |
| **superset** | `local-agent-superset` | 8088 | `superset` | Apache Superset BI platform |

> *RedisInsight port is configurable via `REDIS_INSIGHT_PORT` environment variable

---

## ⚠️ Critical: Environment File Requirement

When running docker-compose from the **project root**, you **MUST** include `--env-file .env`:

```bash
# ✅ Correct - includes env file
docker-compose -f docker/docker-compose.yml --env-file .env up -d

# ❌ Wrong - environment variables won't be loaded
docker-compose -f docker/docker-compose.yml up -d
```

**Why?** Docker Compose looks for `.env` in the same directory as the compose file (`docker/`), not the working directory. Since `.env` is in the project root, you must explicitly specify its path.

**Symptoms if you forget `--env-file .env`:**
- Redis fails with "port 8001 already allocated" (uses default instead of your configured port)
- Volume names may not match your configuration
- Password variables may not be loaded correctly

---

## 🚀 Quick Start

### Windows

```bash
setup-database.bat
```

### Linux/Mac

```bash
chmod +x setup-database.sh
./setup-database.sh
```

### Manual Setup (from project root)

> ⚠️ **Important**: Always include `--env-file .env` when running docker-compose from the project root to ensure environment variables (like port configurations) are properly loaded.

```bash
# Start SQL Server and Redis Stack
docker-compose -f docker/docker-compose.yml --env-file .env up -d

# Wait for healthy status (about 30 seconds)
docker-compose -f docker/docker-compose.yml ps

# Initialize database with sample data
docker-compose -f docker/docker-compose.yml --env-file .env --profile init up mssql-tools
```

### Full Stack Setup

```bash
# Start everything including FastAPI backend
docker-compose -f docker/docker-compose.yml --env-file .env --profile api up -d

# Or with Streamlit UI
docker-compose -f docker/docker-compose.yml --env-file .env --profile api up -d agent-ui
```

---

## 🔌 Connection Details

| Setting | Value |
|---------|-------|
| Server | `localhost,1433` |
| Database | `ResearchAnalytics` |
| Username | `sa` |
| Password | `LocalLLM@2024!` |

> ⚠️ **Warning:** Change the default password for production use!

---

## 🗄️ Sample Database

### Database Schema

The `ResearchAnalytics` database contains sample data for a fictional research organization.

### Tables

| Table | Records | Description |
|-------|---------|-------------|
| `Departments` | 8 | Research departments (AI, ML, NLP, etc.) |
| `Researchers` | 23 | Team members with titles, salaries |
| `Projects` | 15 | Research projects with budgets, status |
| `ProjectAssignments` | - | Researcher-project assignments |
| `Publications` | 10 | Academic papers with citations |
| `PublicationAuthors` | - | Publication-researcher linking |
| `Datasets` | 10 | Research datasets with metadata |
| `Experiments` | 11 | ML experiments with results |
| `Funding` | 12 | Grants from funding sources |
| `Equipment` | 10 | Lab equipment inventory |

### Views

| View | Description |
|------|-------------|
| `vw_ActiveProjects` | Active projects with lead researcher info |
| `vw_ResearcherPublications` | Publication counts and citations per researcher |
| `vw_ProjectFunding` | Funding summary per project |

---

## 📁 Files

```
docker/
├── docker-compose.yml      # Main compose file
├── setup-database.bat      # Windows setup script
├── setup-database.sh       # Linux/Mac setup script
├── README.md               # This file
└── init/
    ├── 01-create-database.sql   # Creates ResearchAnalytics DB
    ├── 02-create-schema.sql     # Creates all tables and views
    └── 03-seed-data.sql         # Populates sample data
```

---

## 💻 Common Commands

All commands assume you're running from the **project root** (not the docker folder).

### Container Management

| Command | Description |
|---------|-------------|
| `docker-compose -f docker/docker-compose.yml --env-file .env up -d` | Start SQL Server + Redis |
| `docker-compose -f docker/docker-compose.yml --env-file .env --profile api up -d` | Start with FastAPI |
| `docker-compose -f docker/docker-compose.yml logs -f mssql` | View SQL Server logs |
| `docker-compose -f docker/docker-compose.yml logs -f redis-stack` | View Redis logs |
| `docker-compose -f docker/docker-compose.yml down` | Stop (preserve data) |
| `docker-compose -f docker/docker-compose.yml down -v` | Stop and delete data |
| `docker-compose -f docker/docker-compose.yml ps` | Check status |

### Database Operations

```bash
# Reinitialize database (re-run all init scripts)
docker-compose -f docker/docker-compose.yml --env-file .env --profile init up mssql-tools

# Connect via Docker exec (note: container name is local-agent-mssql)
docker exec -it local-agent-mssql /opt/mssql-tools18/bin/sqlcmd \
  -S localhost -U sa -P "LocalLLM@2024!" -No -d ResearchAnalytics

# Quick test query
docker exec -it local-agent-mssql /opt/mssql-tools18/bin/sqlcmd \
  -S localhost -U sa -P "LocalLLM@2024!" -No \
  -Q "SELECT COUNT(*) FROM ResearchAnalytics.dbo.Researchers"

# Test Redis connection
docker exec -it local-agent-redis redis-cli PING
```

### Running Agent Services

```bash
# Start Streamlit UI in Docker
docker-compose -f docker/docker-compose.yml --env-file .env up -d agent-ui
# Access at http://localhost:8501

# Start FastAPI backend
docker-compose -f docker/docker-compose.yml --env-file .env --profile api up -d
# Access at http://localhost:8000/docs

# Run interactive CLI
docker-compose -f docker/docker-compose.yml --env-file .env --profile cli run agent-cli
```

---

## ⚙️ Customization

### Environment Variables

Configure these in your `.env` file at the project root:

| Variable | Default | Description |
|----------|---------|-------------|
| `MSSQL_SA_PASSWORD` | `LocalLLM@2024!` | SQL Server SA password |
| `MSSQL_VOLUME_NAME` | `local-llm-mssql-data` | SQL Server data volume name |
| `REDIS_VOLUME_NAME` | `local-llm-redis-data` | Redis data volume name |
| `REDIS_PORT` | `6379` | Redis server port |
| `REDIS_INSIGHT_PORT` | `8001` | RedisInsight GUI port |
| `API_PORT` | `8000` | FastAPI server port |
| `STREAMLIT_PORT` | `8501` | Streamlit UI port |

### Custom SA Password

Set `MSSQL_SA_PASSWORD` in `.env` before starting:

```bash
# In .env file at project root
MSSQL_SA_PASSWORD=YourSecurePassword123!
```

> ⚠️ **Note**: The password is stored in the SQL Server master database on first run. Changing it in `.env` after initialization won't update the database password.

### Port Conflicts

If default ports are in use, configure alternatives in `.env`:

```bash
# Redis server on alternate port
REDIS_PORT=6380

# RedisInsight GUI on alternate port (common conflict with other services)
REDIS_INSIGHT_PORT=8008

# API on alternate port
API_PORT=8080

# Streamlit on alternate port
STREAMLIT_PORT=8502
```

### Data Persistence

Volumes are configured as `external: true` for data persistence. Create them before first run:

```bash
# Create volumes (only needed once)
docker volume create local-llm-mssql-data
docker volume create local-llm-redis-data

# Or with custom names
docker volume create my-custom-mssql-data
# Then set MSSQL_VOLUME_NAME=my-custom-mssql-data in .env
```

---

## 🔧 Troubleshooting

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| Container won't start | Not enough memory | Increase Docker Desktop memory to 2GB+ |
| Database not initialized | Scripts didn't run | Run `docker-compose -f docker/docker-compose.yml --profile init up mssql-tools` |
| Permission denied (Linux) | Script not executable | `chmod +x setup-database.sh` |
| Port 1433 in use | Another SQL Server | Stop other instance or change port |
| Port 8001 in use | RedisInsight conflict | Set `REDIS_INSIGHT_PORT=8008` in `.env` |
| Volume not found | External volume missing | Run `docker volume create local-llm-mssql-data` |
| SA password mismatch | Password changed after init | Password is stored in DB on first run |

### Debugging Commands

```bash
# Check container logs (from project root)
docker-compose -f docker/docker-compose.yml logs mssql
docker-compose -f docker/docker-compose.yml logs redis-stack

# Check container health
docker inspect local-agent-mssql --format='{{.State.Health.Status}}'
docker inspect local-agent-redis --format='{{.State.Health.Status}}'

# Check all containers status
docker-compose -f docker/docker-compose.yml ps

# Check what's using a port
netstat -an | grep 1433
netstat -an | grep 6379
netstat -an | grep 8001

# Interactive container shell
docker exec -it local-agent-mssql /bin/bash
docker exec -it local-agent-redis /bin/bash

# Test Redis
docker exec -it local-agent-redis redis-cli PING
```

### Reset Everything

```bash
# Stop and remove all containers (from project root)
docker-compose -f docker/docker-compose.yml down -v

# Remove images (optional, for full reset)
docker rmi mcr.microsoft.com/mssql/server:2022-latest
docker rmi redis/redis-stack:latest

# Recreate volumes
docker volume create local-llm-mssql-data
docker volume create local-llm-redis-data

# Start fresh
docker-compose -f docker/docker-compose.yml --env-file .env up -d
docker-compose -f docker/docker-compose.yml --env-file .env --profile init up mssql-tools
```

---

## 📊 Sample Queries

Once connected, try these queries to test the database:

### Schema Discovery

```sql
-- List all tables
SELECT TABLE_NAME
FROM INFORMATION_SCHEMA.TABLES
WHERE TABLE_TYPE = 'BASE TABLE';

-- Describe a table
SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_NAME = 'Researchers';
```

### Basic Queries

```sql
-- Count researchers by department
SELECT d.DepartmentName, COUNT(*) as ResearcherCount
FROM Researchers r
JOIN Departments d ON r.DepartmentId = d.DepartmentId
GROUP BY d.DepartmentName
ORDER BY ResearcherCount DESC;

-- Top 5 highest paid researchers
SELECT TOP 5 FirstName, LastName, Title, Salary
FROM Researchers
ORDER BY Salary DESC;
```

### Using Views

```sql
-- Active projects with lead researcher
SELECT * FROM vw_ActiveProjects;

-- Researcher publication summary
SELECT * FROM vw_ResearcherPublications
ORDER BY TotalCitations DESC;

-- Project funding overview
SELECT * FROM vw_ProjectFunding;
```

### Analytical Queries

```sql
-- Department budget utilization
SELECT
    d.DepartmentName,
    d.Budget,
    SUM(p.ActualSpend) as TotalSpend,
    d.Budget - SUM(p.ActualSpend) as Remaining
FROM Departments d
JOIN Projects p ON d.DepartmentId = p.DepartmentId
GROUP BY d.DepartmentName, d.Budget;

-- Most cited publications
SELECT TOP 5
    Title,
    CitationCount,
    Journal,
    PublicationDate
FROM Publications
ORDER BY CitationCount DESC;
```

---

## 📊 Apache Superset

Apache Superset is an enterprise BI platform included as an optional service.

### Starting Superset

```bash
# Start Superset with dependencies
docker-compose -f docker/docker-compose.yml --env-file .env --profile superset up -d

# Wait for initialization (~60 seconds)
docker logs -f local-agent-superset

# Run setup script to configure SQL Server connection
python scripts/setup_superset.py
```

### Access

| Setting | Value |
|---------|-------|
| URL | `http://localhost:8088` |
| Username | `admin` |
| Password | See `SUPERSET_ADMIN_PASSWORD` in `.env` |

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `SUPERSET_SECRET_KEY` | (generated) | Session encryption key |
| `SUPERSET_ADMIN_PASSWORD` | `LocalLLM@2024!` | Admin user password |
| `SUPERSET_PORT` | `8088` | Web UI port |
| `SUPERSET_VOLUME_NAME` | `local-llm-superset-data` | Data volume name |

### Files

```
docker/
├── docker-compose.yml           # Service definition
├── Dockerfile.superset          # Custom image with SQL Server driver
└── superset/
    └── superset_config.py       # Superset configuration
```

For detailed usage, see [docs/superset-guide.md](../docs/superset-guide.md).

---

*Last Updated: December 2025* (Phase 3 - Added Apache Superset BI platform)
