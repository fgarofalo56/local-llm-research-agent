# PRP: Local LLM Research Analytics Tool - Complete Implementation

## Goal

Build a **100% local** smart chat agent that enables natural language interaction with SQL Server data. The system will use Ollama for local LLM inference, Pydantic AI for agent orchestration, and the MSSQL MCP Server for SQL Server data access. Users can interact via both a CLI interface for testing and a Streamlit web UI for production use.

## Why

- **Privacy**: All data processing happens locally - no cloud APIs, no data leakage
- **Cost Efficiency**: Zero inference costs after initial setup (runs on local hardware)
- **SQL Democratization**: Enable non-technical users to query SQL Server using natural language
- **Extensibility**: MCP architecture allows easy addition of new tools and data sources
- **Research Platform**: Foundation for exploring local LLM capabilities with enterprise data

## What

A complete local AI agent system with the following capabilities:

### Success Criteria

- [ ] Docker SQL Server starts with sample ResearchAnalytics database
- [ ] User can start CLI chat and query SQL Server data using natural language
- [ ] User can start Streamlit web UI and have conversations about their data
- [ ] Agent correctly invokes MSSQL MCP tools (list tables, describe table, read data, etc.)
- [ ] System handles multi-turn conversations with context retention
- [ ] Configuration is externalized (environment variables, config files)
- [ ] Error handling provides clear, actionable feedback
- [ ] All components work 100% offline/locally

### Core Features

1. **Pydantic AI Agent** with Ollama backend
2. **MCP Client** for MSSQL MCP Server integration
3. **CLI Chat Interface** using Typer + Rich
4. **Streamlit Web UI** for user-friendly interaction
5. **Configuration Management** via dotenv and JSON configs
6. **Structured Logging** with structlog

## All Needed Context

### Documentation & References

- url: https://ai.pydantic.dev/mcp/client/
  why: Official Pydantic AI MCP client documentation - shows MCPServerStdio usage pattern

- url: https://devblogs.microsoft.com/azure-sql/introducing-mssql-mcp-server/
  why: MSSQL MCP Server introduction - lists available tools and configuration

- url: https://docs.ollama.com/capabilities/tool-calling
  why: Ollama tool calling documentation - shows supported models and API format

- url: https://docs.streamlit.io/develop/api-reference/chat
  why: Streamlit chat components for building the web UI

- url: https://github.com/Azure-Samples/SQL-AI-samples/tree/main/MssqlMcp
  why: MSSQL MCP Server source repository - reference implementation

### Technology Versions

```toml
# pyproject.toml dependencies
python = ">=3.11"
pydantic-ai = { version = ">=0.2.0", extras = ["mcp"] }
pydantic = ">=2.0.0"
streamlit = ">=1.30.0"
typer = ">=0.9.0"
rich = ">=13.0.0"
python-dotenv = ">=1.0.0"
structlog = ">=24.0.0"
httpx = ">=0.27.0"
pytest = ">=8.0.0"
pytest-asyncio = ">=0.23.0"
```

### Key Patterns to Follow

#### 1. Pydantic AI Agent with Ollama

```python
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel

# Ollama exposes OpenAI-compatible API
model = OpenAIModel(
    model_name="qwen2.5:7b-instruct",
    base_url="http://localhost:11434/v1",
    api_key="ollama"
)

agent = Agent(
    model=model,
    system_prompt="You are a helpful SQL data analyst...",
    toolsets=[mssql_server]
)
```

#### 2. MCP Server Configuration

```python
from pydantic_ai.mcp import MCPServerStdio

mssql_server = MCPServerStdio(
    command="node",
    args=[mcp_path],
    env={
        "SERVER_NAME": sql_host,
        "DATABASE_NAME": database,
        "TRUST_SERVER_CERTIFICATE": "true"
    },
    timeout=30
)
```

#### 3. Async Agent Execution

```python
async def run_agent_query(agent: Agent, message: str) -> str:
    async with agent:  # Manages MCP server lifecycle
        result = await agent.run(message)
        return result.output
```

#### 4. Streamlit Async Helper

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

### MSSQL MCP Server Tools

These tools will be available to the agent:

| Tool Name | Purpose | Example Prompt |
|-----------|---------|----------------|
| list_tables | Get all tables in DB | "What tables are in the database?" |
| describe_table | Get table schema | "What columns does the Users table have?" |
| read_data | Query table data | "Show me the top 10 orders" |
| insert_data | Add new records | "Add a new customer named John" |
| update_data | Modify records | "Update the status to 'shipped'" |
| create_table | Create new table | "Create a logs table" |
| drop_table | Delete table | "Remove the temp_data table" |
| create_index | Add index | "Create an index on email column" |

### Ollama Model Selection

For tool calling with high-VRAM GPUs, use larger models for better quality:

**RTX 5090 (32GB VRAM) - Recommended:**
1. **qwen2.5:32b-instruct** - Best quality + excellent tool calling
2. **llama3.3:70b-instruct-q4_K_M** - Near GPT-4 quality (partial CPU offload)
3. **deepseek-r1:32b** - Superior reasoning capabilities

**RTX 4090/3090 (24GB VRAM):**
1. **qwen2.5:14b-instruct** - Great balance of speed and quality
2. **llama3.1:8b-instruct** - Fast and reliable

**RTX 4080/3080 (16GB) or lower:**
1. **qwen2.5:7b-instruct** - Best tool calling at this size
2. **mistral:7b-instruct** - Lighter weight option

Verify model supports tools:
```bash
curl http://localhost:11434/api/show -d '{"name":"qwen2.5:32b-instruct"}' | jq '.template'
```

## Implementation Plan

### Phase 0: Docker SQL Server Setup

**Prerequisites:**
- Docker Desktop installed and running

**Files (already created in scaffold):**
- `docker/docker-compose.yml` - SQL Server 2022 container definition
- `docker/init/01-create-database.sql` - Database creation script
- `docker/init/02-create-schema.sql` - Tables, views, indexes
- `docker/init/03-seed-data.sql` - Sample research analytics data
- `docker/setup-database.bat` - Windows helper script

**Steps to execute:**
```bash
# Start SQL Server container
cd docker
docker compose up -d mssql

# Wait for healthy status, then run init scripts
docker compose --profile init up mssql-tools

# Or use the helper script on Windows:
.\setup-database.bat
```

**Sample Database: ResearchAnalytics**

The database includes:
- **Departments** (8 records) - AI, Data Science, ML, NLP, CV, Robotics, Security, Cloud
- **Researchers** (23 records) - Staff with titles, salaries, specializations
- **Projects** (14 records) - Active, completed, and planned research projects
- **Publications** (10 records) - Journal articles, conference papers, technical reports
- **Datasets** (10 records) - Training data, sensor data, medical images
- **Experiments** (11 records) - ML experiments with results and metrics
- **Funding** (12 records) - Grants from NSF, NIH, DARPA, industry partners
- **Equipment** (10 records) - GPU clusters, drones, medical workstations

**Example queries to test:**
- "What tables are in the database?"
- "Show me all active projects with their budgets"
- "Who are the top 5 researchers by publication count?"
- "What experiments are currently in progress?"
- "How much total funding has the ML department received?"

### Phase 1: Project Foundation

**Files to create:**
- `pyproject.toml` - Project configuration with all dependencies
- `requirements.txt` - Fallback pip requirements
- `.env.example` - Environment variable template
- `.gitignore` - Git ignore rules (secrets, venv, cache)
- `mcp_config.json` - MCP server configuration template
- `src/__init__.py` - Package init
- `src/utils/config.py` - Configuration loading
- `src/utils/logger.py` - Structured logging setup

### Phase 2: MCP Integration

**Files to create:**
- `src/mcp/__init__.py` - MCP package init
- `src/mcp/client.py` - MCP client wrapper with connection management
- `src/mcp/mssql_config.py` - MSSQL server config builder
- `src/mcp/server_manager.py` - Server lifecycle management

**Key implementation:**
```python
# src/mcp/client.py
from pydantic_ai.mcp import MCPServerStdio, load_mcp_servers
from pathlib import Path
import json

class MCPClientManager:
    def __init__(self, config_path: str = "mcp_config.json"):
        self.config_path = Path(config_path)
        self.servers = {}
    
    def load_config(self) -> dict:
        with open(self.config_path) as f:
            return json.load(f)
    
    def get_mssql_server(self) -> MCPServerStdio:
        config = self.load_config()
        mssql_config = config["mcpServers"]["mssql"]
        return MCPServerStdio(
            command=mssql_config["command"],
            args=mssql_config["args"],
            env=self._resolve_env(mssql_config["env"]),
            timeout=30
        )
```

### Phase 3: Agent Implementation

**Files to create:**
- `src/agent/__init__.py` - Agent package init
- `src/agent/research_agent.py` - Main agent implementation
- `src/agent/prompts.py` - System prompts
- `src/agent/tools.py` - Custom tool definitions (if needed)
- `src/models/chat.py` - Chat message models
- `src/models/sql_results.py` - SQL result models

**Key implementation:**
```python
# src/agent/research_agent.py
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel
from src.mcp.client import MCPClientManager
from src.agent.prompts import SYSTEM_PROMPT
from src.utils.config import settings

class ResearchAgent:
    def __init__(self):
        self.model = OpenAIModel(
            model_name=settings.ollama_model,
            base_url=f"{settings.ollama_host}/v1",
            api_key="ollama"
        )
        self.mcp_manager = MCPClientManager()
        self.mssql_server = self.mcp_manager.get_mssql_server()
        
        self.agent = Agent(
            model=self.model,
            system_prompt=SYSTEM_PROMPT,
            toolsets=[self.mssql_server]
        )
    
    async def chat(self, message: str, history: list = None) -> str:
        async with self.agent:
            result = await self.agent.run(message)
            return result.output
```

### Phase 4: CLI Interface

**Files to create:**
- `src/cli/__init__.py` - CLI package init
- `src/cli/chat.py` - CLI chat implementation

**Key implementation:**
```python
# src/cli/chat.py
import typer
import asyncio
from rich.console import Console
from rich.prompt import Prompt
from rich.panel import Panel
from src.agent.research_agent import ResearchAgent

app = typer.Typer()
console = Console()

@app.command()
def chat():
    """Start interactive chat with the research agent."""
    console.print(Panel.fit(
        "[bold green]Local LLM Research Agent[/]\n"
        "Type 'quit' to exit, 'clear' to reset conversation"
    ))
    
    agent = ResearchAgent()
    history = []
    
    while True:
        try:
            user_input = Prompt.ask("\n[bold blue]You[/]")
            
            if user_input.lower() in ("quit", "exit"):
                console.print("[yellow]Goodbye![/]")
                break
            
            if user_input.lower() == "clear":
                history = []
                console.print("[yellow]Conversation cleared.[/]")
                continue
            
            with console.status("[bold green]Thinking..."):
                response = asyncio.run(agent.chat(user_input, history))
            
            console.print(f"\n[bold green]Agent:[/] {response}")
            history.append({"user": user_input, "agent": response})
            
        except KeyboardInterrupt:
            console.print("\n[yellow]Interrupted. Goodbye![/]")
            break

if __name__ == "__main__":
    app()
```

### Phase 5: Streamlit UI

**Files to create:**
- `src/ui/__init__.py` - UI package init
- `src/ui/streamlit_app.py` - Streamlit application

**Key implementation:**
```python
# src/ui/streamlit_app.py
import streamlit as st
import asyncio
from src.agent.research_agent import ResearchAgent

st.set_page_config(
    page_title="Local LLM Research Agent",
    page_icon="🔍",
    layout="wide"
)

def run_async(coro):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()

@st.cache_resource
def get_agent():
    return ResearchAgent()

st.title("🔍 Local LLM Research Agent")
st.caption("Chat with your SQL Server data using natural language")

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("Ask about your data..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    with st.chat_message("assistant"):
        with st.spinner("Querying..."):
            agent = get_agent()
            response = run_async(agent.chat(prompt))
            st.markdown(response)
    
    st.session_state.messages.append({"role": "assistant", "content": response})
```

### Phase 6: Testing & Documentation

**Files to create:**
- `tests/__init__.py`
- `tests/test_agent.py`
- `tests/test_mcp_client.py`
- `tests/test_cli.py`
- `tests/conftest.py` - Pytest fixtures

**Files to update:**
- `README.md` - Complete documentation

## File-by-File Implementation Order

1. `pyproject.toml` - Dependencies first
2. `.env.example` - Configuration template
3. `.gitignore` - Security
4. `src/utils/config.py` - Config loading
5. `src/utils/logger.py` - Logging
6. `src/mcp/client.py` - MCP integration
7. `src/agent/prompts.py` - System prompts
8. `src/agent/research_agent.py` - Agent core
9. `src/cli/chat.py` - CLI interface
10. `src/ui/streamlit_app.py` - Web UI
11. `src/main.py` - Entry point
12. `mcp_config.json` - MCP config
13. Tests
14. `README.md` - Documentation

## Validation Checkpoints

After each phase, verify:

0. **Phase 0**: Docker SQL Server starts, `SELECT * FROM dbo.Researchers` returns data
1. **Phase 1**: `uv sync` succeeds, config loads correctly
2. **Phase 2**: MCP server starts, tools are listed
3. **Phase 3**: Agent responds to "hello" without errors
4. **Phase 4**: CLI chat works with simple prompts
5. **Phase 5**: Streamlit UI displays and responds
6. **Phase 6**: All tests pass

## Out of Scope (Future Enhancements)

- RAG/vector search integration
- Multi-database support
- User authentication
- Conversation persistence to database
- Fine-tuned model support
- Production deployment (Kubernetes, etc.)

## Notes for Implementation

1. **IMPORTANT**: Always use `async with agent:` to manage MCP server lifecycle
2. **IMPORTANT**: Verify Ollama is running before starting the application
3. **Proactively** check that the selected model supports tool calling
4. Handle MCP server startup failures gracefully with clear error messages
5. Use environment variable substitution in mcp_config.json for flexibility
