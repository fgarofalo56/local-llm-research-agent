# Local LLM Research Analytics Tool

A **100% local** smart chat agent for SQL Server data analytics. Query your database using natural language with complete privacy - all inference runs locally via Ollama.

## Features

- **Fully Local** - No cloud APIs, all processing on your machine
- **Natural Language SQL** - Ask questions about your data in plain English
- **MCP Integration** - Extensible tool architecture via Model Context Protocol
- **Dual Interface** - CLI for development, Streamlit for production
- **Privacy First** - Your data never leaves your network
- **Sample Database** - Docker-based SQL Server with research analytics demo data

## Table of Contents

- [Quick Start](#quick-start)
- [Docker Setup (SQL Server with Sample Data)](#docker-setup-sql-server-with-sample-data)
- [MSSQL MCP Server Setup](#mssql-mcp-server-setup)
- [Configuration](#configuration)
- [Running the Agent](#running-the-agent)
- [Testing the Agent](#testing-the-agent)
- [MCP Tools Reference](#mcp-tools-reference)
- [Architecture](#architecture)
- [Development](#development)
- [Contributing](#contributing)
- [License](#license)

## Quick Start

### Prerequisites

- Python 3.11+
- [Ollama](https://ollama.com/) installed and running
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (for SQL Server)
- Node.js 18+ (for MSSQL MCP Server)
- Git

### Installation

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

### Pull the Ollama Model

```bash
# Recommended model for tool calling
ollama pull qwen2.5:7b-instruct

# Alternative models
ollama pull llama3.1:8b
ollama pull mistral:7b-instruct
```

---

## Docker Setup (SQL Server with Sample Data)

The project includes a complete Docker setup with SQL Server 2022 and a pre-populated research analytics database for testing.

### Database Overview

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

### Starting the Database

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

# Wait for SQL Server to be healthy (check status)
docker compose ps

# Run initialization scripts (creates database and sample data)
docker compose --profile init up mssql-tools

# The mssql-tools container will exit after initialization
```

### Connection Details

| Setting | Value |
|---------|-------|
| **Server** | `localhost,1433` |
| **Database** | `ResearchAnalytics` |
| **Username** | `sa` |
| **Password** | `LocalLLM@2024!` (or your `MSSQL_SA_PASSWORD`) |

### Testing the Database Connection

```bash
# Using sqlcmd (if installed)
sqlcmd -S localhost,1433 -U sa -P "LocalLLM@2024!" -d ResearchAnalytics -Q "SELECT COUNT(*) FROM Researchers"

# Using Docker exec
docker exec -it local-llm-mssql /opt/mssql-tools18/bin/sqlcmd \
  -S localhost -U sa -P "LocalLLM@2024!" -No \
  -Q "SELECT COUNT(*) AS ResearcherCount FROM ResearchAnalytics.dbo.Researchers"
```

### Managing the Database

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

### Customizing the Password

Set a custom password via environment variable:

```bash
# Windows
set MSSQL_SA_PASSWORD=YourSecurePassword123!
docker compose up -d

# Linux/Mac
export MSSQL_SA_PASSWORD=YourSecurePassword123!
docker compose up -d
```

Or add to your `.env` file:
```bash
MSSQL_SA_PASSWORD=YourSecurePassword123!
```

---

## MSSQL MCP Server Setup

The MSSQL MCP Server provides the tools for the agent to interact with SQL Server.

### Installation

```bash
# Clone the MSSQL MCP Server repository
git clone https://github.com/Azure-Samples/SQL-AI-samples.git

# Navigate to Node.js implementation
cd SQL-AI-samples/MssqlMcp/Node

# Install dependencies
npm install

# Note the full path to dist/index.js - you'll need this!
# Example: C:\Projects\SQL-AI-samples\MssqlMcp\Node\dist\index.js
```

### Configure the Path

Update your `.env` file with the MCP server path:

```bash
# Windows example
MCP_MSSQL_PATH=C:\Projects\SQL-AI-samples\MssqlMcp\Node\dist\index.js

# Linux/Mac example
MCP_MSSQL_PATH=/home/user/SQL-AI-samples/MssqlMcp/Node/dist/index.js
```

---

## Configuration

### Environment Variables (.env)

Create your `.env` file from the template:

```bash
cp .env.example .env
```

Configure for the Docker database:

```bash
# Ollama Configuration
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=qwen2.5:7b-instruct

# SQL Server Configuration (Docker defaults)
SQL_SERVER_HOST=localhost
SQL_SERVER_PORT=1433
SQL_DATABASE_NAME=ResearchAnalytics
SQL_TRUST_SERVER_CERTIFICATE=true

# SQL Server Authentication
SQL_USERNAME=sa
SQL_PASSWORD=LocalLLM@2024!

# MSSQL MCP Server Path (UPDATE THIS!)
MCP_MSSQL_PATH=/path/to/SQL-AI-samples/MssqlMcp/Node/dist/index.js

# Optional: Read-only mode for safety
MCP_MSSQL_READONLY=false

# Logging
LOG_LEVEL=INFO
```

---

## Running the Agent

### CLI Interface

```bash
# Start the CLI chat
uv run python -m src.cli.chat

# With read-only mode (safer for exploration)
uv run python -m src.cli.chat --readonly

# With debug output
uv run python -m src.cli.chat --debug
```

### Streamlit Web UI

```bash
# Start the web interface
uv run streamlit run src/ui/streamlit_app.py

# Access at: http://localhost:8501
```

---

## Testing the Agent

### Sample Queries to Try

Once the agent is running with the Docker database, try these queries:

#### Schema Discovery
```
What tables are in the database?
Describe the Researchers table
Show me the schema for Projects
What views are available?
```

#### Basic Queries
```
How many researchers are there?
List all departments and their budgets
Show me the top 5 highest paid researchers
What are the active projects?
```

#### Analytical Queries
```
Which department has the most researchers?
What's the total budget across all projects?
Show me researchers in the AI department
List projects that are over budget
Who are the project leads?
```

#### Relationship Queries
```
How many publications does each researcher have?
What funding sources support the LLM project?
Show me experiments for the Drone Navigation project
Which researchers are assigned to multiple projects?
```

#### Advanced Queries
```
What's the average salary by department?
Show me the most cited publications
List datasets larger than 100GB
Which experiments have completed successfully?
Compare approved vs pending funding by project
```

### Expected Behavior

1. **Agent lists tables** when you ask about database structure
2. **Agent describes schemas** before querying data
3. **Agent shows results** in a readable format
4. **Agent explains its actions** as it works

### Troubleshooting

#### "Connection refused" or timeout errors
```bash
# Check SQL Server is running
docker compose ps

# Check logs for errors
docker compose logs mssql
```

#### "Database does not exist"
```bash
# Re-run initialization
docker compose --profile init up mssql-tools
```

#### "Ollama connection failed"
```bash
# Check Ollama is running
curl http://localhost:11434/api/tags

# Pull the model if missing
ollama pull qwen2.5:7b-instruct
```

#### "MCP server not found"
- Verify `MCP_MSSQL_PATH` in `.env` points to valid `dist/index.js`
- Ensure you ran `npm install` in the MCP server directory

---

## MCP Tools Reference

The MSSQL MCP Server provides these tools:

| Tool | Description | Example Use |
|------|-------------|-------------|
| `list_tables` | Lists all tables | "What tables exist?" |
| `describe_table` | Get table schema | "Describe the Researchers table" |
| `read_data` | Query data | "Show top 10 researchers" |
| `insert_data` | Insert rows | "Add a new researcher" |
| `update_data` | Modify data | "Update project status" |
| `create_table` | Create tables | "Create an audit log table" |
| `drop_table` | Delete tables | "Remove temp table" |
| `create_index` | Add indexes | "Index the email column" |

> **Note**: Use `MCP_MSSQL_READONLY=true` to disable write operations.

---

## Architecture

```
+-------------------------------------------------------------+
|                      User Interfaces                         |
|  +------------------+              +----------------------+  |
|  |   CLI (Typer)    |              |  Streamlit Web UI    |  |
|  +--------+---------+              +-----------+----------+  |
+-----------|------------------------------------|-------------+
            |                                    |
            v                                    v
+-------------------------------------------------------------+
|                     Pydantic AI Agent                       |
|  +-------------------------------------------------------+  |
|  |  System Prompt + Tool Orchestration + Conversation    |  |
|  +-------------------------------------------------------+  |
+----------------------------+--------------------------------+
                             |
            +----------------+----------------+
            v                                 v
+--------------------+       +----------------------------------+
|      Ollama        |       |          MCP Servers            |
|   (Local LLM)      |       |  +----------------------------+ |
|                    |       |  |    MSSQL MCP Server        | |
| qwen2.5/llama3.1   |       |  |   (SQL Server Access)      | |
+--------------------+       |  +-------------+--------------+ |
                             |                |                |
                             |                v                |
                             |  +----------------------------+ |
                             |  |       SQL Server           | |
                             |  |   (Docker Container)       | |
                             |  |   ResearchAnalytics DB     | |
                             |  +----------------------------+ |
                             +----------------------------------+
```

## Tech Stack

| Component | Technology |
|-----------|------------|
| LLM Runtime | Ollama |
| Agent Framework | Pydantic AI |
| MCP Server | MSSQL MCP (Node.js) |
| Web UI | Streamlit |
| CLI | Typer + Rich |
| Database | SQL Server 2022 (Docker) |
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
├── docker/
│   ├── docker-compose.yml    # SQL Server container
│   ├── init/                 # Database init scripts
│   │   ├── 01-create-database.sql
│   │   ├── 02-create-schema.sql
│   │   └── 03-seed-data.sql
│   └── setup-database.bat    # Windows setup helper
├── tests/              # Test suite
├── ai_docs/            # AI documentation context
├── examples/           # Usage examples
├── .github/            # GitHub templates and guides
├── CLAUDE.md           # AI assistant context
├── CONTRIBUTING.md     # Contribution guidelines
├── SECURITY.md         # Security policy
└── LICENSE             # MIT License
```

---

## Development

### Running Tests

```bash
# Run all tests
uv run pytest tests/ -v

# Run with coverage
uv run pytest tests/ --cov=src --cov-report=html

# Run specific test file
uv run pytest tests/test_agent.py -v
```

### Code Quality

```bash
# Lint code
uv run ruff check .

# Auto-fix lint issues
uv run ruff check --fix .

# Format code
uv run ruff format .
```

---

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

**Important**: All external contributions must be submitted via Pull Request. Direct pushes to `main` are restricted.

### Quick Contribution Steps

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests (`uv run pytest tests/ -v`)
5. Submit a Pull Request

---

## Security

Please see [SECURITY.md](SECURITY.md) for:
- How to report vulnerabilities
- Security best practices
- Known security considerations

**Never commit credentials or `.env` files!**

---

## License

MIT License - see [LICENSE](LICENSE) file for details.

---

## Acknowledgments

- [Pydantic AI](https://ai.pydantic.dev/) - Agent framework
- [Ollama](https://ollama.com/) - Local LLM runtime
- [MSSQL MCP Server](https://github.com/Azure-Samples/SQL-AI-samples/tree/main/MssqlMcp) - SQL Server MCP integration
- [Model Context Protocol](https://modelcontextprotocol.io/) - Tool integration standard
