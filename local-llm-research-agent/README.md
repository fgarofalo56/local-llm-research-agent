# 🔍 Local LLM Research Analytics Tool

A **100% local** smart chat agent for SQL Server data analytics. Query your database using natural language with complete privacy - all inference runs locally via Ollama.

## Features

- 🏠 **Fully Local** - No cloud APIs, all processing on your machine
- 💬 **Natural Language SQL** - Ask questions about your data in plain English
- 🔧 **MCP Integration** - Extensible tool architecture via Model Context Protocol
- 🖥️ **Dual Interface** - CLI for development, Streamlit for production
- 🔒 **Privacy First** - Your data never leaves your network

## Quick Start

### Prerequisites

- Python 3.11+
- [Ollama](https://ollama.com/) installed and running
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (for sample database)
- Node.js 18+ (for MSSQL MCP Server)

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/local-llm-research-agent.git
cd local-llm-research-agent

# Install dependencies (using uv - recommended)
uv sync

# Or using pip
pip install -r requirements.txt

# Copy environment template
cp .env.example .env
# Edit .env with your configuration
```

### Option A: Use Docker SQL Server (Recommended for Demo)

```bash
# Start SQL Server with sample ResearchAnalytics database
cd docker
docker compose up -d mssql

# Wait for SQL Server to be healthy (about 30 seconds)
# Then initialize the database with sample data
docker compose --profile init up mssql-tools

# On Windows, you can use the helper script:
.\setup-database.bat
```

The sample database includes:
- 23 researchers across 8 departments
- 14 research projects (AI, ML, NLP, Robotics, etc.)
- Publications, datasets, experiments, and funding data

### Option B: Use Your Own SQL Server

Edit `.env` with your SQL Server connection details.

### Pull the Ollama Model

Choose based on your GPU VRAM:

```bash
# RTX 5090 (32GB) - Best quality
ollama pull qwen2.5:32b-instruct

# RTX 4090/3090 (24GB) - Great balance
ollama pull qwen2.5:14b-instruct

# RTX 4080/3080 or lower (16GB or less)
ollama pull qwen2.5:7b-instruct
```

### Setup MSSQL MCP Server

```bash
# Clone MSSQL MCP Server
git clone https://github.com/Azure-Samples/SQL-AI-samples.git
cd SQL-AI-samples/MssqlMcp/Node
npm install

# Note the path to dist/index.js for configuration
```

### Configuration

Edit `.env` with your settings:

```bash
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=qwen2.5:7b-instruct

SQL_SERVER_HOST=localhost
SQL_DATABASE_NAME=your_database
SQL_TRUST_SERVER_CERTIFICATE=true
```

Update `mcp_config.json` with the path to your MSSQL MCP Server.

### Run

```bash
# CLI Chat
uv run python -m src.cli.chat

# Streamlit Web UI
uv run streamlit run src/ui/streamlit_app.py
```

## Usage Examples

```
You: What tables are in the database?
Agent: The database contains 8 tables: Departments, Researchers, Projects, 
       Publications, Datasets, Experiments, Funding, and Equipment.

You: Show me all active projects with their budgets
Agent: Here are the active projects:
       - LLM Fine-tuning Platform: $450,000 budget
       - Autonomous Drone Navigation: $680,000 budget
       - Predictive Maintenance ML Pipeline: $320,000 budget
       ...

You: Who are the top 5 researchers by publication count?
Agent: Based on citations, the top researchers are:
       1. Kevin Anderson - 156 citations (Medical Imaging Survey)
       2. Amanda Foster - 89 citations (Federated Learning)
       ...

You: How much total funding has the ML department received?
Agent: The Machine Learning department has received $830,000 in approved 
       funding across 3 grants.
```

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        User Interfaces                       │
│  ┌─────────────────┐              ┌─────────────────────┐   │
│  │   CLI (Typer)   │              │  Streamlit Web UI   │   │
│  └────────┬────────┘              └──────────┬──────────┘   │
└───────────┼──────────────────────────────────┼──────────────┘
            │                                  │
            ▼                                  ▼
┌─────────────────────────────────────────────────────────────┐
│                     Pydantic AI Agent                        │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  System Prompt + Tool Orchestration + Conversation  │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────┬───────────────────────────────────┘
                          │
            ┌─────────────┴─────────────┐
            ▼                           ▼
┌───────────────────┐       ┌─────────────────────────────────┐
│      Ollama       │       │         MCP Servers             │
│  (Local LLM)      │       │  ┌─────────────────────────┐   │
│                   │       │  │    MSSQL MCP Server     │   │
│ qwen2.5/llama3.1  │       │  │  (SQL Server Access)    │   │
└───────────────────┘       │  └────────────┬────────────┘   │
                            │               │                 │
                            │               ▼                 │
                            │  ┌─────────────────────────┐   │
                            │  │      SQL Server         │   │
                            │  │  (Your Local Database)  │   │
                            │  └─────────────────────────┘   │
                            └─────────────────────────────────┘
```

## Tech Stack

| Component | Technology |
|-----------|------------|
| LLM Runtime | Ollama |
| Agent Framework | Pydantic AI |
| MCP Server | MSSQL MCP (Node.js) |
| Web UI | Streamlit |
| CLI | Typer + Rich |
| Validation | Pydantic v2 |

## Project Structure

```
local-llm-research-agent/
├── docker/             # Docker SQL Server setup
│   ├── docker-compose.yml
│   ├── setup-database.bat
│   └── init/           # Database initialization scripts
├── src/
│   ├── agent/          # Pydantic AI agent implementation
│   ├── mcp/            # MCP client and server configuration
│   ├── cli/            # Command-line interface
│   ├── ui/             # Streamlit web interface
│   ├── models/         # Pydantic data models
│   └── utils/          # Configuration and logging
├── tests/              # Test suite
├── PRPs/               # Product Requirement Prompts
├── ai_docs/            # AI documentation context
└── examples/           # Usage examples
```

## Development

```bash
# Run tests
uv run pytest tests/ -v

# Format code
uv run ruff format .

# Lint
uv run ruff check .
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests
5. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Acknowledgments

- [Pydantic AI](https://ai.pydantic.dev/) - Agent framework
- [Ollama](https://ollama.com/) - Local LLM runtime
- [MSSQL MCP Server](https://github.com/Azure-Samples/SQL-AI-samples/tree/main/MssqlMcp) - SQL Server MCP integration
- [Model Context Protocol](https://modelcontextprotocol.io/) - Tool integration standard
