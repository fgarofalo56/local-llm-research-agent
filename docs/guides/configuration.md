# ⚙️ Configuration Reference

> **Complete configuration guide for all Local LLM Research Agent settings**

---

## 📑 Table of Contents

- [Overview](#-overview)
- [Environment Variables](#-environment-variables)
- [MCP Configuration](#-mcp-configuration)
- [Ollama Settings](#-ollama-settings)
- [Database Configuration](#-database-configuration)
- [Security Configuration](#-security-configuration)
- [Advanced Options](#-advanced-options)

---

## 🎯 Overview

The Local LLM Research Agent uses a layered configuration system:

| Priority | Source | Description |
|----------|--------|-------------|
| 1 (Highest) | CLI Arguments | Runtime flags override all |
| 2 | Environment Variables | `.env` file settings |
| 3 | Config Files | `mcp_config.json` |
| 4 (Lowest) | Defaults | Built-in defaults |

---

## 🌍 Environment Variables

### Core Settings

Create a `.env` file in the project root:

```bash
cp .env.example .env
```

### Ollama Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `OLLAMA_HOST` | `http://localhost:11434` | Ollama server URL |
| `OLLAMA_MODEL` | `qwen2.5:7b-instruct` | LLM model to use |
| `OLLAMA_TIMEOUT` | `120` | Request timeout (seconds) |

```bash
# .env
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=qwen2.5:7b-instruct
OLLAMA_TIMEOUT=120
```

### SQL Server Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `SQL_SERVER_HOST` | `localhost` | SQL Server hostname |
| `SQL_SERVER_PORT` | `1433` | SQL Server port |
| `SQL_DATABASE_NAME` | `ResearchAnalytics` | Target database |
| `SQL_TRUST_SERVER_CERTIFICATE` | `true` | Trust self-signed certs |
| `SQL_USERNAME` | - | SQL authentication username |
| `SQL_PASSWORD` | - | SQL authentication password |

```bash
# .env - SQL Server (Docker defaults)
SQL_SERVER_HOST=localhost
SQL_SERVER_PORT=1433
SQL_DATABASE_NAME=ResearchAnalytics
SQL_TRUST_SERVER_CERTIFICATE=true
SQL_USERNAME=sa
SQL_PASSWORD=LocalLLM@2024!
```

> ⚠️ **Security:** Never commit `.env` files with real passwords!

### MCP Server Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_MSSQL_PATH` | - | Path to MSSQL MCP server |
| `MCP_MSSQL_READONLY` | `false` | Enable read-only mode |
| `MCP_TIMEOUT` | `30` | MCP operation timeout |

```bash
# .env - MCP paths
# Windows
MCP_MSSQL_PATH=C:\Projects\SQL-AI-samples\MssqlMcp\Node\dist\index.js

# Linux/Mac
MCP_MSSQL_PATH=/home/user/SQL-AI-samples/MssqlMcp/Node/dist/index.js

# Optional: Read-only mode (safer for exploration)
MCP_MSSQL_READONLY=true
```

### Application Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `LOG_LEVEL` | `INFO` | Logging verbosity |
| `STREAMLIT_PORT` | `8501` | Web UI port |
| `DEBUG` | `false` | Enable debug mode |

```bash
# .env - Application
LOG_LEVEL=INFO
STREAMLIT_PORT=8501
DEBUG=false
```

---

## 🔌 MCP Configuration

### Configuration File

The `mcp_config.json` file defines MCP server connections:

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

### Environment Variable Expansion

Variables in `mcp_config.json` are expanded from the environment:

| Syntax | Example | Description |
|--------|---------|-------------|
| `${VAR}` | `${SQL_SERVER_HOST}` | Required variable |
| `${VAR:-default}` | `${PORT:-1433}` | With default value |

### Adding Additional MCP Servers

To add more MCP servers, extend the config:

```json
{
  "mcpServers": {
    "mssql": { ... },
    "filesystem": {
      "command": "node",
      "args": ["/path/to/filesystem-mcp/dist/index.js"],
      "env": {
        "ALLOWED_PATHS": "/data,/reports"
      }
    }
  }
}
```

---

## 🦙 Ollama Settings

### Recommended Models

| Model | Size | VRAM | Best For |
|-------|------|------|----------|
| `qwen2.5:7b-instruct` | 4.4GB | ~8GB | ✅ Tool calling, SQL queries |
| `llama3.1:8b` | 4.7GB | ~8GB | General reasoning |
| `mistral:7b-instruct` | 4.1GB | ~6GB | Lightweight option |
| `codellama:7b` | 3.8GB | ~6GB | Code-focused tasks |

### Model Configuration

Pull your chosen model:

```bash
# Recommended for tool calling
ollama pull qwen2.5:7b-instruct

# Verify model is available
ollama list
```

### Custom Model Settings

For advanced Ollama configuration:

```bash
# Create custom Modelfile
FROM qwen2.5:7b-instruct
PARAMETER temperature 0.7
PARAMETER num_ctx 8192
PARAMETER num_predict 2048
```

```bash
# Create custom model
ollama create custom-research -f Modelfile
```

Then update `.env`:

```bash
OLLAMA_MODEL=custom-research
```

---

## 🗄️ Database Configuration

### Dual Database Architecture

The system uses two SQL Server instances:

| Database | Version | Port | Purpose |
|----------|---------|------|---------|
| **ResearchAnalytics** | SQL Server 2022 | 1433 | Sample demo data for queries |
| **LLM_BackEnd** | SQL Server 2025 | 1434 | Application state + native vectors |

### Docker SQL Server (Sample Database)

The Docker setup uses these defaults for the sample database:

| Setting | Value |
|---------|-------|
| Image | `mcr.microsoft.com/mssql/server:2022-latest` |
| Container | `local-agent-mssql` |
| Port | `1433` |
| SA Password | `LocalLLM@2024!` |
| Database | `ResearchAnalytics` |

### Docker SQL Server 2025 (Backend Database)

The backend database uses SQL Server 2025 with native vector support:

| Setting | Value |
|---------|-------|
| Image | `mcr.microsoft.com/mssql/server:2025-latest` |
| Container | `local-agent-mssql-backend` |
| Port | `1434` |
| SA Password | `LocalLLM@2024!` |
| Database | `LLM_BackEnd` |
| Schemas | `app` (tables), `vectors` (embeddings) |

**SQL Server 2025 Features Used:**
- **Native VECTOR(768) type** - Store embeddings directly in SQL
- **VECTOR_DISTANCE function** - Cosine similarity search
- **Preview features enabled** - Required for vector operations

### Backend Database Configuration

Configure the backend database connection:

```bash
# .env - Backend Database (SQL Server 2025)
BACKEND_DB_HOST=localhost
BACKEND_DB_PORT=1434
BACKEND_DB_NAME=LLM_BackEnd
BACKEND_DB_USERNAME=               # Defaults to SQL_USERNAME if empty
BACKEND_DB_PASSWORD=               # Defaults to SQL_PASSWORD if empty
BACKEND_DB_TRUST_CERT=true
```

### Vector Store Configuration

Choose between SQL Server 2025 native vectors (primary) or Redis Stack (fallback):

```bash
# .env - Vector Store
# Options: "mssql" (SQL Server 2025) or "redis" (Redis Stack)
VECTOR_STORE_TYPE=mssql

# Embedding dimensions (768 for nomic-embed-text, 384 for all-MiniLM-L6-v2)
VECTOR_DIMENSIONS=768
```

**Vector Store Comparison:**

| Feature | SQL Server 2025 (mssql) | Redis Stack (redis) |
|---------|-------------------------|---------------------|
| Storage | Relational tables | In-memory + persistence |
| Index Type | Native VECTOR type | HNSW index |
| Similarity | VECTOR_DISTANCE (cosine) | Cosine similarity |
| Scalability | SQL Server capabilities | Redis clustering |
| Dependencies | None (built-in) | Requires Redis Stack |

### Custom SA Password

Override the default password:

```bash
# Set in environment before starting Docker
export MSSQL_SA_PASSWORD="YourSecurePassword123!"

# Start containers
cd docker
docker compose up -d
```

Or in `.env`:

```bash
MSSQL_SA_PASSWORD=YourSecurePassword123!
SQL_PASSWORD=YourSecurePassword123!
```

### Connecting to Existing SQL Server

To use an existing SQL Server instance:

```bash
# .env
SQL_SERVER_HOST=your-server.database.windows.net
SQL_SERVER_PORT=1433
SQL_DATABASE_NAME=YourDatabase
SQL_TRUST_SERVER_CERTIFICATE=false
SQL_USERNAME=your_user
SQL_PASSWORD=your_password
```

> 💡 **Tip:** Set `SQL_TRUST_SERVER_CERTIFICATE=false` for production servers with valid certificates.

### Windows Authentication

For Windows Authentication (on-premises):

```bash
# .env
SQL_SERVER_HOST=your-server
SQL_DATABASE_NAME=YourDatabase
# Leave username/password empty for Windows Auth
SQL_USERNAME=
SQL_PASSWORD=
```

---

## 🔐 Security Configuration

### Read-Only Mode

Enable read-only mode for safe exploration:

```bash
# .env
MCP_MSSQL_READONLY=true
```

In read-only mode, these operations are blocked:

| Operation | Status |
|-----------|--------|
| `list_tables` | ✅ Allowed |
| `describe_table` | ✅ Allowed |
| `read_data` | ✅ Allowed |
| `insert_data` | ❌ Blocked |
| `update_data` | ❌ Blocked |
| `delete_data` | ❌ Blocked |
| `create_table` | ❌ Blocked |
| `drop_table` | ❌ Blocked |

### Credential Security

Best practices for credential management:

| Practice | Status |
|----------|--------|
| Use `.env` files | ✅ Recommended |
| Use environment variables | ✅ Recommended |
| Hardcode passwords | ❌ Never |
| Commit `.env` to git | ❌ Never |
| Use secrets manager | ✅ Production |

### Network Security

For Docker deployments:

```yaml
# docker-compose.yml - Restrict to localhost
services:
  mssql:
    ports:
      - "127.0.0.1:1433:1433"  # Only localhost access
```

---

## 🔧 Advanced Options

### Logging Configuration

Configure structured logging:

```bash
# .env
LOG_LEVEL=DEBUG           # DEBUG, INFO, WARNING, ERROR
LOG_FORMAT=json           # json or console
LOG_FILE=/var/log/agent.log
```

### Performance Tuning

| Setting | Default | Description |
|---------|---------|-------------|
| `MCP_TIMEOUT` | `30` | MCP operation timeout |
| `OLLAMA_TIMEOUT` | `120` | LLM inference timeout |
| `MAX_RETRIES` | `3` | Max retry attempts |
| `CONTEXT_WINDOW` | `8192` | Model context size |

```bash
# .env - Performance
MCP_TIMEOUT=60
OLLAMA_TIMEOUT=180
MAX_RETRIES=5
CONTEXT_WINDOW=16384
```

### Debug Mode

Enable comprehensive debugging:

```bash
# .env
DEBUG=true
LOG_LEVEL=DEBUG
```

Debug mode enables:

- Verbose MCP communication logs
- Full SQL query tracing
- LLM prompt/response logging
- Performance timing metrics

---

## 📋 Complete Example

Full `.env` configuration:

```bash
# ======================
# Ollama Configuration
# ======================
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=qwen2.5:7b-instruct
OLLAMA_TIMEOUT=120

# ======================
# SQL Server Configuration (Sample Database)
# ======================
SQL_SERVER_HOST=localhost
SQL_SERVER_PORT=1433
SQL_DATABASE_NAME=ResearchAnalytics
SQL_TRUST_SERVER_CERTIFICATE=true
SQL_USERNAME=sa
SQL_PASSWORD=LocalLLM@2024!

# ======================
# Backend Database (SQL Server 2025)
# ======================
BACKEND_DB_HOST=localhost
BACKEND_DB_PORT=1434
BACKEND_DB_NAME=LLM_BackEnd
BACKEND_DB_USERNAME=
BACKEND_DB_PASSWORD=
BACKEND_DB_TRUST_CERT=true

# ======================
# Vector Store Configuration
# ======================
VECTOR_STORE_TYPE=mssql
VECTOR_DIMENSIONS=768

# ======================
# Redis Configuration (fallback)
# ======================
REDIS_URL=redis://localhost:6379

# ======================
# MCP Configuration
# ======================
MCP_MSSQL_PATH=/path/to/SQL-AI-samples/MssqlMcp/Node/dist/index.js
MCP_MSSQL_READONLY=false
MCP_TIMEOUT=30

# ======================
# Application Settings
# ======================
LOG_LEVEL=INFO
STREAMLIT_PORT=8501
DEBUG=false

# ======================
# Docker (if using custom password)
# ======================
MSSQL_SA_PASSWORD=LocalLLM@2024!
BACKEND_VOLUME_NAME=local-llm-backend-data
```

---

*Last Updated: December 2025*
