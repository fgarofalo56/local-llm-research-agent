# Configuration Reference

Complete reference for all configuration options in the Local LLM Research Agent.

## Environment Variables

All configuration is done through environment variables. Create a `.env` file in the project root by copying `.env.example`:

```bash
cp .env.example .env
```

---

## LLM Provider Configuration

### Provider Selection

| Variable | Default | Description |
|----------|---------|-------------|
| `LLM_PROVIDER` | `ollama` | LLM provider to use: `ollama` or `foundry_local` |

### Ollama Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `OLLAMA_HOST` | `http://localhost:11434` | Ollama server URL |
| `OLLAMA_MODEL` | `qwen2.5:7b-instruct` | Model for inference |

**Recommended Models:**
- `qwen2.5:7b-instruct` - Best balance of capability and speed
- `llama3.1:8b` - Strong general performance
- `mistral:7b-instruct` - Lightweight option

**Example:**
```bash
LLM_PROVIDER=ollama
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=qwen2.5:7b-instruct
```

### Foundry Local Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `FOUNDRY_ENDPOINT` | `http://127.0.0.1:53760` | Foundry Local API endpoint |
| `FOUNDRY_MODEL` | `phi-4` | Model alias to use |
| `FOUNDRY_AUTO_START` | `false` | Auto-start model on agent init |

**Available Models:**
- `phi-4` - Microsoft Phi-4 (default)
- `qwen2.5-0.5b` - Lightweight option
- `mistral-7b` - General purpose

**Example:**
```bash
LLM_PROVIDER=foundry_local
FOUNDRY_ENDPOINT=http://127.0.0.1:53760
FOUNDRY_MODEL=phi-4
FOUNDRY_AUTO_START=true
```

---

## SQL Server Configuration

### Connection Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `SQL_SERVER_HOST` | `localhost` | SQL Server hostname or IP |
| `SQL_SERVER_PORT` | `1433` | SQL Server port |
| `SQL_DATABASE_NAME` | `master` | Database name to connect to |
| `SQL_TRUST_SERVER_CERTIFICATE` | `true` | Trust self-signed certificates |

### Authentication

| Variable | Default | Description |
|----------|---------|-------------|
| `SQL_USERNAME` | (empty) | SQL Server username (blank for Windows Auth) |
| `SQL_PASSWORD` | (empty) | SQL Server password |

**Windows Authentication:**
```bash
SQL_SERVER_HOST=localhost
SQL_DATABASE_NAME=ResearchAnalytics
SQL_USERNAME=
SQL_PASSWORD=
```

**SQL Server Authentication:**
```bash
SQL_SERVER_HOST=localhost
SQL_DATABASE_NAME=ResearchAnalytics
SQL_USERNAME=sa
SQL_PASSWORD=YourPassword123!
```

**Docker SQL Server:**
```bash
SQL_SERVER_HOST=localhost
SQL_DATABASE_NAME=ResearchAnalytics
SQL_USERNAME=sa
SQL_PASSWORD=LocalLLM@2024!
```

---

## MCP Server Configuration

### MSSQL MCP Server

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_MSSQL_PATH` | (empty) | Path to MSSQL MCP Server `index.js` |
| `MCP_MSSQL_READONLY` | `false` | Enable read-only mode (safer for exploration) |
| `MCP_DEBUG` | `false` | Enable MCP server debug logging |

**Finding MCP_MSSQL_PATH:**

After cloning and building the MSSQL MCP Server:
```bash
# Clone
git clone https://github.com/Azure-Samples/SQL-AI-samples.git
cd SQL-AI-samples/MssqlMcp/Node
npm install

# Path will be:
# Windows: C:\path\to\SQL-AI-samples\MssqlMcp\Node\dist\index.js
# Linux/Mac: /path/to/SQL-AI-samples/MssqlMcp/Node/dist/index.js
```

**Example:**
```bash
# Windows
MCP_MSSQL_PATH=C:\Projects\SQL-AI-samples\MssqlMcp\Node\dist\index.js

# Linux/Mac
MCP_MSSQL_PATH=/home/user/SQL-AI-samples/MssqlMcp/Node/dist/index.js

# Read-only mode (recommended for exploration)
MCP_MSSQL_READONLY=true
```

---

## Application Settings

### General

| Variable | Default | Description |
|----------|---------|-------------|
| `LOG_LEVEL` | `INFO` | Logging level: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL` |
| `DEBUG` | `false` | Enable debug mode (verbose output) |
| `STREAMLIT_PORT` | `8501` | Streamlit web UI port |

### Response Caching

| Variable | Default | Description |
|----------|---------|-------------|
| `CACHE_ENABLED` | `true` | Enable response caching |
| `CACHE_MAX_SIZE` | `100` | Maximum cached responses |
| `CACHE_TTL_SECONDS` | `3600` | Cache TTL in seconds (0 = no expiration) |

**Example:**
```bash
# Enable caching with 2-hour TTL
CACHE_ENABLED=true
CACHE_MAX_SIZE=200
CACHE_TTL_SECONDS=7200

# Disable caching
CACHE_ENABLED=false
```

---

## Docker Configuration

### Docker SQL Server

| Variable | Default | Description |
|----------|---------|-------------|
| `MSSQL_SA_PASSWORD` | `LocalLLM@2024!` | SA password for Docker SQL Server |

### Docker Agent

When running the agent in Docker, these additional settings apply:

| Variable | Default | Description |
|----------|---------|-------------|
| `OLLAMA_HOST` | `http://host.docker.internal:11434` | Host's Ollama instance |
| `SQL_SERVER_HOST` | `mssql` | Docker network hostname |

---

## CLI Configuration

### Command-Line Flags

The CLI supports these runtime flags:

| Flag | Description |
|------|-------------|
| `--provider`, `-p` | Override LLM provider |
| `--model`, `-m` | Override model name |
| `--readonly` | Force read-only mode |
| `--no-cache` | Disable response caching |
| `--stream` | Enable streaming output |
| `--verbose`, `-v` | Enable verbose logging |

**Examples:**
```bash
# Use Foundry Local with streaming
llm-chat --provider foundry_local --stream

# Single query without cache
llm-chat query "What tables exist?" --no-cache

# Read-only mode
llm-chat --readonly
```

---

## Programmatic Configuration

### Using Settings in Code

```python
from src.utils.config import settings

# Access settings
print(f"Provider: {settings.llm_provider}")
print(f"Model: {settings.ollama_model}")
print(f"Database: {settings.sql_database_name}")

# Get MCP environment
mcp_env = settings.get_mcp_env()
```

### Creating Custom Agents

```python
from src.agent.research_agent import create_research_agent

# Use defaults from .env
agent = create_research_agent()

# Override at runtime
agent = create_research_agent(
    provider_type="foundry_local",
    model_name="phi-4",
    readonly=True,
    cache_enabled=False
)
```

---

## Configuration Precedence

Configuration is loaded in this order (later overrides earlier):

1. **Default values** - Hardcoded in `Settings` class
2. **`.env` file** - Project root environment file
3. **Environment variables** - System environment
4. **CLI flags** - Runtime command-line arguments
5. **Programmatic** - Code-level overrides

---

## Validation

### Model Compatibility

The agent validates that the configured model supports tool calling. Compatible models include:

- `qwen2.5*`
- `llama3.1*`, `llama3.2*`
- `mistral*`, `mixtral*`
- `command-r*`
- `firefunction*`

### Connection Testing

Test your configuration:

```bash
# Test Ollama
curl http://localhost:11434/api/tags

# Test SQL Server (from CLI)
llm-chat query "What tables are available?"

# Test with verbose output
llm-chat --verbose query "SELECT 1"
```

---

## Troubleshooting

### Common Issues

**Ollama not found:**
```bash
# Check Ollama is running
curl http://localhost:11434/api/tags

# Pull required model
ollama pull qwen2.5:7b-instruct
```

**MCP Server not found:**
```bash
# Verify path exists
ls /path/to/SQL-AI-samples/MssqlMcp/Node/dist/index.js

# Test MCP server directly
node /path/to/SQL-AI-samples/MssqlMcp/Node/dist/index.js
```

**SQL Server connection:**
```bash
# Test with sqlcmd
sqlcmd -S localhost,1433 -U sa -P "YourPassword" -Q "SELECT 1"
```

### Debug Mode

Enable debug logging for troubleshooting:

```bash
LOG_LEVEL=DEBUG
DEBUG=true
MCP_DEBUG=true
```

---

## Example Configurations

### Development (Local)

```bash
# .env for local development
LLM_PROVIDER=ollama
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=qwen2.5:7b-instruct

SQL_SERVER_HOST=localhost
SQL_DATABASE_NAME=ResearchAnalytics
SQL_USERNAME=sa
SQL_PASSWORD=LocalLLM@2024!

MCP_MSSQL_PATH=C:\Projects\SQL-AI-samples\MssqlMcp\Node\dist\index.js
MCP_MSSQL_READONLY=false

LOG_LEVEL=INFO
CACHE_ENABLED=true
```

### Production (Read-Only)

```bash
# .env for production with safety measures
LLM_PROVIDER=ollama
OLLAMA_HOST=http://ollama-server:11434
OLLAMA_MODEL=qwen2.5:7b-instruct

SQL_SERVER_HOST=prod-sql-server
SQL_DATABASE_NAME=Analytics
SQL_USERNAME=readonly_user
SQL_PASSWORD=${DB_PASSWORD}  # Use secret management

MCP_MSSQL_PATH=/opt/mssql-mcp/dist/index.js
MCP_MSSQL_READONLY=true  # IMPORTANT: Read-only for safety

LOG_LEVEL=WARNING
CACHE_ENABLED=true
CACHE_TTL_SECONDS=7200
```

### Docker Compose

```bash
# .env for docker compose setup
LLM_PROVIDER=ollama
OLLAMA_HOST=http://host.docker.internal:11434
OLLAMA_MODEL=qwen2.5:7b-instruct

SQL_DATABASE_NAME=ResearchAnalytics
MSSQL_SA_PASSWORD=LocalLLM@2024!

STREAMLIT_PORT=8501
MCP_MSSQL_READONLY=false
CACHE_ENABLED=true
```
