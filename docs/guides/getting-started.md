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
- [Next Steps](#-next-steps)
- [Troubleshooting](#-troubleshooting)

---

## 🎯 Overview

The Local LLM Research Agent enables natural language interaction with SQL Server databases using 100% local processing. No data leaves your machine.

### What You'll Set Up

| Component | Description |
|-----------|-------------|
| 🦙 **Ollama** | Local LLM inference engine |
| 🗃️ **SQL Server** | Docker container with sample data |
| 🔌 **MSSQL MCP** | Model Context Protocol server |
| 🤖 **Agent** | Pydantic AI orchestration |

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

### Step 3: Install Ollama

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

### Step 4: Verify Ollama

```bash
# Check Ollama is running
curl http://localhost:11434/api/tags

# Or on Windows
Invoke-WebRequest http://localhost:11434/api/tags
```

---

## 🗄️ Database Setup

The project includes a Docker-based SQL Server with sample research analytics data.

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

### Manual Setup

```bash
cd docker

# Start SQL Server container
docker compose up -d mssql

# Wait for healthy status (about 30 seconds)
docker compose ps

# Initialize database with sample data
docker compose --profile init up mssql-tools
```

### Verify Database

```bash
# Check container is running
docker ps | grep local-llm-mssql

# Test connection (using Docker)
docker exec -it local-llm-mssql /opt/mssql-tools18/bin/sqlcmd \
  -S localhost -U sa -P "LocalLLM@2024!" -No \
  -Q "SELECT COUNT(*) AS Tables FROM ResearchAnalytics.INFORMATION_SCHEMA.TABLES"
```

### Database Connection Details

| Setting | Value |
|---------|-------|
| Server | `localhost,1433` |
| Database | `ResearchAnalytics` |
| Username | `sa` |
| Password | `LocalLLM@2024!` |

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
# Ollama Configuration
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=qwen2.5:7b-instruct

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
```

> ⚠️ **Important:** Update `MCP_MSSQL_PATH` to your actual path!

---

## ▶️ Running the Agent

### Option 1: CLI Interface

```bash
# Start CLI chat
uv run python -m src.cli.chat

# With read-only mode (safer)
uv run python -m src.cli.chat --readonly

# With debug output
uv run python -m src.cli.chat --debug
```

### Option 2: Web Interface

```bash
# Start Streamlit
uv run streamlit run src/ui/streamlit_app.py

# Access at: http://localhost:8501
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

Expected: Agent queries the database and returns count (23)

### Analytical Query

```
Show me the top 5 highest paid researchers
```

Expected: Agent returns names, titles, and salaries

### Complex Query

```
Which department has the most active projects?
```

Expected: Agent joins tables and aggregates data

---

## 🔜 Next Steps

Now that you're set up:

1. **Explore the data** - Try queries from [Testing the Agent](../../README.md#testing-the-agent)
2. **Read the MCP tools reference** - [MSSQL MCP Tools](../reference/mssql_mcp_tools.md)
3. **Configure for production** - [Configuration Guide](configuration.md)
4. **Troubleshoot issues** - [Troubleshooting Guide](troubleshooting.md)

---

## 🔧 Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| Ollama not connecting | Ensure Ollama is running: `curl http://localhost:11434` |
| Database connection refused | Check Docker container: `docker compose ps` |
| MCP server not found | Verify `MCP_MSSQL_PATH` in `.env` |
| Model not found | Pull model: `ollama pull qwen2.5:7b-instruct` |

### Need More Help?

See the full [Troubleshooting Guide](troubleshooting.md).

---

*Last Updated: December 2024*
