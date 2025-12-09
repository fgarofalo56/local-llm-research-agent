# 🔍 Local LLM Research Analytics Tool

> **A 100% local smart chat agent for SQL Server data analytics. Query your database using natural language with complete privacy - all inference runs locally via Ollama or Microsoft Foundry Local.**

---

## ✨ Features

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

---

## 📑 Table of Contents

- [Quick Start](#-quick-start)
- [Docker Setup](#-docker-setup-sql-server-with-sample-data)
- [MSSQL MCP Server Setup](#-mssql-mcp-server-setup)
- [Configuration](#️-configuration)
- [Running the Agent](#-running-the-agent)
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

## 🐳 Docker Setup (SQL Server with Sample Data)

The project includes a complete Docker setup with SQL Server 2022 and a pre-populated research analytics database.

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

### 🚀 Starting the Database

#### Option 1: Quick Setup (Windows)

```bash
cd docker
setup-database.bat
```

#### Option 2: Manual Setup (All Platforms)

```bash
cd docker

# Start SQL Server container
docker compose up -d mssql

# Wait for SQL Server to be healthy
docker compose ps

# Run initialization scripts
docker compose --profile init up mssql-tools
```

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

# Using Docker exec
docker exec -it local-llm-mssql /opt/mssql-tools18/bin/sqlcmd \
  -S localhost -U sa -P "LocalLLM@2024!" -No \
  -Q "SELECT COUNT(*) AS ResearcherCount FROM ResearchAnalytics.dbo.Researchers"
```

### 📋 Managing the Database

```bash
# View container logs
docker compose logs -f mssql

# Stop the database (preserves data)
docker compose down

# Stop and DELETE all data (fresh start)
docker compose down -v

# Restart with fresh data
docker compose down -v
docker compose up -d mssql
docker compose --profile init up mssql-tools
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

# Microsoft Foundry Local Configuration (alternative)
FOUNDRY_ENDPOINT=http://127.0.0.1:55588
FOUNDRY_MODEL=phi-4
FOUNDRY_AUTO_START=false

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
# MCP Configuration
# =============================================================================
MCP_MSSQL_PATH=/path/to/SQL-AI-samples/MssqlMcp/Node/dist/index.js
MCP_MSSQL_READONLY=false

# =============================================================================
# Application Settings
# =============================================================================
LOG_LEVEL=INFO
```

### 🦙 LLM Provider Options

| Provider | Recommended Models | Notes |
|----------|-------------------|-------|
| **Ollama** | `qwen2.5:7b-instruct`, `llama3.1:8b` | Requires Ollama running |
| **Foundry Local** | `phi-4`, `phi-3-mini` | Microsoft's local runtime |

---

## 🚀 Running the Agent

### ⌨️ CLI Interface

```bash
# Start the CLI chat
uv run python -m src.cli.chat

# With streaming responses
uv run python -m src.cli.chat --stream

# Use Foundry Local instead of Ollama
uv run python -m src.cli.chat --provider foundry_local

# With read-only mode (safer for exploration)
uv run python -m src.cli.chat --readonly

# With debug output
uv run python -m src.cli.chat --debug
```

### 🌐 Streamlit Web UI

```bash
# Start the web interface
uv run streamlit run src/ui/streamlit_app.py

# Access at: http://localhost:8501
```

> 💡 **Tip**: The web UI includes a provider selector in the sidebar to switch between Ollama and Foundry Local.

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
+-------------------------------------------------------------+
|                      User Interfaces                         |
|  +------------------+              +----------------------+  |
|  |  ⌨️ CLI (Typer)  |              |  🌐 Streamlit Web UI |  |
|  +--------+---------+              +-----------+----------+  |
+-----------|------------------------------------|-------------+
            |                                    |
            v                                    v
+-------------------------------------------------------------+
|                    🤖 Pydantic AI Agent                      |
|  +-------------------------------------------------------+  |
|  |  System Prompt + Tool Orchestration + Conversation    |  |
|  +-------------------------------------------------------+  |
+----------------------------+--------------------------------+
                             |
            +----------------+----------------+
            v                                 v
+--------------------+       +----------------------------------+
|  🦙 LLM Provider   |       |         🔌 MCP Servers           |
|  +--------------+  |       |  +----------------------------+ |
|  | Ollama       |  |       |  |    MSSQL MCP Server        | |
|  | Foundry Local|  |       |  |   (SQL Server Access)      | |
|  +--------------+  |       |  +-------------+--------------+ |
+--------------------+       |                |                |
                             |                v                |
                             |  +----------------------------+ |
                             |  |   🗃️ SQL Server           | |
                             |  |   (Docker Container)       | |
                             |  |   ResearchAnalytics DB     | |
                             |  +----------------------------+ |
                             +----------------------------------+
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

### 📁 Project Structure

```
local-llm-research-agent/
├── src/
│   ├── agent/          # 🤖 Pydantic AI agent
│   ├── providers/      # 🦙 LLM provider abstraction
│   ├── mcp/            # 🔌 MCP client and config
│   ├── cli/            # ⌨️ Command-line interface
│   ├── ui/             # 🌐 Streamlit web interface
│   ├── models/         # 📋 Pydantic data models
│   └── utils/          # ⚙️ Configuration and logging
├── docker/
│   ├── docker-compose.yml    # 🐳 SQL Server container
│   └── init/                 # 🗃️ Database init scripts
├── tests/              # 🧪 Test suite
├── docs/               # 📚 Documentation
├── examples/           # 💡 Usage examples
└── .github/            # 🔧 CI/CD workflows
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

*Last Updated: December 2024*
