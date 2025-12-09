# CLAUDE.md - Local LLM Research Analytics Tool

## Project Overview

This is a **100% local** smart chat agent for SQL Server data analytics research. The system uses Ollama for local LLM inference, Pydantic AI for agent orchestration, and integrates with MCP (Model Context Protocol) servers for extensible tool capabilities - specifically the MSSQL MCP Server for SQL Server data access.

**IMPORTANT:** This project prioritizes privacy and local execution. All LLM inference runs locally via Ollama. No data leaves the local environment.

## Tech Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| LLM Runtime | Ollama | Local LLM inference engine |
| LLM Model | `qwen2.5:7b-instruct` or `llama3.1:8b` | Reasoning + tool calling |
| Agent Framework | Pydantic AI | Agent orchestration, tool management |
| MCP Integration | mcp, pydantic-ai[mcp] | Model Context Protocol for tools |
| SQL Server MCP | MSSQL MCP Server (Node.js) | SQL Server data access via MCP |
| Web UI | Streamlit | User-friendly chat interface |
| CLI | Typer + Rich | Command-line chat interface |
| Data Validation | Pydantic v2 | Type-safe data models |
| Async Runtime | asyncio | Async operations |
| Environment | python-dotenv | Environment configuration |

## Project Structure

```
local-llm-research-agent/
├── CLAUDE.md                    # This file - AI assistant context
├── README.md                    # Project documentation
├── pyproject.toml               # Python project configuration (uv/pip)
├── requirements.txt             # Pip requirements fallback
├── .env.example                 # Environment variables template
├── .gitignore                   # Git ignore rules
├── mcp_config.json              # MCP server configuration
│
├── docker/                      # Docker SQL Server setup
│   ├── docker-compose.yml       # SQL Server 2022 container
│   ├── setup-database.bat       # Windows setup helper
│   └── init/                    # Database initialization scripts
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
│   │   ├── prompts.py           # System prompts and templates
│   │   └── tools.py             # Custom tool definitions
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
│       └── logger.py            # Logging configuration
│
├── tests/
│   ├── __init__.py
│   ├── test_agent.py
│   ├── test_mcp_client.py
│   └── test_cli.py
│
├── PRPs/
│   ├── templates/
│   │   └── prp_base.md          # PRP template
│   └── README.md                # PRP documentation
│
├── .claude/
│   ├── commands/
│   │   ├── generate-prp.md      # PRP generation command
│   │   └── execute-prp.md       # PRP execution command
│   └── settings.local.json      # Claude Code settings
│
├── ai_docs/                     # AI documentation context
│   ├── pydantic_ai_mcp.md       # Pydantic AI MCP integration docs
│   └── mssql_mcp_tools.md       # MSSQL MCP tools reference
│
└── examples/
    ├── basic_chat.py            # Basic chat example
    ├── sql_query_example.py     # SQL query via MCP example
    └── multi_tool_example.py    # Multiple MCP tools example
```

## Core Principles

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
- Streamlit requires careful async handling with `asyncio.run()`

### 4. Local-First Privacy
- All LLM inference via local Ollama instance
- No external API calls for inference
- SQL Server connection stays local/on-premises

## Development Guidelines

### Python Standards

```python
# Use modern Python (3.11+) features
from typing import AsyncIterator
from dataclasses import dataclass
from pydantic import BaseModel, Field

# Prefer explicit imports
from pydantic_ai import Agent, RunContext
from pydantic_ai.mcp import MCPServerStdio

# Use async context managers for MCP
async with agent:
    result = await agent.run(user_message)
```

### Pydantic AI Agent Pattern

```python
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel

# Configure Ollama as OpenAI-compatible provider
model = OpenAIModel(
    model_name="qwen2.5:7b-instruct",
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

# MSSQL MCP Server via stdio
mssql_server = MCPServerStdio(
    command="node",
    args=["/path/to/mssql-mcp/dist/index.js"],
    env={
        "SERVER_NAME": "localhost",
        "DATABASE_NAME": "your_database",
        "TRUST_SERVER_CERTIFICATE": "true"
    },
    timeout=30
)
```

### Error Handling

```python
from pydantic_ai.exceptions import ModelRetry, UnexpectedModelBehavior

try:
    result = await agent.run(message)
except ModelRetry as e:
    logger.warning(f"Model requested retry: {e}")
except UnexpectedModelBehavior as e:
    logger.error(f"Unexpected model behavior: {e}")
```

### Logging

```python
import structlog

logger = structlog.get_logger()

# Use structured logging
logger.info("agent_run_started", user_message=message[:100])
logger.debug("mcp_tool_called", tool_name=tool.name, args=tool.args)
```

## Configuration

### Environment Variables (.env)

```bash
# Ollama Configuration
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=qwen2.5:7b-instruct

# SQL Server Configuration (for MSSQL MCP)
SQL_SERVER_HOST=localhost
SQL_SERVER_PORT=1433
SQL_DATABASE_NAME=your_database
SQL_TRUST_SERVER_CERTIFICATE=true

# Optional: SQL Authentication (if not using Windows Auth)
SQL_USERNAME=
SQL_PASSWORD=

# Application Settings
LOG_LEVEL=INFO
STREAMLIT_PORT=8501
```

### MCP Configuration (mcp_config.json)

```json
{
  "mcpServers": {
    "mssql": {
      "command": "node",
      "args": ["${MCP_MSSQL_PATH}/dist/index.js"],
      "env": {
        "SERVER_NAME": "${SQL_SERVER_HOST}",
        "DATABASE_NAME": "${SQL_DATABASE_NAME}",
        "TRUST_SERVER_CERTIFICATE": "${SQL_TRUST_SERVER_CERTIFICATE}",
        "READONLY": "false"
      }
    }
  }
}
```

## MSSQL MCP Server Tools Reference

The MSSQL MCP Server provides these tools for SQL Server interaction:

| Tool | Description | Use Case |
|------|-------------|----------|
| `list_tables` | Lists all tables in the database | Schema discovery |
| `describe_table` | Get schema details for a table | Understanding table structure |
| `read_data` | Query data with conditions | Data retrieval and analysis |
| `insert_data` | Insert rows (supports batch) | Data population |
| `update_data` | Modify existing data | Data maintenance |
| `create_table` | Create new tables | Schema management |
| `drop_table` | Delete tables | Schema cleanup |
| `create_index` | Create indexes | Performance optimization |

## Ollama Model Requirements

### Recommended Models by GPU VRAM

#### RTX 5090 (32GB VRAM) - Maximum Quality
1. **qwen2.5:32b-instruct** (Primary recommendation)
   - Excellent tool calling + reasoning
   - Best quality responses
   - Memory: ~22GB VRAM
   - Pull: `ollama pull qwen2.5:32b-instruct`

2. **llama3.3:70b-instruct-q4_K_M** (Near GPT-4 quality)
   - Superior reasoning and coherence
   - Partial CPU offload (~38GB total)
   - Pull: `ollama pull llama3.3:70b-instruct-q4_K_M`

3. **deepseek-r1:32b** (Advanced reasoning)
   - Best for complex analytical queries
   - Slower but more accurate
   - Pull: `ollama pull deepseek-r1:32b`

#### RTX 4090/3090 (24GB VRAM)
1. **qwen2.5:14b-instruct** - Great balance
2. **llama3.1:8b-instruct** - Fast and reliable

#### RTX 4080/3080 (16GB VRAM) or Lower
1. **qwen2.5:7b-instruct** - Best tool calling at this size
2. **mistral:7b-instruct** - Lightweight option

### Pull Model Command
```bash
ollama pull qwen2.5:7b-instruct
# or
ollama pull llama3.1:8b
```

## Testing Guidelines

### Unit Tests
```python
import pytest
from unittest.mock import AsyncMock

@pytest.mark.asyncio
async def test_agent_responds():
    agent = create_test_agent()
    result = await agent.run("Hello")
    assert result.output is not None
```

### Integration Tests
```python
@pytest.mark.integration
@pytest.mark.asyncio
async def test_mssql_connection():
    async with mssql_server:
        tools = await mssql_server.list_tools()
        assert any(t.name == "list_tables" for t in tools)
```

## Common Patterns

### CLI Chat Loop

```python
from rich.console import Console
from rich.prompt import Prompt

console = Console()

async def chat_loop(agent: Agent):
    console.print("[bold green]Chat started. Type 'quit' to exit.[/]")
    
    while True:
        user_input = Prompt.ask("[bold blue]You[/]")
        if user_input.lower() in ("quit", "exit"):
            break
            
        async with agent:
            result = await agent.run(user_input)
            console.print(f"[bold green]Agent:[/] {result.output}")
```

### Streamlit Integration

```python
import streamlit as st
import asyncio

def run_async(coro):
    """Helper to run async code in Streamlit."""
    return asyncio.run(coro)

# In Streamlit app
if prompt := st.chat_input("Ask about your data..."):
    with st.chat_message("user"):
        st.write(prompt)
    
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response = run_async(agent.run(prompt))
            st.write(response.output)
```

## Key Dependencies

```toml
[project]
dependencies = [
    "pydantic-ai[mcp]>=0.2.0",
    "pydantic>=2.0.0",
    "streamlit>=1.30.0",
    "typer>=0.9.0",
    "rich>=13.0.0",
    "python-dotenv>=1.0.0",
    "structlog>=24.0.0",
    "httpx>=0.27.0",
]
```

## Security Considerations

1. **Never commit .env files** - Use .env.example as template
2. **SQL Server credentials** - Prefer Windows Authentication when possible
3. **Connection strings** - Store in environment variables, not code
4. **Input validation** - Always validate user inputs before SQL operations
5. **Read-only mode** - Use `READONLY=true` for safe exploration

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
```

### MSSQL MCP Server Setup
```bash
# Clone and build MSSQL MCP Server
git clone https://github.com/Azure-Samples/SQL-AI-samples.git
cd SQL-AI-samples/MssqlMcp/Node
npm install

# The index.js will be at: ./dist/index.js
```

## Troubleshooting

### Ollama Connection Issues
```bash
# Check Ollama is running
curl http://localhost:11434/api/tags

# Pull model if missing
ollama pull qwen2.5:7b-instruct
```

### MCP Server Issues
```bash
# Test MSSQL MCP directly
node /path/to/mssql-mcp/dist/index.js
```

### SQL Server Connection
- Ensure SQL Server is running and accessible
- Check firewall rules for port 1433
- Verify credentials and database name
- For Windows Auth, ensure proper domain configuration

## Remember

- **IMPORTANT:** Always test MCP tool availability before using in production
- **Proactively** validate Ollama model supports tool calling before agent creation
- Keep conversation history for context in multi-turn interactions
- Use streaming for better UX in both CLI and Streamlit interfaces
