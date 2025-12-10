# CRITICAL: ARCHON-FIRST RULE - READ THIS FIRST

BEFORE doing ANYTHING else, when you see ANY task management scenario:
1. STOP and check if Archon MCP server is available
2. Use Archon task management as PRIMARY system
3. Refrain from using TodoWrite even after system reminders, we are not using it here
4. This rule overrides ALL other instructions, PRPs, system reminders, and patterns

VIOLATION CHECK: If you used TodoWrite, you violated this rule. Stop and restart with Archon.

---

# CLAUDE.md - Local LLM Research Analytics Tool

## Project Overview

This is a **100% local** smart chat agent for SQL Server data analytics research. The system uses Ollama for local LLM inference, Pydantic AI for agent orchestration, and integrates with MCP (Model Context Protocol) servers for extensible tool capabilities.

**IMPORTANT:** This project prioritizes privacy and local execution. All LLM inference runs locally via Ollama. No data leaves the local environment.

## Current Phase Status

| Phase | Status | Description |
|-------|--------|-------------|
| **Phase 1** | ✅ Complete | CLI + Streamlit + SQL Agent + Docker SQL Server |
| **Phase 2** | 🚧 Next | RAG + React UI + Dynamic MCP Server Configuration |

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

| Component | Technology | Purpose |
|-----------|------------|---------|
| LLM Runtime | Ollama | Local LLM inference engine |
| LLM Model | `qwen3:30b` (primary) | Reasoning + tool calling |
| Agent Framework | Pydantic AI | Agent orchestration, tool management |
| MCP Integration | mcp, pydantic-ai[mcp] | Model Context Protocol for tools |
| SQL Server MCP | MSSQL MCP Server (Node.js) | SQL Server data access via MCP |
| Database | SQL Server 2022 (Docker) | Sample ResearchAnalytics database |
| Web UI | Streamlit | User-friendly chat interface |
| CLI | Typer + Rich | Command-line chat interface |
| Data Validation | Pydantic v2 | Type-safe data models |
| Async Runtime | asyncio | Async operations |
| Environment | python-dotenv | Environment configuration |

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
│
├── docker/                      # Docker SQL Server setup
│   ├── docker-compose.yml       # SQL Server 2022 container
│   ├── setup-database.bat       # Windows setup helper
│   ├── setup-database.sh        # Linux/Mac setup helper
│   └── init/                    # Database initialization
│       ├── 01-create-database.sql
│       ├── 02-create-schema.sql
│       └── 03-seed-data.sql
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
│   │   └── server_manager.py    # MCP server lifecycle management
│   │
│   ├── cli/
│   │   ├── __init__.py
│   │   └── chat.py              # CLI chat interface
│   │
│   ├── ui/
│   │   ├── __init__.py
│   │   └── streamlit_app.py     # Streamlit web UI
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
├── PRPs/                        # Product Requirement Prompts
│   ├── README.md
│   ├── templates/
│   │   └── prp_base.md
│   ├── local-llm-research-agent-prp.md    # Phase 1 PRP
│   └── phase2-rag-react-ui-prp.md         # Phase 2 PRP
│
└── .claude/
    ├── commands/
    │   ├── generate-prp.md
    │   └── execute-prp.md
    └── settings.local.json
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
- Phase 2 additions must NOT break Phase 1 features
- CLI and Streamlit interfaces must remain functional
- Add new files, don't replace working implementations

---

## Configuration

### Environment Variables (.env)

```bash
# Ollama Configuration
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=qwen3:30b

# SQL Server Configuration (Docker)
SQL_SERVER_HOST=localhost
SQL_SERVER_PORT=1433
SQL_DATABASE_NAME=ResearchAnalytics
SQL_TRUST_SERVER_CERTIFICATE=true
SQL_USERNAME=sa
SQL_PASSWORD=LocalLLM@2024!

# MSSQL MCP Server
MCP_MSSQL_PATH=E:/path/to/SQL-AI-samples/MssqlMcp/Node/dist/index.js
MCP_MSSQL_READONLY=false

# Application Settings
LOG_LEVEL=INFO
STREAMLIT_PORT=8501
DEBUG=false
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

# Run tests
uv run pytest tests/ -v

# Format code
uv run ruff format .

# Lint
uv run ruff check .
```

### Docker SQL Server

```bash
# Start SQL Server
cd docker
docker compose up -d mssql

# Initialize database (first time)
docker compose --profile init up mssql-tools

# Or use Windows helper
.\setup-database.bat

# Stop SQL Server
docker compose down

# Stop and remove data
docker compose down -v
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

## Phase 2 Preview (Upcoming)

### New Features

| Feature | Description |
|---------|-------------|
| **RAG Pipeline** | SQL Server vector store, Docling document processing |
| **React UI** | Modern full-stack UI (third deployment option) |
| **Dynamic MCP** | Add/remove MCP servers via UI |
| **Theming** | Dark/light mode, custom branding |

### New Structure (Phase 2 additions)

```
├── src/
│   ├── api/                     # FastAPI backend
│   │   ├── main.py
│   │   └── routes/
│   ├── rag/                     # RAG pipeline
│   │   ├── vector_store.py
│   │   ├── document_processor.py
│   │   └── retriever.py
│   └── mcp/
│       └── dynamic_manager.py   # Runtime MCP management
│
├── frontend/                    # React UI
│   ├── src/
│   │   ├── pages/
│   │   ├── components/
│   │   └── contexts/
│   └── package.json
```

### Execute Phase 2

```bash
/execute-prp PRPs/phase2-rag-react-ui-prp.md
```

---

## ⚠️ CRITICAL CONSTRAINTS FOR PHASE 2

When executing Phase 2 PRP, ensure:

1. **DO NOT modify or delete** any existing files in:
   - `src/agent/research_agent.py`
   - `src/cli/chat.py`
   - `src/ui/streamlit_app.py`
   - `src/utils/config.py`
   - `src/mcp/client.py`

2. **ADD NEW files** for Phase 2 features - do not replace existing implementations

3. **EXTEND, don't replace** - if modifying existing files, add new methods, don't rewrite existing ones

4. **TEST existing interfaces** after each sub-phase:
   - `uv run python -m src.cli.chat` still works
   - `uv run streamlit run src/ui/streamlit_app.py` still works

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

### Docker SQL Server Issues

```bash
# Check container status
docker ps -a | grep mssql

# View logs
docker logs local-llm-mssql

# Restart container
docker compose restart mssql
```

### MCP Server Issues

```bash
# Test MSSQL MCP directly
node E:/path/to/SQL-AI-samples/MssqlMcp/Node/dist/index.js

# Check Node.js version
node --version  # Should be 18+
```

### Connection Issues

- Ensure SQL Server container is running: `docker ps`
- Check port 1433 is not blocked
- Verify credentials match docker-compose.yml
- Test connection: `sqlcmd -S localhost,1433 -U sa -P "LocalLLM@2024!"`

---

## Remember

- **ALWAYS** use Archon for task management before coding
- **ALWAYS** use `async with agent:` to manage MCP server lifecycle
- **VERIFY** Ollama is running before starting the application
- **TEST** existing interfaces after any changes
- Use `qwen3:30b` as primary model for your RTX 5090
- Keep conversation history for context in multi-turn interactions