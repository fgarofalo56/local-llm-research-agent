# 🚀 Getting Started

> **Complete setup guide to run the Local LLM Research Agent in under 15 minutes**

---

## 📑 Table of Contents

- [Overview](#-overview)
- [Prerequisites](#-prerequisites)
- [Installation](#-installation)
- [Database Setup](#-database-setup)
- [MCP Server Setup](#-mcp-server-setup)
- [Configuration](#-configuration)
- [Running the Agent](#-running-the-agent)
- [Your First Query](#-your-first-query)
- [Using Features](#-using-features)
- [Next Steps](#-next-steps)
- [Troubleshooting](#-troubleshooting)

---

## 🎯 Overview

The Local LLM Research Agent enables natural language interaction with SQL Server databases using 100% local processing. No data leaves your machine.

### What You'll Set Up

| Component | Description |
|-----------|-------------|
| 🦙 **LLM Provider** | Ollama or Microsoft Foundry Local |
| 🗃️ **SQL Server** | Docker container with sample data |
| 🔌 **MSSQL MCP** | Model Context Protocol server |
| 🤖 **Agent** | Pydantic AI orchestration |

### Key Features

| Feature | Status | Description |
|---------|--------|-------------|
| Natural Language Queries | ✅ | Ask questions in plain English |
| Streaming Responses | ✅ | See answers as they're generated |
| Response Caching | ✅ | Faster repeated queries |
| Export (JSON/CSV/MD) | ✅ | Save conversations and data |
| Session History | ✅ | Recall previous conversations |
| Dual Providers | ✅ | Ollama or Foundry Local |

---

## 📦 Prerequisites

Before starting, ensure you have:

- [ ] **Python 3.11+** - [Download](https://python.org/downloads/)
- [ ] **Docker Desktop** - [Download](https://docker.com/products/docker-desktop/)
- [ ] **Node.js 18+** - [Download](https://nodejs.org/)
- [ ] **Git** - [Download](https://git-scm.com/)
- [ ] **8GB+ RAM** recommended for Ollama models

### Verify Prerequisites

```bash
# Check Python version
python --version  # Should be 3.11+

# Check Docker
docker --version

# Check Node.js
node --version  # Should be 18+

# Check Git
git --version
```

---

## 📥 Installation

### Step 1: Clone the Repository

```bash
git clone https://github.com/fgarofalo56/local-llm-research-agent.git
cd local-llm-research-agent
```

### Step 2: Install Python Dependencies

```bash
# Using uv (recommended)
uv sync

# Or using pip
pip install -r requirements.txt
```

### Step 3: Install an LLM Provider

Choose **one** of the following:

#### Option A: Ollama (Recommended)

1. Download from [ollama.com](https://ollama.com/)
2. Install and start the application
3. Pull a recommended model:

```bash
# Recommended for tool calling
ollama pull qwen2.5:7b-instruct

# Or alternative models
ollama pull llama3.1:8b
ollama pull mistral:7b-instruct
```

#### Option B: Microsoft Foundry Local

```bash
# Install the SDK
pip install foundry-local-sdk

# The agent will auto-download models when needed
```

### Step 4: Verify Provider

```bash
# For Ollama
curl http://localhost:11434/api/tags

# For Foundry Local - check when starting the agent
```

---

## 🗄️ Database Setup

The project includes a Docker-based SQL Server and Redis Stack with sample research analytics data. All services run under the `local-agent-ai-stack` project.

### Docker Services

| Service | Container | Port | Purpose |
|---------|-----------|------|---------|
| **mssql** | `local-agent-mssql` | 1433 | SQL Server 2022 |
| **redis-stack** | `local-agent-redis` | 6379, 8001 | Redis + Vector Search |
| **agent-ui** | `local-agent-streamlit-ui` | 8501 | Web Interface |
| **api** | `local-agent-api` | 8000 | FastAPI Backend |
| **superset** | `local-agent-superset` | 8088 | Apache Superset BI (optional) |

### Quick Setup

#### Windows
```bash
cd docker
setup-database.bat
```

#### Linux/Mac
```bash
cd docker
chmod +x setup-database.sh
./setup-database.sh
```

### Manual Setup (from project root)

> ⚠️ **Critical**: Always include `--env-file .env` when running docker-compose from the project root. Without it, environment variables like port configurations won't be loaded, causing containers to fail.

```bash
# Create external volumes (first time only)
docker volume create local-llm-mssql-data
docker volume create local-llm-redis-data

# Start SQL Server and Redis containers
docker-compose -f docker/docker-compose.yml --env-file .env up -d

# Wait for healthy status (about 30 seconds)
docker-compose -f docker/docker-compose.yml ps

# Initialize database with sample data
docker-compose -f docker/docker-compose.yml --env-file .env --profile init up mssql-tools
```

### Verify Database

```bash
# Check container is running
docker ps | grep local-agent-mssql

# Test connection (using Docker)
docker exec -it local-agent-mssql /opt/mssql-tools18/bin/sqlcmd \
  -S localhost -U sa -P "LocalLLM@2024!" -No \
  -Q "SELECT COUNT(*) AS Tables FROM ResearchAnalytics.INFORMATION_SCHEMA.TABLES"

# Test Redis connection
docker exec -it local-agent-redis redis-cli PING
```

### Database Connection Details

| Setting | Value |
|---------|-------|
| Server | `localhost,1433` |
| Database | `ResearchAnalytics` |
| Username | `sa` |
| Password | `LocalLLM@2024!` |
| Redis | `redis://localhost:6379` |

---

## 🔌 MCP Server Setup

The MSSQL MCP Server provides SQL tools to the agent.

### Step 1: Clone MCP Server

```bash
# Clone to a separate directory
git clone https://github.com/Azure-Samples/SQL-AI-samples.git

# Navigate to Node.js implementation
cd SQL-AI-samples/MssqlMcp/Node

# Install dependencies
npm install
```

### Step 2: Note the Path

The server is at: `<your-path>/SQL-AI-samples/MssqlMcp/Node/dist/index.js`

**Example paths:**
- Windows: `C:\Projects\SQL-AI-samples\MssqlMcp\Node\dist\index.js`
- Linux/Mac: `/home/user/SQL-AI-samples/MssqlMcp/Node/dist/index.js`

---

## ⚙️ Configuration

### Step 1: Create Environment File

```bash
# Return to project directory
cd local-llm-research-agent

# Copy template
cp .env.example .env
```

### Step 2: Edit Configuration

Open `.env` and configure:

```bash
# LLM Provider Selection
LLM_PROVIDER=ollama  # or "foundry_local"

# Ollama Configuration
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=qwen2.5:7b-instruct

# Foundry Local Configuration (if using)
FOUNDRY_ENDPOINT=http://127.0.0.1:53760
FOUNDRY_MODEL=phi-4

# SQL Server (Docker defaults)
SQL_SERVER_HOST=localhost
SQL_SERVER_PORT=1433
SQL_DATABASE_NAME=ResearchAnalytics
SQL_TRUST_SERVER_CERTIFICATE=true

# SQL Authentication
SQL_USERNAME=sa
SQL_PASSWORD=LocalLLM@2024!

# MCP Server Path (UPDATE THIS!)
MCP_MSSQL_PATH=/path/to/SQL-AI-samples/MssqlMcp/Node/dist/index.js

# Optional: Read-only mode
MCP_MSSQL_READONLY=false

# Caching (optional)
CACHE_ENABLED=true
CACHE_MAX_SIZE=100
CACHE_TTL_SECONDS=3600
```

> ⚠️ **Important:** Update `MCP_MSSQL_PATH` to your actual path!

---

## ▶️ Running the Agent

### Option 1: CLI Interface

```bash
# Start CLI chat
uv run python -m src.cli.chat

# With streaming (show tokens as generated)
uv run python -m src.cli.chat --stream

# With read-only mode (safer)
uv run python -m src.cli.chat --readonly

# With Foundry Local provider
uv run python -m src.cli.chat --provider foundry_local

# Disable response caching
uv run python -m src.cli.chat --no-cache

# With debug output
uv run python -m src.cli.chat --debug
```

### Option 2: Web Interface

```bash
# Start Streamlit
uv run streamlit run src/ui/streamlit_app.py

# Access at: http://localhost:8501
```

### Option 3: Single Query

```bash
# Run a single query and exit
uv run python -m src.cli.chat query "What tables are in the database?"

# With streaming
uv run python -m src.cli.chat query "Show all researchers" --stream
```

---

## 💬 Your First Query

Once the agent is running, try these queries:

### Schema Discovery

```
What tables are in the database?
```

Expected: Agent lists all tables (Departments, Researchers, Projects, etc.)

### Simple Query

```
How many researchers are there?
```

Expected: Agent queries the database and returns count

### Analytical Query

```
Show me the top 5 highest paid researchers
```

Expected: Agent returns names, titles, and salaries in a formatted table

### Complex Query

```
Which department has the most active projects?
```

Expected: Agent joins tables and aggregates data

---

## ✨ Using Features

### Interactive Commands

While in the CLI chat, use these commands:

| Command | Description |
|---------|-------------|
| `help` | Show all commands |
| `clear` | Clear conversation |
| `status` | Show connection status |
| `cache` | Show cache statistics |
| `cache-clear` | Clear the response cache |
| `export` | Export conversation (JSON/CSV/MD) |
| `export json` | Export to JSON |
| `export csv` | Export to CSV |
| `export md` | Export to Markdown |
| `history` | List saved sessions |
| `history save` | Save current session |
| `history load <id>` | Load a saved session |
| `history delete <id>` | Delete a session |
| `quit` | Exit the chat |

### Streaming Mode

Enable streaming to see responses as they're generated:

```bash
# CLI with streaming
uv run python -m src.cli.chat --stream
```

In Streamlit, toggle "Streaming responses" in the sidebar.

### Response Caching

The agent caches responses to identical queries:

```bash
# View cache stats
cache

# Clear cache
cache-clear

# Disable caching
uv run python -m src.cli.chat --no-cache
```

### Exporting Data

Export your conversation or query results:

```bash
# In chat, type:
export json   # Saves to chat_YYYYMMDD_HHMMSS.json
export csv    # Saves to chat_YYYYMMDD_HHMMSS.csv
export md     # Saves to chat_YYYYMMDD_HHMMSS.md
```

In Streamlit, use the Export buttons in the sidebar.

### Session History

Save and recall previous conversations:

```bash
# List saved sessions
history

# Save current session
history save

# Load a previous session
history load abc12345

# Delete a session
history delete abc12345
```

---

## 🔜 Next Steps

Now that you're set up:

1. **Explore the data** - Try different queries on the ResearchAnalytics database
2. **Learn Docker services** - [Docker Services Guide](docker-services.md) - Complete guide to all containers
3. **Read the MCP tools reference** - [MSSQL MCP Tools](../reference/mssql_mcp_tools.md)
4. **Configure for production** - [Configuration Guide](configuration.md)
5. **Try Apache Superset** - [Superset Guide](../superset-guide.md) - Enterprise BI platform
6. **Troubleshoot issues** - [Troubleshooting Guide](troubleshooting.md)

---

## 🔧 Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| Ollama not connecting | Ensure Ollama is running: `curl http://localhost:11434` |
| Foundry Local not found | Install SDK: `pip install foundry-local-sdk` |
| Database connection refused | Check Docker container: `docker-compose -f docker/docker-compose.yml ps` |
| MCP server not found | Verify `MCP_MSSQL_PATH` in `.env` |
| Model not found | Pull model: `ollama pull qwen2.5:7b-instruct` |
| Cache not working | Check `CACHE_ENABLED=true` in `.env` |
| Port 8001 in use | Set `REDIS_INSIGHT_PORT=8008` in `.env` |
| Volume not found | Create volumes: `docker volume create local-llm-mssql-data` |

### Need More Help?

See the full [Troubleshooting Guide](troubleshooting.md).

---

*Last Updated: December 2025*
