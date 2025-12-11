# 🔍 Local LLM Research Analytics Tool

> **A 100% local smart chat agent for SQL Server data analytics. Query your database using natural language with complete privacy - all inference runs locally via Ollama or Microsoft Foundry Local.**

---

## ✨ Features

### Core Features (Phase 1)

| Feature | Status | Description |
|---------|--------|-------------|
| 🔒 **Fully Local** | ✅ | No cloud APIs - all processing on your machine |
| 💬 **Natural Language SQL** | ✅ | Ask questions about your data in plain English |
| 🔌 **MCP Integration** | ✅ | Extensible tool architecture via Model Context Protocol |
| ⌨️ **CLI Interface** | ✅ | Command-line chat for development |
| 🌐 **Streamlit Web UI** | ✅ | User-friendly web interface |
| 🔐 **Privacy First** | ✅ | Your data never leaves your network |
| 🗃️ **Sample Database** | ✅ | Docker-based SQL Server with demo data |
| 🦙 **Multiple LLM Providers** | ✅ | Ollama or Microsoft Foundry Local |
| ⚡ **Streaming Responses** | ✅ | Real-time token streaming |

### Backend & RAG Features (Phase 2.1)

| Feature | Status | Description |
|---------|--------|-------------|
| 🚀 **FastAPI Backend** | ✅ | REST API with automatic OpenAPI docs |
| 🧠 **RAG Pipeline** | ✅ | Document-augmented question answering |
| 📦 **Redis Vector Store** | ✅ | Fast similarity search with Redis Stack |
| 📄 **Document Processing** | ✅ | PDF/DOCX parsing with Docling |
| 🗄️ **SQLAlchemy ORM** | ✅ | Database models with Alembic migrations |
| 🔧 **Dynamic MCP** | ✅ | Configure MCP servers at runtime |

---

## 📑 Table of Contents

- [Quick Start](#-quick-start)
- [Docker Setup](#-docker-setup-sql-server--redis-stack)
- [MSSQL MCP Server Setup](#-mssql-mcp-server-setup)
- [Configuration](#️-configuration)
- [Running the Application](#-running-the-application)
- [FastAPI Backend](#-fastapi-backend-phase-21)
- [Testing the Agent](#-testing-the-agent)
- [MCP Tools Reference](#-mcp-tools-reference)
- [Architecture](#️-architecture)
- [Development](#-development)
- [Contributing](#-contributing)
- [License](#-license)

---

## 🚀 Quick Start

### 📦 Prerequisites

| Requirement | Version | Notes |
|-------------|---------|-------|
| Python | 3.11+ | Required |
| [Ollama](https://ollama.com/) | Latest | LLM inference (or Foundry Local) |
| [Docker Desktop](https://www.docker.com/products/docker-desktop/) | Latest | For SQL Server |
| Node.js | 18+ | For MSSQL MCP Server |
| Git | Latest | Required |

### 📦 Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/local-llm-research-agent.git
cd local-llm-research-agent

# Install Python dependencies (using uv - recommended)
uv sync

# Or using pip
pip install -r requirements.txt

# Copy environment template
cp .env.example .env
```

### 🦙 Pull the Ollama Model

```bash
# Recommended model for tool calling
ollama pull qwen2.5:7b-instruct

# Alternative models
ollama pull llama3.1:8b
ollama pull mistral:7b-instruct
```

> 💡 **Tip**: `qwen2.5:7b-instruct` provides the best balance of performance and tool-calling capability.

---

## 🐳 Docker Setup (SQL Server + Redis Stack)

The project includes a complete Docker setup with SQL Server 2022, Redis Stack for vector search, and a pre-populated research analytics database. All services are nested under the `local-agent-ai-stack` project.

### ⚠️ Critical: Environment File Requirement

When running docker-compose from the **project root** (recommended), you **MUST** include `--env-file .env`:

```bash
# ✅ Correct - includes env file
docker-compose -f docker/docker-compose.yml --env-file .env up -d

# ❌ Wrong - will use default ports, may cause conflicts
docker-compose -f docker/docker-compose.yml up -d
```

**Why?** Docker Compose looks for `.env` in the same directory as the compose file. Since `docker-compose.yml` is in the `docker/` subdirectory but `.env` is in the project root, you must explicitly specify the env file path.

**What happens without it?**
- Port configurations (like `REDIS_INSIGHT_PORT`) won't be loaded
- Containers may fail to start due to port conflicts
- Volume names may not be set correctly

### 📦 Docker Services

| Service | Container Name | Port | Profile | Purpose |
|---------|---------------|------|---------|---------|
| **mssql** | `local-agent-mssql` | 1433 | default | SQL Server 2022 database |
| **redis-stack** | `local-agent-redis` | 6379, 8001* | default | Redis with vector search |
| **mssql-tools** | `local-agent-mssql-tools` | - | `init` | Database initialization |
| **agent-ui** | `local-agent-streamlit-ui` | 8501 | default | Streamlit web interface |
| **agent-cli** | `local-agent-cli` | - | `cli` | Interactive CLI chat |
| **api** | `local-agent-api` | 8000 | `api` | FastAPI backend |

> *RedisInsight GUI port is configurable via `REDIS_INSIGHT_PORT` (default: 8001)

### 🗄️ Database Overview

The sample database (`ResearchAnalytics`) contains:

| Table | Description | Records |
|-------|-------------|---------|
| Departments | Research departments (AI, ML, NLP, etc.) | 8 |
| Researchers | Team members with roles and salaries | 23 |
| Projects | Research projects with budgets and status | 15 |
| Publications | Academic papers and reports | 10 |
| Datasets | Research datasets with metadata | 10 |
| Experiments | ML experiments with results | 11 |
| Funding | Grants and funding sources | 12 |
| Equipment | Lab equipment and resources | 10 |

Plus 3 useful views: `vw_ActiveProjects`, `vw_ResearcherPublications`, `vw_ProjectFunding`

### 🚀 Starting the Services

All docker-compose commands should be run from the **project root** using `-f docker/docker-compose.yml --env-file .env`:

> ⚠️ **Important**: Always include `--env-file .env` when running docker-compose from the project root to ensure environment variables are properly loaded.

#### Option 1: Quick Setup (Windows)

```bash
cd docker
setup-database.bat
```

#### Option 2: Core Services (SQL Server + Redis)

```bash
# From project root - Start SQL Server and Redis
docker-compose -f docker/docker-compose.yml --env-file .env up -d

# Wait for services to be healthy
docker-compose -f docker/docker-compose.yml ps

# Initialize database with sample data (first time only)
docker-compose -f docker/docker-compose.yml --env-file .env --profile init up mssql-tools
```

#### Option 3: Full Stack (with FastAPI Backend)

```bash
# Start all services including the API
docker-compose -f docker/docker-compose.yml --env-file .env --profile api up -d

# This starts: SQL Server, Redis Stack, and FastAPI backend
```

#### Option 4: With Streamlit UI in Docker

```bash
# Core services + Streamlit UI
docker-compose -f docker/docker-compose.yml --env-file .env up -d agent-ui

# Core services + FastAPI + Streamlit
docker-compose -f docker/docker-compose.yml --env-file .env --profile api up -d agent-ui
```

#### Option 5: Interactive CLI in Docker

```bash
# Run interactive CLI chat
docker-compose -f docker/docker-compose.yml --env-file .env --profile cli run agent-cli
```

### 🔴 Redis Stack

Redis Stack provides vector similarity search for the RAG pipeline.

| Service | Default Port | Environment Variable | Purpose |
|---------|--------------|---------------------|---------|
| Redis | 6379 | `REDIS_PORT` | Vector store |
| RedisInsight | 8001 | `REDIS_INSIGHT_PORT` | GUI management |

Access RedisInsight at: http://localhost:8001 (or your configured port)

> 💡 **Tip**: If port 8001 is in use, set `REDIS_INSIGHT_PORT=8008` (or any free port) in your `.env` file.

### 🔌 Connection Details

| Setting | Value |
|---------|-------|
| **Server** | `localhost,1433` |
| **Database** | `ResearchAnalytics` |
| **Username** | `sa` |
| **Password** | `LocalLLM@2024!` (or your `MSSQL_SA_PASSWORD`) |

### 🔧 Testing the Connection

```bash
# Using sqlcmd (if installed)
sqlcmd -S localhost,1433 -U sa -P "LocalLLM@2024!" -d ResearchAnalytics -Q "SELECT COUNT(*) FROM Researchers"

# Using Docker exec (note the new container name)
docker exec -it local-agent-mssql /opt/mssql-tools18/bin/sqlcmd \
  -S localhost -U sa -P "LocalLLM@2024!" -No \
  -Q "SELECT COUNT(*) AS ResearcherCount FROM ResearchAnalytics.dbo.Researchers"
```

### 💾 Data Persistence

Docker volumes preserve data across container rebuilds:

| Volume | Default Name | Environment Variable | Purpose |
|--------|-------------|---------------------|---------|
| SQL Server | `local-llm-mssql-data` | `MSSQL_VOLUME_NAME` | Database files |
| Redis | `local-llm-redis-data` | `REDIS_VOLUME_NAME` | Vector store data |

> ⚠️ **Important**: Volumes are configured as `external: true`. Create them before first run:
> ```bash
> docker volume create local-llm-mssql-data
> docker volume create local-llm-redis-data
> ```

### 📋 Managing the Services

```bash
# View container status
docker-compose -f docker/docker-compose.yml ps

# View container logs
docker-compose -f docker/docker-compose.yml logs -f mssql

# Stop all services (preserves data)
docker-compose -f docker/docker-compose.yml down

# Stop and DELETE all data (fresh start)
docker-compose -f docker/docker-compose.yml down -v

# Restart with fresh data
docker-compose -f docker/docker-compose.yml down -v
docker volume create local-llm-mssql-data
docker volume create local-llm-redis-data
docker-compose -f docker/docker-compose.yml --env-file .env up -d
docker-compose -f docker/docker-compose.yml --env-file .env --profile init up mssql-tools
```

---

## 🔌 MSSQL MCP Server Setup

The MSSQL MCP Server provides tools for SQL Server interaction.

### 📦 Installation

```bash
# Clone the MSSQL MCP Server repository
git clone https://github.com/Azure-Samples/SQL-AI-samples.git

# Navigate to Node.js implementation
cd SQL-AI-samples/MssqlMcp/Node

# Install dependencies
npm install

# Note the full path to dist/index.js
# Example: C:\Projects\SQL-AI-samples\MssqlMcp\Node\dist\index.js
```

### ⚙️ Configure the Path

Update your `.env` file:

```bash
# Windows example
MCP_MSSQL_PATH=C:\Projects\SQL-AI-samples\MssqlMcp\Node\dist\index.js

# Linux/Mac example
MCP_MSSQL_PATH=/home/user/SQL-AI-samples/MssqlMcp/Node/dist/index.js
```

---

## ⚙️ Configuration

### Environment Variables (.env)

```bash
cp .env.example .env
```

Configure for the Docker database:

```bash
# =============================================================================
# LLM Provider Configuration
# =============================================================================
# Provider: "ollama" or "foundry_local"
LLM_PROVIDER=ollama

# Ollama Configuration
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=qwen2.5:7b-instruct

# Embedding model for RAG
EMBEDDING_MODEL=nomic-embed-text

# Microsoft Foundry Local Configuration (alternative)
FOUNDRY_ENDPOINT=http://127.0.0.1:55588
FOUNDRY_MODEL=phi-4
FOUNDRY_AUTO_START=true

# =============================================================================
# SQL Server Configuration
# =============================================================================
SQL_SERVER_HOST=localhost
SQL_SERVER_PORT=1433
SQL_DATABASE_NAME=ResearchAnalytics
SQL_TRUST_SERVER_CERTIFICATE=true

# SQL Server Authentication
SQL_USERNAME=sa
SQL_PASSWORD=LocalLLM@2024!

# =============================================================================
# Docker Configuration
# =============================================================================
# Docker SA password (must match SQL_PASSWORD for local dev)
MSSQL_SA_PASSWORD=LocalLLM@2024!

# Docker volume names for data persistence
MSSQL_VOLUME_NAME=local-llm-mssql-data
REDIS_VOLUME_NAME=local-llm-redis-data

# =============================================================================
# Redis Configuration
# =============================================================================
REDIS_URL=redis://localhost:6379
REDIS_PORT=6379
REDIS_INSIGHT_PORT=8001  # Change if port 8001 is in use

# =============================================================================
# RAG Configuration
# =============================================================================
CHUNK_SIZE=500
CHUNK_OVERLAP=50
RAG_TOP_K=5

# =============================================================================
# MCP Configuration
# =============================================================================
MCP_MSSQL_PATH=/path/to/SQL-AI-samples/MssqlMcp/Node/dist/index.js
MCP_MSSQL_READONLY=false
MCP_CONFIG_PATH=mcp_config.json

# =============================================================================
# API Server Configuration
# =============================================================================
API_HOST=0.0.0.0
API_PORT=8000

# =============================================================================
# Storage Configuration
# =============================================================================
UPLOAD_DIR=./data/uploads
MAX_UPLOAD_SIZE_MB=100

# =============================================================================
# Application Settings
# =============================================================================
LOG_LEVEL=INFO
DEBUG=false
STREAMLIT_PORT=8501
```

### 🦙 LLM Provider Options

| Provider | Recommended Models | Notes |
|----------|-------------------|-------|
| **Ollama** | `qwen2.5:7b-instruct`, `llama3.1:8b` | Requires Ollama running |
| **Foundry Local** | `phi-4`, `phi-3-mini` | Microsoft's local runtime |

---

## 🚀 Running the Application

### ⌨️ CLI Interface

```bash
# Check available commands
uv run python -m src.cli.chat --help

# Start the CLI chat
uv run python -m src.cli.chat chat

# With streaming responses
uv run python -m src.cli.chat chat --stream

# Use Foundry Local instead of Ollama
uv run python -m src.cli.chat chat --provider foundry_local

# With read-only mode (safer for exploration)
uv run python -m src.cli.chat --readonly

# With debug output
uv run python -m src.cli.chat chat --debug
```

### 🌐 Streamlit Web UI

```bash
# Start the web interface
uv run streamlit run src/ui/streamlit_app.py

# Access at: http://localhost:8501
```

> 💡 **Tip**: The web UI includes a provider selector in the sidebar to switch between Ollama and Foundry Local.

### 🚀 FastAPI Backend (Phase 2.1)

```bash
# Start the FastAPI server
uv run uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000

# Access points:
# - API: http://localhost:8000
# - Swagger UI: http://localhost:8000/docs
# - ReDoc: http://localhost:8000/redoc
```

---

## 📡 FastAPI Backend (Phase 2.1)

The FastAPI backend provides a REST API for all agent operations, document management, and RAG search.

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health` | GET | Health check and service status |
| `/api/health/metrics` | GET | System metrics (CPU, memory, etc.) |
| `/api/documents` | GET/POST | List/upload documents |
| `/api/documents/search` | POST | RAG vector search |
| `/api/documents/schema/index` | POST | Index database schema |
| `/api/conversations` | GET/POST | List/create conversations |
| `/api/conversations/{id}` | GET/PATCH/DELETE | Manage conversation |
| `/api/conversations/{id}/messages` | POST | Add message |
| `/api/queries/history` | GET | Query execution history |
| `/api/queries/saved` | GET/POST | Saved queries |
| `/api/dashboards` | GET/POST | List/create dashboards |
| `/api/dashboards/{id}/widgets` | POST | Add dashboard widget |
| `/api/mcp` | GET | List MCP servers |
| `/api/mcp/{name}/tools` | GET | List MCP server tools |
| `/api/settings/theme` | GET/PUT | Theme configuration |
| `/api/agent/chat` | POST | Send message to agent |

### Running the Backend

```bash
# Development mode (with hot reload)
uv run uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000

# Production mode
uv run uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --workers 4

# Via Docker
cd docker && docker compose up -d api
```

### Database Migrations

```bash
# Generate new migration after model changes
uv run alembic revision --autogenerate -m "Add new table"

# Apply all pending migrations
uv run alembic upgrade head

# Rollback one migration
uv run alembic downgrade -1
```

---

## 🧪 Testing the Agent

### Sample Queries to Try

Once the agent is running with the Docker database:

#### 📊 Schema Discovery
```
What tables are in the database?
Describe the Researchers table
Show me the schema for Projects
What views are available?
```

#### 🔍 Basic Queries
```
How many researchers are there?
List all departments and their budgets
Show me the top 5 highest paid researchers
What are the active projects?
```

#### 📈 Analytical Queries
```
Which department has the most researchers?
What's the total budget across all projects?
Show me researchers in the AI department
List projects that are over budget
```

#### 🔗 Relationship Queries
```
How many publications does each researcher have?
What funding sources support the LLM project?
Which researchers are assigned to multiple projects?
```

### ✅ Expected Behavior

| Step | Agent Action |
|------|-------------|
| 1 | Lists tables when asked about database structure |
| 2 | Describes schemas before querying data |
| 3 | Shows results in readable format |
| 4 | Explains its actions as it works |

### 🔧 Troubleshooting

| Issue | Solution |
|-------|----------|
| Connection refused | Check `docker compose ps` and logs |
| Database does not exist | Re-run `docker compose --profile init up mssql-tools` |
| Ollama connection failed | Run `curl http://localhost:11434/api/tags` |
| MCP server not found | Verify `MCP_MSSQL_PATH` in `.env` |

---

## 🔌 MCP Tools Reference

| Tool | Description | Mode | Example Use |
|------|-------------|------|-------------|
| `list_tables` | Lists all tables | ✅ Read | "What tables exist?" |
| `describe_table` | Get table schema | ✅ Read | "Describe the Researchers table" |
| `read_data` | Query data | ✅ Read | "Show top 10 researchers" |
| `insert_data` | Insert rows | ⚠️ Write | "Add a new researcher" |
| `update_data` | Modify data | ⚠️ Write | "Update project status" |
| `create_table` | Create tables | ⚠️ Write | "Create an audit log table" |
| `drop_table` | Delete tables | ⚠️ Write | "Remove temp table" |
| `create_index` | Add indexes | ⚠️ Write | "Index the email column" |

> ⚠️ **Warning**: Use `MCP_MSSQL_READONLY=true` to disable write operations.

---

## 🏗️ Architecture

```
+-----------------------------------------------------------------------------+
|                           User Interfaces                                    |
|  +------------------+  +----------------------+  +------------------------+  |
|  |  ⌨️ CLI (Typer)  |  |  🌐 Streamlit Web UI |  |  🚀 FastAPI Backend    | |
|  +--------+---------+  +-----------+----------+  +-----------+------------+  |
+-----------|-----------------------|--------------------------|---------------+
            |                       |                          |
            v                       v                          v
+-----------------------------------------------------------------------------+
|                         🤖 Pydantic AI Agent                                |
|  +-----------------------------------------------------------------------+  |
|  |  System Prompt + Tool Orchestration + Conversation + RAG Context      |  |
|  +-----------------------------------------------------------------------+  |
+------------------------------------+----------------------------------------+
                                     |
            +------------------------+------------------------+
            |                        |                        |
            v                        v                        v
+--------------------+  +----------------------------+  +---------------------+
|  🦙 LLM Provider   |  |      🔌 MCP Servers        |  |  🧠 RAG Pipeline   |
|  +--------------+  |  |  +----------------------+ |  |  +---------------+   |
|  | Ollama       |  |  |  | MSSQL MCP Server     | |  |  | 📄 Docling    |   |
|  | Foundry Local|  |  |  | (SQL Server Access)  | |  |  | 🔢 Embeddings |   |
|  +--------------+  |  |  +----------------------+ |  |  | 🔍 Search     |   |
+--------------------+  +----------------------------+  |  +---------------+  |
                                     |                  +----------+----------+
                                     v                             |
                        +----------------------------+             v
                        |   🗃️ SQL Server           |  +---------------------+
                        |   (Docker Container)       |  |  🔴 Redis Stack     |
                        |   ResearchAnalytics DB     |  |   Vector Store      |
                        +----------------------------+  +---------------------+
```

### 🔧 Tech Stack

| Component | Technology | Icon |
|-----------|------------|------|
| LLM Runtime | Ollama / Foundry Local | 🦙 |
| Agent Framework | Pydantic AI | 🤖 |
| MCP Server | MSSQL MCP (Node.js) | 🔌 |
| Web UI | Streamlit | 🌐 |
| CLI | Typer + Rich | ⌨️ |
| Database | SQL Server 2022 (Docker) | 🗃️ |
| Validation | Pydantic v2 | ✅ |
| **Backend API** | FastAPI + Uvicorn | 🚀 |
| **ORM** | SQLAlchemy 2.0 + Alembic | 🗄️ |
| **Vector Store** | Redis Stack | 🔴 |
| **Embeddings** | Ollama (nomic-embed-text) | 🧠 |
| **Doc Processing** | Docling | 📄 |

### 📁 Project Structure

```
local-llm-research-agent/
├── src/
│   ├── agent/          # 🤖 Pydantic AI agent
│   ├── api/            # 🚀 FastAPI backend (Phase 2.1)
│   │   ├── models/     # SQLAlchemy ORM models
│   │   └── routes/     # API endpoints
│   ├── rag/            # 🧠 RAG pipeline (Phase 2.1)
│   │   ├── embedder.py          # Ollama embeddings
│   │   ├── redis_vector_store.py # Vector search
│   │   ├── document_processor.py # Docling parsing
│   │   └── schema_indexer.py    # DB schema indexing
│   ├── providers/      # 🦙 LLM provider abstraction
│   ├── mcp/            # 🔌 MCP client and config
│   ├── cli/            # ⌨️ Command-line interface
│   ├── ui/             # 🌐 Streamlit web interface
│   ├── models/         # 📋 Pydantic data models
│   └── utils/          # ⚙️ Configuration and logging
├── alembic/            # 🗄️ Database migrations (Phase 2.1)
├── data/               # 📁 Uploads and cache (Phase 2.1)
├── docker/
│   ├── docker-compose.yml    # 🐳 SQL Server + Redis + API
│   ├── Dockerfile.api        # FastAPI container
│   └── init/                 # 🗃️ Database init scripts
├── tests/              # 🧪 Test suite
├── docs/               # 📚 Documentation
├── examples/           # 💡 Usage examples
└── PRPs/               # 📋 Product Requirement Prompts
```

---

## 🛠️ Development

### 🧪 Running Tests

```bash
# Run all tests
uv run pytest tests/ -v

# Run only unit tests
uv run pytest tests/ -v -m unit

# Run only integration tests
uv run pytest tests/ -v -m integration

# Run with coverage
uv run pytest tests/ --cov=src --cov-report=html
```

### 📋 Code Quality

```bash
# Lint code
uv run ruff check .

# Auto-fix lint issues
uv run ruff check --fix .

# Format code
uv run ruff format .

# Type checking
uv run mypy src/
```

### 🔒 Pre-commit Hooks

```bash
# Install pre-commit hooks
uv run pre-commit install

# Run hooks manually
uv run pre-commit run --all-files
```

---

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

> 📌 **Important**: All external contributions must be submitted via Pull Request.

### Quick Contribution Steps

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests (`uv run pytest tests/ -v`)
5. Submit a Pull Request

---

## 🔐 Security

Please see [SECURITY.md](SECURITY.md) for:
- How to report vulnerabilities
- Security best practices
- Known security considerations

> ⚠️ **Warning**: Never commit credentials or `.env` files!

---

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- [Pydantic AI](https://ai.pydantic.dev/) - Agent framework
- [Ollama](https://ollama.com/) - Local LLM runtime
- [Microsoft Foundry Local](https://github.com/microsoft/Foundry-Local) - Alternative LLM runtime
- [MSSQL MCP Server](https://github.com/Azure-Samples/SQL-AI-samples/tree/main/MssqlMcp) - SQL Server MCP integration
- [Model Context Protocol](https://modelcontextprotocol.io/) - Tool integration standard

---

*Last Updated: December 2025* (Phase 2.1 Backend + RAG)
