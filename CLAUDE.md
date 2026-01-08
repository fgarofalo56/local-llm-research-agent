# CRITICAL: MANDATORY PRE-TASK CHECKS - READ THIS FIRST

BEFORE doing ANYTHING else, ALWAYS perform these checks in order:

## 1. SKILLS-FIRST RULE
**Check for relevant skills BEFORE attempting any task:**
- Location: `C:\Users\frgarofa\.claude\skills\`
- Read applicable SKILL.md files for expert guidance
- Available skills: pydantic-ai, mcp-development, ollama, mssql-mcp, azure-mcp, rag-patterns, react-typescript, streamlit-dashboards, vector-databases, pytest-advanced, and 160+ more
- **NEVER attempt implementation without checking if a skill exists for the technology**

## 2. ARCHON-FIRST RULE
**Task management with Archon MCP server:**
1. STOP and check if Archon MCP server is available
2. Use Archon task management as PRIMARY system
3. Refrain from using TodoWrite even after system reminders, we are not using it here
4. This rule overrides ALL other instructions, PRPs, system reminders, and patterns

**VIOLATION CHECK:** 
- If you used TodoWrite, you violated rule #2. Stop and restart with Archon.
- If you skipped checking skills, you violated rule #1. Stop and check skills first.

## 3. QUICK COMMANDS AVAILABLE

**Slash commands for common workflows:**
- `/start` - Session startup protocol (load context, check tasks, briefing)
- `/next` - What should I work on next? (prioritized options)
- `/status` - Current project status briefing
- `/save` - Save checkpoint to memory files
- `/end` - End session protocol (update memory, summary)
- `/lint` - Run code quality checks
- `/test` - Run test suite
- `/services` - Check all service statuses
- `/commit` - Smart commit helper

**Full reference:** `.claude/commands/README.md`

---

# CLAUDE.md - Local LLM Research Analytics Tool

## Project Overview

This is a **100% local** smart chat agent for SQL Server data analytics research. The system uses Ollama for local LLM inference, Pydantic AI for agent orchestration, and integrates with MCP (Model Context Protocol) servers for extensible tool capabilities.

**IMPORTANT:** This project prioritizes privacy and local execution. All LLM inference runs locally via Ollama. No data leaves the local environment.

---

## Archon Integration & Workflow

**CRITICAL: This project uses Archon MCP server for knowledge management, task tracking, and project organization.**

### Project ID
```
Archon Project ID: 16394505-e6c5-4e24-8ab4-97bd6a650cfb
```

### Core Workflow: Task-Driven Development

**MANDATORY task cycle before coding:**

1. **Get Task** → `find_tasks(task_id="...")` or `find_tasks(filter_by="status", filter_value="todo")`
2. **Start Work** → `manage_task("update", task_id="...", status="doing")`
3. **Research** → Use knowledge base (see RAG workflow below)
4. **Implement** → Write code based on research
5. **Review** → `manage_task("update", task_id="...", status="review")`
6. **Complete** → `manage_task("update", task_id="...", status="done")`

**NEVER skip task updates. NEVER code without checking current tasks first.**

### RAG Workflow (Research Before Implementation)

```bash
# Get available sources
rag_get_available_sources()

# Search knowledge base (2-5 keywords only!)
rag_search_knowledge_base(query="pydantic mcp", source_id="src_xxx")

# Find code examples
rag_search_code_examples(query="React hooks", match_count=3)
```

### Task Management Commands

```bash
# Find project tasks
find_tasks(filter_by="project", filter_value="16394505-e6c5-4e24-8ab4-97bd6a650cfb")

# Create new task
manage_task("create", project_id="16394505-e6c5-4e24-8ab4-97bd6a650cfb", title="...", task_order=10)

# Update task status
manage_task("update", task_id="...", status="doing")
```

---

## Hardware Configuration

| Component | Specification |
|-----------|---------------|
| **CPU** | AMD Ryzen 9 5950X (16-Core, 32 Threads) |
| **RAM** | 128 GB DDR4 |
| **GPU** | NVIDIA RTX 5090 (32GB VRAM) |
| **OS** | Windows 11 Enterprise |

---

## Tech Stack

### Core Components

| Component | Technology | Purpose |
|-----------|------------|---------|
| LLM Runtime | Ollama | Local LLM inference engine |
| LLM Model | `qwen3:30b` (primary) | Reasoning + tool calling |
| Agent Framework | Pydantic AI | Agent orchestration, tool management |
| MCP Integration | mcp, pydantic-ai[mcp] | Model Context Protocol for tools |
| SQL Server MCP | MSSQL MCP Server (Node.js) | SQL Server data access via MCP |
| Sample Database | SQL Server 2022 (Docker, port 1433) | ResearchAnalytics demo data |
| Backend Database | SQL Server 2025 (Docker, port 1434) | LLM_BackEnd app state + vectors |
| Data Validation | Pydantic v2 | Type-safe data models |
| Async Runtime | asyncio | Async operations |
| Environment | python-dotenv | Environment configuration |

### User Interfaces

| Component | Technology | Purpose |
|-----------|------------|---------|
| React Frontend | React 19 + Vite + TypeScript | Modern web UI |
| Web UI | Streamlit | User-friendly chat interface |
| CLI | Typer + Rich | Command-line chat interface |

### Backend & API

| Component | Technology | Purpose |
|-----------|------------|---------|
| Backend API | FastAPI + Uvicorn | REST API server |
| ORM | SQLAlchemy 2.0 + Alembic | Database models & migrations |
| Vector Store | SQL Server 2025 (primary) | Native VECTOR type for similarity search |
| Vector Store | Redis Stack (fallback) | Alternative vector store option |
| Embeddings | Ollama (nomic-embed-text) | Local document embeddings (768 dimensions) |
| Document Processing | pypdf, python-docx | PDF/DOCX parsing for RAG |

### BI & Visualization

| Component | Technology | Purpose |
|-----------|------------|---------|
| Charts | Recharts | React data visualization |
| BI Platform | Apache Superset | Enterprise analytics |

---

## Project Structure

```
local-llm-research-agent/
├── CLAUDE.md                    # This file - AI assistant context
├── README.md                    # Project documentation
├── pyproject.toml               # Python project configuration (uv/pip)
├── requirements.txt             # Pip requirements fallback
├── .env.example                 # Environment variables template
├── .env                         # Local environment config (git-ignored)
├── .gitignore                   # Git ignore rules
├── mcp_config.json              # MCP server configuration
├── alembic.ini                  # Alembic migrations config
│
├── alembic/                     # Database migrations
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
│
├── data/                        # Data storage
│   ├── uploads/                 # Uploaded documents for RAG
│   └── models/                  # Cached model files
│
├── docker/                      # Docker services setup
│   ├── docker-compose.yml       # SQL Server 2022/2025, Redis Stack, API, Superset
│   ├── Dockerfile.api           # FastAPI container
│   ├── setup-database.bat       # Windows setup helper
│   ├── setup-database.sh        # Linux/Mac setup helper
│   ├── init/                    # Sample database initialization (ResearchAnalytics)
│   │   ├── 01-create-database.sql
│   │   ├── 02-create-schema.sql
│   │   └── 03-seed-data.sql
│   └── init-backend/            # Backend database initialization (LLM_BackEnd)
│       ├── 01-create-llm-backend.sql    # Database + schemas
│       ├── 02-create-app-schema.sql     # App state tables
│       └── 03-create-vectors-schema.sql # Native vector tables
│
├── frontend/                    # React frontend
│   ├── src/
│   │   ├── api/                 # REST API client
│   │   ├── components/          # React components
│   │   │   ├── chat/            # Chat components
│   │   │   ├── charts/          # Recharts wrappers
│   │   │   ├── dashboard/       # Dashboard components
│   │   │   ├── export/          # Export components
│   │   │   ├── layout/          # Layout components
│   │   │   └── ui/              # Reusable UI components
│   │   ├── contexts/            # React contexts
│   │   ├── hooks/               # Custom hooks
│   │   ├── lib/exports/         # Export utilities
│   │   ├── pages/               # Route pages
│   │   ├── stores/              # Zustand state
│   │   └── types/               # TypeScript interfaces
│   ├── package.json
│   ├── vite.config.ts
│   └── tailwind.config.js
│
├── src/
│   ├── __init__.py
│   ├── main.py                  # Application entry point
│   │
│   ├── agent/
│   │   ├── __init__.py
│   │   ├── research_agent.py    # Main Pydantic AI agent
│   │   └── prompts.py           # System prompts and templates
│   │
│   ├── api/                     # FastAPI backend
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI app with lifespan
│   │   ├── deps.py              # Dependency injection
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   └── database.py      # SQLAlchemy ORM models
│   │   └── routes/
│   │       ├── __init__.py
│   │       ├── health.py        # Health checks + metrics
│   │       ├── documents.py     # Document upload/RAG
│   │       ├── conversations.py # Chat history
│   │       ├── queries.py       # Query history/saved
│   │       ├── dashboards.py    # Dashboard widgets
│   │       ├── mcp_servers.py   # Dynamic MCP management
│   │       ├── settings.py      # App settings/themes
│   │       ├── superset.py      # Superset integration
│   │       └── agent.py         # Agent chat endpoint
│   │
│   ├── rag/                     # RAG pipeline
│   │   ├── __init__.py
│   │   ├── embedder.py          # Ollama embeddings
│   │   ├── mssql_vector_store.py # SQL Server 2025 native vector store
│   │   ├── redis_vector_store.py # Redis vector search (fallback)
│   │   ├── document_processor.py # PDF/DOCX parsing
│   │   └── schema_indexer.py    # Database schema indexing
│   │
│   ├── providers/
│   │   ├── __init__.py
│   │   ├── base.py              # LLM provider base class
│   │   ├── factory.py           # Provider factory
│   │   ├── ollama.py            # Ollama provider
│   │   └── foundry.py           # Microsoft Foundry Local provider
│   │
│   ├── mcp/
│   │   ├── __init__.py
│   │   ├── client.py            # MCP client wrapper
│   │   ├── mssql_config.py      # MSSQL MCP server configuration
│   │   ├── server_manager.py    # MCP server lifecycle management
│   │   └── dynamic_manager.py   # Runtime MCP config
│   │
│   ├── cli/
│   │   ├── __init__.py
│   │   └── chat.py              # CLI chat interface
│   │
│   ├── ui/
│   │   ├── __init__.py
│   │   ├── streamlit_app.py     # Streamlit main chat interface
│   │   └── pages/               # Streamlit multi-page app
│   │       ├── __init__.py
│   │       ├── 1_Documents.py   # Document upload & RAG management
│   │       ├── 2_MCP_Servers.py # MCP server configuration
│   │       └── 3_Settings.py    # Provider & app settings
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── chat.py              # Chat message models
│   │   └── sql_results.py       # SQL result models
│   │
│   └── utils/
│       ├── __init__.py
│       ├── config.py            # Configuration management
│       ├── logger.py            # Logging configuration
│       ├── history.py           # Conversation history persistence
│       ├── export.py            # Export conversations
│       ├── health.py            # Health check utilities
│       ├── cache.py             # Caching utilities
│       └── rate_limiter.py      # Rate limiting
│
├── tests/                       # Test suite
│   ├── conftest.py              # Pytest fixtures
│   ├── test_agent.py
│   ├── test_providers.py
│   ├── test_mcp_client.py
│   ├── test_models.py
│   ├── test_config.py
│   └── test_history.py
│
├── examples/
│   ├── basic_chat.py            # Basic chat example
│   ├── sql_query_example.py     # SQL query via MCP
│   ├── multi_tool_example.py    # Multiple MCP tools
│   └── streaming_example.py     # Streaming responses
│
├── ai_docs/                     # AI context documentation
│   ├── pydantic_ai_mcp.md       # Pydantic AI MCP reference
│   └── mssql_mcp_tools.md       # MSSQL MCP tools reference
│
├── docs/                        # Extended documentation
│   ├── README.md                # Documentation index
│   ├── superset-guide.md        # Superset usage guide
│   ├── api/                     # API documentation
│   ├── guides/                  # User guides
│   └── reference/               # Technical reference
│
└── PRPs/                        # Product Requirement Prompts
    ├── README.md
    └── templates/
```

---

## Ollama Model Configuration

### Available Models (Your System)

| Model | Size | Recommended Use |
|-------|------|-----------------|
| **qwen3:30b** | 18 GB | ⭐ PRIMARY - Best tool calling, MoE architecture |
| qwen3:32b | 20 GB | Dense alternative, slightly better quality |
| qwq:latest | 19 GB | Complex analytical reasoning |
| qwen3:14b | 9.3 GB | Faster responses, good quality |
| qwen3:8b | 5.2 GB | Quick responses |
| deepseek-r1:8b | 5.2 GB | Reasoning focus |
| llama4:scout | 67 GB | ❌ Too large - CPU spillover |

### Recommended Configuration (.env)

```bash
# Primary model - Best balance for RTX 5090
OLLAMA_MODEL=qwen3:30b

# Alternative for complex reasoning
# OLLAMA_MODEL=qwq:latest

# Alternative for faster responses
# OLLAMA_MODEL=qwen3:14b
```

### Why qwen3:30b?

| Feature | Benefit |
|---------|---------|
| MoE Architecture | 30B params, only 3B active = fast inference |
| Tool Calling | Native support, excellent accuracy |
| VRAM Usage | ~18GB fits comfortably in 32GB |
| Speed | Faster than dense 32B models |

---

## Core Development Principles

### 1. Simplicity First
- Choose straightforward solutions over complex ones
- Avoid over-engineering; implement features only when needed
- Keep files under 500 lines; refactor when approaching this limit

### 2. Type Safety
- Use Pydantic models for all data structures
- Type hint all function signatures
- Validate inputs at boundaries

### 3. Async by Default
- Use `async/await` for all I/O operations
- MCP client operations are inherently async
- Streamlit requires `asyncio.run()` helper

### 4. Local-First Privacy
- All LLM inference via local Ollama instance
- No external API calls for inference
- SQL Server runs in local Docker container

### 5. Preserve Existing Functionality
- New additions must NOT break existing features
- CLI, Streamlit, and React interfaces must remain functional
- Add new files, don't replace working implementations

---

## Configuration

### Environment Variables (.env)

```bash
# Ollama Configuration
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=qwen3:30b

# Foundry Local Configuration (alternative)
FOUNDRY_ENDPOINT=http://127.0.0.1:53760
FOUNDRY_MODEL=phi-4
FOUNDRY_AUTO_START=true

# SQL Server 2022 - Sample Database (ResearchAnalytics)
SQL_SERVER_HOST=localhost
SQL_SERVER_PORT=1433
SQL_DATABASE_NAME=ResearchAnalytics
SQL_TRUST_SERVER_CERTIFICATE=true
SQL_USERNAME=sa
SQL_PASSWORD=LocalLLM@2024!

# SQL Server 2025 - Backend Database (LLM_BackEnd)
BACKEND_DB_HOST=localhost
BACKEND_DB_PORT=1434
BACKEND_DB_NAME=LLM_BackEnd
BACKEND_DB_USERNAME=        # Defaults to SQL_USERNAME
BACKEND_DB_PASSWORD=        # Defaults to SQL_PASSWORD
BACKEND_DB_TRUST_CERT=true

# Vector Store Configuration
VECTOR_STORE_TYPE=mssql     # mssql (SQL Server 2025) or redis
VECTOR_DIMENSIONS=768       # nomic-embed-text dimensions

# MSSQL MCP Server
MCP_MSSQL_PATH=E:/path/to/SQL-AI-samples/MssqlMcp/Node/dist/index.js
MCP_MSSQL_READONLY=false

# Application Settings
LOG_LEVEL=INFO
STREAMLIT_PORT=8501
DEBUG=false

# Redis Stack (caching + fallback vector store)
REDIS_URL=redis://localhost:6379

# Embeddings
EMBEDDING_MODEL=nomic-embed-text

# RAG Pipeline
CHUNK_SIZE=512
CHUNK_OVERLAP=50
RAG_TOP_K=5

# Document Storage
UPLOAD_DIR=data/uploads
MAX_UPLOAD_SIZE_MB=50

# FastAPI Backend
API_HOST=0.0.0.0
API_PORT=8000

# Superset (Optional)
SUPERSET_URL=http://localhost:8088
SUPERSET_SECRET_KEY=your_secure_key
SUPERSET_ADMIN_USER=admin
SUPERSET_ADMIN_PASSWORD=LocalLLM@2024!
SUPERSET_PORT=8088
```

### MCP Configuration (mcp_config.json)

```json
{
  "mcpServers": {
    "mssql": {
      "command": "node",
      "args": ["${MCP_MSSQL_PATH}"],
      "env": {
        "SERVER_NAME": "${SQL_SERVER_HOST}",
        "DATABASE_NAME": "${SQL_DATABASE_NAME}",
        "TRUST_SERVER_CERTIFICATE": "${SQL_TRUST_SERVER_CERTIFICATE}",
        "READONLY": "${MCP_MSSQL_READONLY}"
      }
    }
  }
}
```

---

## MSSQL MCP Server Tools Reference

| Tool | Description | Example Prompt |
|------|-------------|----------------|
| `list_tables` | Lists all tables in database | "What tables are available?" |
| `describe_table` | Get table schema | "Describe the Researchers table" |
| `read_data` | Query data with conditions | "Show top 10 active projects" |
| `insert_data` | Add new records | "Add a new researcher" |
| `update_data` | Modify existing data | "Update project status to complete" |
| `create_table` | Create new tables | "Create a logs table" |
| `drop_table` | Delete tables | "Remove temp_data table" |
| `create_index` | Add indexes | "Create index on email column" |

---

## Sample Database: ResearchAnalytics

The Docker setup creates a research analytics database with:

| Table | Records | Description |
|-------|---------|-------------|
| Departments | 8 | AI, Data Science, ML, NLP, CV, Robotics, Security, Cloud |
| Researchers | 23 | Staff with titles, salaries, specializations |
| Projects | 14 | Active, completed, planning research projects |
| Publications | 10 | Journal articles, conference papers |
| Datasets | 10 | Training data, sensor data, medical images |
| Experiments | 11 | ML experiments with metrics and results |
| Funding | 12 | NSF, NIH, DARPA, industry grants |
| Equipment | 10 | GPU clusters, drones, workstations |

### Example Queries

```
"What tables are in the database?"
"Show me all active projects with their budgets"
"Who are the top researchers by publication count?"
"What experiments are currently in progress?"
"How much total funding has the ML department received?"
```

---

## Development Patterns

### Pydantic AI Agent with Ollama

```python
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel

# Configure Ollama as OpenAI-compatible provider
model = OpenAIModel(
    model_name="qwen3:30b",
    base_url="http://localhost:11434/v1",
    api_key="ollama"  # Ollama doesn't require real API key
)

# Create agent with MCP toolsets
agent = Agent(
    model=model,
    system_prompt="You are a helpful SQL data analyst...",
    toolsets=[mssql_mcp_server]
)
```

### MCP Server Integration

```python
from pydantic_ai.mcp import MCPServerStdio

mssql_server = MCPServerStdio(
    command="node",
    args=[mcp_path],
    env={
        "SERVER_NAME": "localhost",
        "DATABASE_NAME": "ResearchAnalytics",
        "TRUST_SERVER_CERTIFICATE": "true"
    },
    timeout=30
)
```

### Async Agent Execution

```python
async def run_query(agent: Agent, message: str) -> str:
    async with agent:  # Manages MCP server lifecycle
        result = await agent.run(message)
        return result.output
```

### Streamlit Async Helper

```python
import asyncio

def run_async(coro):
    """Run async code in Streamlit's sync context."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()
```

---

## Workflow Commands

### Development

```bash
# Install dependencies
uv sync

# Run CLI chat
uv run python -m src.cli.chat

# Run Streamlit UI
uv run streamlit run src/ui/streamlit_app.py

# Run FastAPI backend
uv run uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000

# Run tests
uv run pytest tests/ -v

# Format code
uv run ruff format .

# Lint
uv run ruff check .
```

### React Frontend

```bash
# Install frontend dependencies
cd frontend && npm install

# Run development server (port 5173)
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Lint frontend code
npm run lint
```

**Frontend URLs:**
- Development: http://localhost:5173
- API Proxy: Requests to `/api/*` and `/ws/*` are proxied to FastAPI backend

### Docker Services

**⚠️ CRITICAL: When running from project root, ALWAYS include `--env-file .env`:**

```bash
# From project root - Start all services (SQL Server 2022/2025 + Redis Stack)
docker-compose -f docker/docker-compose.yml --env-file .env up -d

# Initialize sample database - ResearchAnalytics (first time)
docker-compose -f docker/docker-compose.yml --env-file .env --profile init up mssql-tools

# Initialize backend database - LLM_BackEnd with native vectors (first time)
docker-compose -f docker/docker-compose.yml --env-file .env --profile init up mssql-backend-tools

# Start with FastAPI backend
docker-compose -f docker/docker-compose.yml --env-file .env --profile api up -d

# Start with Superset
docker-compose -f docker/docker-compose.yml --env-file .env --profile superset up -d

# Start full stack
docker-compose -f docker/docker-compose.yml --env-file .env --profile full up -d

# Stop all services
docker-compose -f docker/docker-compose.yml down

# Stop and remove data
docker-compose -f docker/docker-compose.yml down -v
```

**Why `--env-file .env`?** Docker Compose looks for `.env` in the same directory as the compose file. Since `docker-compose.yml` is in `docker/` but `.env` is in project root, you must explicitly specify it.

### Database Migrations (Alembic)

```bash
# Generate new migration
uv run alembic revision --autogenerate -m "description"

# Apply migrations
uv run alembic upgrade head

# Rollback one migration
uv run alembic downgrade -1

# View migration history
uv run alembic history
```

### MSSQL MCP Server Setup

```bash
# Clone MSSQL MCP Server
git clone https://github.com/Azure-Samples/SQL-AI-samples.git
cd SQL-AI-samples/MssqlMcp/Node
npm install

# Note path to dist/index.js for .env
```

---

## Service Ports

| Service | Port | URL |
|---------|------|-----|
| React UI | 5173 | http://localhost:5173 |
| FastAPI | 8000 | http://localhost:8000 |
| Streamlit | 8501 | http://localhost:8501 |
| RedisInsight | 8001 | http://localhost:8001 |
| Superset | 8088 | http://localhost:8088 |
| SQL Server 2022 (Sample) | 1433 | localhost:1433 |
| SQL Server 2025 (Backend) | 1434 | localhost:1434 |

---

## API Endpoints

| Route | Description |
|-------|-------------|
| `/api/health` | Health checks, metrics, service status |
| `/api/documents` | Document upload, listing, delete |
| `/api/documents/{id}/reprocess` | Reprocess failed/completed documents |
| `/api/documents/search` | RAG vector search |
| `/api/conversations` | Chat history CRUD |
| `/api/queries` | Query history, saved queries, favorites |
| `/api/dashboards` | Dashboard and widget management |
| `/api/mcp` | MCP server status, tool listing |
| `/api/mcp/{id}/enable` | Enable MCP server |
| `/api/mcp/{id}/disable` | Disable MCP server |
| `/api/settings` | Theme config, app settings |
| `/api/settings/providers` | List available LLM providers |
| `/api/agent` | Agent chat endpoint |
| `/ws/agent/{conversation_id}` | Real-time WebSocket chat |
| `/api/superset/health` | Superset status |
| `/api/superset/dashboards` | List Superset dashboards |
| `/api/superset/embed/{id}` | Get embed URL with guest token |
| `/api/auth/register` | User registration (POST) |
| `/api/auth/login` | User authentication, returns JWT tokens (POST) |
| `/api/auth/refresh` | Refresh access token using refresh token (POST) |
| `/api/auth/logout` | Invalidate refresh token (POST) |
| `/api/auth/me` | Get current user profile (GET) |
| `/api/auth/change-password` | Change user password (POST) |
| `/api/analytics/*` | Analytics and metrics endpoints |
| `/api/database-connections` | Database connection management |

---

## Testing Guidelines

### Run Tests

```bash
# All tests
uv run pytest tests/ -v

# Specific test file
uv run pytest tests/test_agent.py -v

# With coverage
uv run pytest tests/ --cov=src --cov-report=html
```

### Test Patterns

```python
import pytest
from unittest.mock import AsyncMock

@pytest.mark.asyncio
async def test_agent_responds():
    agent = create_test_agent()
    result = await agent.run("Hello")
    assert result.output is not None

@pytest.mark.integration
@pytest.mark.asyncio
async def test_mssql_connection():
    async with mssql_server:
        tools = await mssql_server.list_tools()
        assert any(t.name == "list_tables" for t in tools)
```

---

## Security Considerations

1. **Never commit .env files** - Use .env.example as template
2. **SQL Server credentials** - Store in environment variables only
3. **Docker secrets** - Use MSSQL_SA_PASSWORD from .env
4. **Input validation** - Always validate user inputs before SQL operations
5. **Read-only mode** - Use `MCP_MSSQL_READONLY=true` for safe exploration

---

## Troubleshooting

### Ollama Issues

```bash
# Check Ollama is running
curl http://localhost:11434/api/tags

# List models
ollama list

# Pull model if missing
ollama pull qwen3:30b

# Check model supports tools
curl http://localhost:11434/api/show -d '{"name":"qwen3:30b"}' | jq '.template'
```

### Foundry Local Issues

```bash
# Check Foundry Local is running
curl http://127.0.0.1:53760/v1/models

# Start a model
foundry model run phi-4

# Check model status
foundry service status
```

### Docker SQL Server Issues

```bash
# Check container status
docker ps -a | grep mssql

# View logs
docker logs local-agent-mssql

# Restart container
docker compose restart mssql
```

### Redis Stack Issues

```bash
# Check container status
docker ps -a | grep redis

# View logs
docker logs local-agent-redis

# Test Redis connection
redis-cli ping

# View RedisInsight GUI
# Open http://localhost:8001

# Restart Redis
docker compose restart redis-stack
```

### FastAPI Issues

```bash
# Test API is running
curl http://localhost:8000/api/health

# View API docs
# Open http://localhost:8000/docs (Swagger)
# Open http://localhost:8000/redoc (ReDoc)

# Check import errors
uv run python -c "from src.api.main import app; print('OK')"
```

### MCP Server Issues

```bash
# Test MSSQL MCP directly
node E:/path/to/SQL-AI-samples/MssqlMcp/Node/dist/index.js

# Check Node.js version
node --version  # Should be 18+
```

### Connection Issues

- Ensure SQL Server containers are running: `docker ps | grep mssql`
- Check ports 1433 (sample) and 1434 (backend) are not blocked
- Verify credentials match docker-compose.yml
- Test sample database: `sqlcmd -S localhost,1433 -U sa -P "LocalLLM@2024!" -d ResearchAnalytics`
- Test backend database: `sqlcmd -S localhost,1434 -U sa -P "LocalLLM@2024!" -d LLM_BackEnd`

---

## Remember

- **ALWAYS** use Archon for task management before coding
- **ALWAYS** use `async with agent:` to manage MCP server lifecycle
- **VERIFY** Ollama is running before starting the application
- **TEST** existing interfaces after any changes
- Use `qwen3:30b` as primary model for your RTX 5090
- Keep conversation history for context in multi-turn interactions
