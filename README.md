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
- Node.js 18+ (for MSSQL MCP Server)
- SQL Server (local or accessible instance)

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

### Pull the Ollama Model

```bash
# Recommended model for tool calling
ollama pull qwen2.5:7b-instruct

# Or alternative
ollama pull llama3.1:8b
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
Agent: I found 5 tables: Users, Orders, Products, Categories, and OrderItems.

You: Show me the top 5 customers by order count
Agent: Here are the top 5 customers...

You: What's the schema of the Orders table?
Agent: The Orders table has the following columns: OrderID (int), CustomerID (int)...
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
