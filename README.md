# 🔍 Local LLM Universal Research Agent

> **A 100% local universal research agent combining SQL analytics, RAG-powered knowledge retrieval, and multi-MCP tool integration. Query databases, search documents, and leverage multiple tools - all with complete privacy via local Ollama inference.**

---

## ✨ Features

### 🔒 Privacy & Local Processing

| Feature | Description |
|---------|-------------|
| **Fully Local** | No cloud APIs - all LLM processing on your machine |
| **Privacy First** | Your data never leaves your network |
| **Multiple LLM Providers** | Ollama or Microsoft Foundry Local |
| **Streaming Responses** | Real-time token streaming |

### 💬 Natural Language SQL

| Feature | Description |
|---------|-------------|
| **Natural Language Queries** | Ask questions about your data in plain English |
| **MCP Integration** | Extensible tool architecture via Model Context Protocol |
| **Smart Tool Calling** | Agent automatically selects appropriate database operations |
| **Sample Database** | Docker-based SQL Server with demo data |

### 🖥️ User Interfaces

| Feature | Description |
|---------|-------------|
| **React Frontend** | Modern UI with React 19 + Vite + TypeScript |
| **Chat Toolbar** | Quick toggles for Thinking, Files, MCP Servers, Web Search |
| **Model Switcher** | Switch providers (Ollama/Foundry) and models on-the-fly |
| **Agent Status Indicator** | Live animated status with real-time tool call display |
| **Streamlit Web UI** | User-friendly web interface |
| **CLI Interface** | Command-line chat for development |
| **Dark/Light Theme** | System-aware theming with CSS variables |
| **WebSocket Chat** | Real-time streaming responses |

### 🚀 Backend & API

| Feature | Description |
|---------|-------------|
| **FastAPI Backend** | REST API with automatic OpenAPI docs |
| **SQLAlchemy ORM** | Database models with Alembic migrations |
| **Dual Database Architecture** | SQL Server 2022 (sample) + SQL Server 2025 (backend) |
| **SQL Server 2025 Vectors** | Native VECTOR type for embeddings (primary) |
| **Redis Vector Store** | Fast similarity search (fallback option) |
| **Dynamic MCP** | Configure MCP servers at runtime |

### 🧠 RAG Pipeline (Retrieval-Augmented Generation)

| Feature | Description |
|---------|-------------|
| **Docling Document Processing** | Advanced parsing for 14+ document types (PDF, DOCX, PPTX, XLSX, HTML, Markdown, Images) |
| **Ollama Embeddings** | Local document embeddings (nomic-embed-text, 768 dims) |
| **Hybrid Search** | Combines semantic (vector) + keyword (full-text) search with RRF |
| **MSSQL Vector Store** | SQL Server 2025 native VECTOR type (primary) |
| **Redis Vector Store** | Fallback vector search with Redis Stack |
| **Schema Indexing** | Database schema for context-aware queries |

### 📄 Supported Document Formats

| Format | Extensions | Processing |
|--------|------------|------------|
| **PDF** | `.pdf` | Text extraction, images, tables via Docling |
| **Word** | `.docx`, `.doc` | Full text + formatting |
| **PowerPoint** | `.pptx` | Slides + speaker notes |
| **Excel** | `.xlsx`, `.xls` | Sheet data + formulas |
| **HTML/Web** | `.html`, `.htm` | Clean text extraction |
| **Markdown** | `.md` | Full Markdown support |
| **Text** | `.txt` | Plain text |
| **Images** | `.png`, `.jpg`, `.jpeg` | OCR via Docling |
| **AsciiDoc** | `.adoc`, `.asciidoc` | Documentation format |

### 📊 Dashboards & Visualization

| Feature | Description |
|---------|-------------|
| **Recharts Integration** | Bar, Line, Area, Pie, Scatter charts |
| **AI Chart Suggestions** | Automatic chart type recommendations |
| **KPI Cards** | Single-value metric displays |
| **Dashboard Builder** | Create and manage custom dashboards |
| **Widget Pinning** | Pin query results to dashboards |
| **Drag & Drop Layout** | react-grid-layout for positioning |
| **Auto-Refresh** | Per-widget refresh intervals |

### 📤 Export System

| Feature | Description |
|---------|-------------|
| **PNG Export** | Export charts as high-resolution PNG images |
| **PDF Export** | Export dashboards and charts to PDF |
| **CSV Export** | Export query results to CSV format |
| **Excel Export** | Export data to Excel spreadsheets |
| **Dashboard JSON** | Import/export dashboard configurations |
| **Chat Export** | Export conversations to Markdown or PDF |
| **Power BI Dialog** | Integration dialog for PBIX export |

### 📈 Apache Superset BI Platform

| Feature | Description |
|---------|-------------|
| **Superset Container** | Apache Superset 3.1.0 with SQL Server driver |
| **SQL Lab** | Full SQL IDE for data exploration |
| **Dashboard Embedding** | Embed Superset dashboards in React app |
| **Guest Token Auth** | Secure iframe embedding with guest tokens |
| **Health Integration** | Superset status in health checks |

---

## 📑 Table of Contents

- [Quick Start](#-quick-start)
- [Docker Setup](#-docker-setup)
- [MSSQL MCP Server Setup](#-mssql-mcp-server-setup)
- [Configuration](#️-configuration)
- [Running the Application](#-running-the-application)
- [FastAPI Backend](#-fastapi-backend)
- [React Frontend](#️-react-frontend)
- [Dashboards & Visualization](#-dashboards--visualization)
- [Exports & Power BI](#-exports--power-bi)
- [Apache Superset](#-apache-superset)
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

## 🐳 Docker Setup

The project includes a complete Docker setup with SQL Server 2022, Redis Stack for vector search, and a pre-populated research analytics database.

### ⚠️ Critical: Environment File Requirement

When running docker-compose from the **project root** (recommended), you **MUST** include `--env-file .env`:

```bash
# ✅ Correct - includes env file
docker-compose -f docker/docker-compose.yml --env-file .env up -d

# ❌ Wrong - will use default ports, may cause conflicts
docker-compose -f docker/docker-compose.yml up -d
```

### 📦 Docker Services

| Service | Container Name | Port | Profile | Purpose |
|---------|---------------|------|---------|---------|
| **mssql** | `local-agent-mssql` | 1433 | default | SQL Server 2022 (sample database) |
| **mssql-backend** | `local-agent-mssql-backend` | 1434 | default | SQL Server 2025 (backend + vectors) |
| **redis-stack** | `local-agent-redis` | 6379, 8001* | default | Redis (caching, vector fallback) |
| **mssql-tools** | `local-agent-mssql-tools` | - | `init` | Sample database initialization |
| **mssql-backend-tools** | `local-agent-mssql-backend-tools` | - | `init` | Backend database initialization |
| **agent-ui** | `local-agent-streamlit-ui` | 8501 | default | Streamlit web interface |
| **agent-cli** | `local-agent-cli` | - | `cli` | Interactive CLI chat |
| **api** | `local-agent-api` | 8000 | `api` | FastAPI backend |
| **superset** | `local-agent-superset` | 8088 | `superset` | Apache Superset BI |

> *RedisInsight GUI port is configurable via `REDIS_INSIGHT_PORT` (default: 8001)

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

### 🚀 Starting the Services

#### Option 1: Full Stack Development (Recommended)

Use the convenience scripts to start all services at once:

**Windows:**
```bash
start-dev.bat
```

**Linux/Mac:**
```bash
./start-dev.sh
```

This starts:
- SQL Server 2022 (Docker) on port 1433 - Sample database (ResearchAnalytics)
- SQL Server 2025 (Docker) on port 1434 - Backend with vectors + hybrid search (LLM_BackEnd)
- Redis Stack (Docker) on ports 6379, 8001
- FastAPI Backend on port 8000
- React Frontend on port 5173

The scripts automatically initialize both databases with:
- Sample research data (ResearchAnalytics)
- App schema (conversations, messages, dashboards)
- Vector schema (native VECTOR type, full-text indexes)
- Hybrid search stored procedures (RRF fusion)

#### Option 2: Quick Database Setup (Windows)

```bash
cd docker
setup-database.bat
```

#### Option 3: Core Services Only (SQL Server + Redis)

```bash
# From project root - Start SQL Server and Redis
docker-compose -f docker/docker-compose.yml --env-file .env up -d

# Wait for services to be healthy
docker-compose -f docker/docker-compose.yml ps

# Initialize database with sample data (first time only)
docker-compose -f docker/docker-compose.yml --env-file .env --profile init up mssql-tools
```

#### Option 4: Full Stack via Docker (with FastAPI Backend)

```bash
# Start all services including the API
docker-compose -f docker/docker-compose.yml --env-file .env --profile api up -d
```

#### Option 5: With Superset BI Platform

```bash
# Start with Superset
docker-compose -f docker/docker-compose.yml --env-file .env --profile superset up -d

# Or start everything
docker-compose -f docker/docker-compose.yml --env-file .env --profile full up -d
```

### 🔌 Connection Details

**Sample Database (SQL Server 2022):**

| Setting | Value |
|---------|-------|
| **Server** | `localhost,1433` |
| **Database** | `ResearchAnalytics` |
| **Username** | `sa` |
| **Password** | `LocalLLM@2024!` (or your `MSSQL_SA_PASSWORD`) |

**Backend Database (SQL Server 2025 with vectors):**

| Setting | Value |
|---------|-------|
| **Server** | `localhost,1434` |
| **Database** | `LLM_BackEnd` |
| **Username** | `sa` |
| **Password** | `LocalLLM@2024!` (or your `MSSQL_SA_PASSWORD`) |

### 📋 Managing the Services

```bash
# View container status
docker-compose -f docker/docker-compose.yml ps

# View container logs
docker-compose -f docker/docker-compose.yml logs -f mssql

# Stop all services (preserves data)
docker-compose -f docker/docker-compose.yml down

# Stop and DELETE all data (fresh start)
docker-compose -f docker/docker-compose.yml down -v
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
LLM_PROVIDER=ollama  # or "foundry_local"

# Ollama Configuration
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=qwen2.5:7b-instruct

# Embedding model for RAG
EMBEDDING_MODEL=nomic-embed-text

# Microsoft Foundry Local Configuration (alternative)
FOUNDRY_ENDPOINT=http://127.0.0.1:53760
FOUNDRY_MODEL=phi-4
FOUNDRY_AUTO_START=true

# =============================================================================
# SQL Server Configuration
# =============================================================================
SQL_SERVER_HOST=localhost
SQL_SERVER_PORT=1433
SQL_DATABASE_NAME=ResearchAnalytics
SQL_TRUST_SERVER_CERTIFICATE=true
SQL_USERNAME=sa
SQL_PASSWORD=LocalLLM@2024!

# =============================================================================
# Docker Configuration
# =============================================================================
MSSQL_SA_PASSWORD=LocalLLM@2024!
MSSQL_VOLUME_NAME=local-llm-mssql-data
REDIS_VOLUME_NAME=local-llm-redis-data

# =============================================================================
# Redis Configuration
# =============================================================================
REDIS_URL=redis://localhost:6379
REDIS_PORT=6379
REDIS_INSIGHT_PORT=8001  # Change if port 8001 is in use

# =============================================================================
# Backend Database (SQL Server 2025 with native vectors)
# =============================================================================
BACKEND_DB_HOST=localhost
BACKEND_DB_PORT=1434
BACKEND_DB_NAME=LLM_BackEnd
BACKEND_DB_TRUST_CERT=true

# =============================================================================
# Vector Store Configuration
# =============================================================================
# Vector store type: "mssql" (SQL Server 2025) or "redis" (fallback)
VECTOR_STORE_TYPE=mssql
VECTOR_DIMENSIONS=768

# =============================================================================
# RAG Configuration
# =============================================================================
CHUNK_SIZE=500
CHUNK_OVERLAP=50
RAG_TOP_K=5

# =============================================================================
# Hybrid Search Configuration
# =============================================================================
# Enable hybrid search by default (combines vector + full-text search)
RAG_HYBRID_ENABLED=false
# Weight for semantic search in hybrid mode (0.0 = keyword only, 1.0 = semantic only)
RAG_HYBRID_ALPHA=0.5

### 🔍 Hybrid Search

Hybrid search combines semantic (vector) and keyword (full-text) search using Reciprocal Rank Fusion (RRF) for improved retrieval accuracy.

#### How It Works

```
RRF Score = α × (1/(k + vector_rank)) + (1-α) × (1/(k + keyword_rank))
```

| Parameter | Default | Description |
|-----------|---------|-------------|
| `alpha` | 0.5 | Weight for semantic search (0.0 = keyword only, 1.0 = semantic only) |
| `k` | 60 | RRF constant (higher = smoother ranking) |

#### When to Use

| Search Type | Best For |
|-------------|----------|
| **Semantic Only** (`alpha=1.0`) | Conceptual queries, synonyms, paraphrasing |
| **Hybrid** (`alpha=0.5`) | General queries, best overall accuracy |
| **Keyword Only** (`alpha=0.0`) | Exact matches, specific terms, code snippets |

#### API Usage

```bash
# Semantic search (default)
curl -X POST http://localhost:8000/api/documents/search \
  -H "Content-Type: application/json" \
  -d '{"query": "machine learning research", "top_k": 5}'

# Hybrid search (semantic + keyword)
curl -X POST http://localhost:8000/api/documents/search \
  -H "Content-Type: application/json" \
  -d '{"query": "machine learning research", "top_k": 5, "hybrid": true, "alpha": 0.5}'
```

#### WebSocket Chat with Hybrid Search

Enable hybrid search in WebSocket messages:

```json
{
  "type": "message",
  "content": "Find documents about vector embeddings",
  "rag_enabled": true,
  "rag_hybrid_search": true,
  "rag_alpha": 0.5
}
```

# =============================================================================
# MCP Configuration
# =============================================================================
MCP_MSSQL_PATH=/path/to/SQL-AI-samples/MssqlMcp/Node/dist/index.js
MCP_MSSQL_READONLY=false
MCP_CONFIG_PATH=mcp_config.json

# =============================================================================
# API Server Configuration
# =============================================================================
API_HOST=0.0.0.0
API_PORT=8000

# =============================================================================
# Storage Configuration
# =============================================================================
UPLOAD_DIR=./data/uploads
MAX_UPLOAD_SIZE_MB=100

# =============================================================================
# Superset Configuration (Optional)
# =============================================================================
SUPERSET_URL=http://localhost:8088
SUPERSET_SECRET_KEY=your_secure_key
SUPERSET_ADMIN_USER=admin
SUPERSET_ADMIN_PASSWORD=LocalLLM@2024!
SUPERSET_PORT=8088

# =============================================================================
# Application Settings
# =============================================================================
LOG_LEVEL=INFO
DEBUG=false
STREAMLIT_PORT=8501
```

### 🦙 LLM Provider Options

| Provider | Recommended Models | Notes |
|----------|-------------------|-------|
| **Ollama** | `qwen2.5:7b-instruct`, `llama3.1:8b` | Requires Ollama running |
| **Foundry Local** | `phi-4`, `phi-3-mini` | Microsoft's local runtime |

---

## 🚀 Running the Application

### ⌨️ CLI Interface

```bash
# Check available commands
uv run python -m src.cli.chat --help

# Start the CLI chat
uv run python -m src.cli.chat chat

# With streaming responses
uv run python -m src.cli.chat chat --stream

# Use Foundry Local instead of Ollama
uv run python -m src.cli.chat chat --provider foundry_local

# With read-only mode (safer for exploration)
uv run python -m src.cli.chat --readonly
```

### 📝 CLI Interactive Commands

Once inside the CLI chat, use these commands:

#### Core Commands

| Command | Description |
|---------|-------------|
| `quit` / `exit` / `q` | Exit the chat |
| `clear` | Clear conversation history |
| `status` | Show connection info and provider status |
| `cache` | Display cache statistics |
| `cache-clear` | Clear the response cache |
| `help` | Show available commands |

#### Export & History

| Command | Description |
|---------|-------------|
| `export [format]` | Export conversation (json, csv, md) |
| `history` | List saved sessions |
| `history save` | Save current session |
| `history load <id>` | Load a previous session |
| `history delete <id>` | Delete a saved session |

#### Provider & Model Switching

| Command | Description |
|---------|-------------|
| `/provider <name>` | Switch LLM provider (ollama, foundry_local) |
| `/model <name>` | Switch to a different model |
| `/models` | List all available models |

#### MCP Server Management

| Command | Description |
|---------|-------------|
| `/mcp` | List all MCP servers with status |
| `/mcp status <name>` | Show detailed server info |
| `/mcp add` | Add new server interactively |
| `/mcp enable <name>` | Enable a disabled server |
| `/mcp disable <name>` | Disable a server |
| `/mcp remove <name>` | Remove server from config |
| `/mcp reconnect <name>` | Reconnect a failed server |

#### Database Management

| Command | Description |
|---------|-------------|
| `db` | List configured databases |
| `db switch <name>` | Switch active database |
| `db add` | Add new database interactively |
| `db remove <name>` | Remove database config |

> 💡 **Tip**: MCP server changes require restarting the chat to take effect.

### 🌐 Streamlit Web UI

```bash
# Start the web interface
uv run streamlit run src/ui/streamlit_app.py

# Access at: http://localhost:8501
```

> 💡 **Tip**: The web UI includes a provider selector in the sidebar to switch between Ollama and Foundry Local.

---

## 📡 FastAPI Backend

The FastAPI backend provides a REST API for all agent operations, document management, and RAG search.

### Running the Backend

```bash
# Development mode (with hot reload)
uv run uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000

# Production mode
uv run uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --workers 4

# Access points:
# - API: http://localhost:8000
# - Swagger UI: http://localhost:8000/docs
# - ReDoc: http://localhost:8000/redoc
```

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health` | GET | Health check and service status |
| `/api/health/metrics` | GET | System metrics (CPU, memory, etc.) |
| `/api/documents` | GET/POST | List/upload documents |
| `/api/documents/search` | POST | RAG search (semantic or hybrid) |
| `/api/documents/schema/index` | POST | Index database schema |
| `/api/conversations` | GET/POST | List/create conversations |
| `/api/conversations/{id}` | GET/PATCH/DELETE | Manage conversation |
| `/api/conversations/{id}/messages` | POST | Add message |
| `/api/queries/history` | GET | Query execution history |
| `/api/queries/saved` | GET/POST | Saved queries |
| `/api/dashboards` | GET/POST | List/create dashboards |
| `/api/dashboards/{id}/widgets` | POST | Add dashboard widget |
| `/api/mcp` | GET | List MCP servers |
| `/api/mcp/{name}/tools` | GET | List MCP server tools |
| `/api/settings/theme` | GET/PUT | Theme configuration |
| `/api/settings/providers` | GET | List available LLM providers |
| `/api/agent/chat` | POST | Send message to agent |
| `/ws/agent/{conversation_id}` | WS | Real-time WebSocket chat |
| `/api/superset/health` | GET | Superset status |
| `/api/superset/dashboards` | GET | List Superset dashboards |
| `/api/superset/embed/{id}` | GET | Get embed URL with guest token |

### Database Migrations

```bash
# Generate new migration after model changes
uv run alembic revision --autogenerate -m "Add new table"

# Apply all pending migrations
uv run alembic upgrade head

# Rollback one migration
uv run alembic downgrade -1
```

---

## ⚛️ React Frontend

The React frontend provides a modern web interface for interacting with the research agent.

### Features

- **Real-time Chat** - WebSocket-based streaming responses from the agent
- **Chat Toolbar** - Quick access to chat options positioned above the input area:
  - **Thinking Toggle** - Enable/disable thinking mode for detailed reasoning
  - **Attach Files** - Upload documents for RAG context
  - **MCP Servers Panel** - View and select active MCP servers
  - **Web Search Toggle** - Enable/disable web search capabilities
- **Model/Provider Switcher** - Switch between LLM providers and models:
  - Provider selection (Ollama, Foundry Local)
  - Model dropdown (filters to models supporting chat + tool calling)
  - Switching restarts the conversation for clean context
- **Agent Status Indicator** - Live feedback while agent is working:
  - Animated cycling messages ("Thinking...", "Analyzing...", "Processing...")
  - Real-time tool status ("Calling list_tables...", "Querying database...")
  - Tool-specific icons for database, search, and document operations
- **Dark/Light Theme** - System-aware theming with manual override
- **Conversation History** - Browse and continue past conversations
- **MCP Server Selection** - Choose which tools the agent can use
- **Document Management** - Upload and search documents for RAG
- **Query History** - View and favorite SQL queries
- **Dashboard Builder** - Create custom analytics dashboards
- **Export System** - Export to PNG, PDF, CSV, Excel

### Tech Stack

| Package | Version | Purpose |
|---------|---------|---------|
| React | 19.1.0 | UI framework |
| Vite | 7.2.7 | Build tool & dev server |
| TanStack Query | 5.90.12 | Server state management |
| Zustand | 5.0.9 | Client state management |
| Tailwind CSS | 3.4.15 | Styling |
| React Router | 7.10.1 | Routing |
| Recharts | - | Data visualization |

### Running the Frontend

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
# Open http://localhost:5173

# Build for production
npm run build

# Preview production build
npm run preview
```

### Pages

| Route | Description |
|-------|-------------|
| `/chat` | Main chat interface with agent |
| `/chat/:id` | Specific conversation |
| `/documents` | Document upload and RAG search |
| `/dashboards` | Analytics dashboards with widgets |
| `/queries` | Query history and favorites |
| `/mcp-servers` | MCP server status and tools |
| `/superset` | Superset BI reports and embedding |
| `/settings` | Theme and app settings |

---

## 📊 Dashboards & Visualization

The dashboard system allows you to create custom analytics views with interactive charts and KPI cards.

### Features

| Feature | Description |
|---------|-------------|
| **Dashboard CRUD** | Create, edit, and delete dashboards |
| **Widget Pinning** | Pin query results directly to dashboards |
| **Chart Types** | Bar, Line, Area, Pie, Scatter charts via Recharts |
| **KPI Cards** | Single-value metrics with formatting |
| **Drag & Drop** | Resize and reposition widgets with react-grid-layout |
| **Auto-Refresh** | Per-widget refresh intervals (30s, 1m, 5m, etc.) |
| **Persistence** | Dashboard layout saved to SQL Server |

### Widget Types

| Type | Description | Best For |
|------|-------------|----------|
| `bar` | Vertical bar chart | Comparisons, categories |
| `line` | Line chart with points | Time series, trends |
| `area` | Filled area chart | Volumes, accumulation |
| `pie` | Pie/donut chart | Proportions, distributions |
| `scatter` | Scatter plot | Correlations, clusters |
| `kpi` | Single value card | Key metrics, counts |

### Usage

1. **Create Dashboard**: Navigate to `/dashboards` and click "New Dashboard"
2. **Add Widget**: Run a query in chat, then click "Pin to Dashboard"
3. **Arrange Layout**: Drag widgets to reposition, resize using corners
4. **Configure Refresh**: Set auto-refresh interval per widget
5. **Share**: Generate shareable link with expiration

---

## 📤 Exports & Power BI

Comprehensive export functionality for charts, dashboards, and conversations.

### Export Formats

| Format | Use Case | Features |
|--------|----------|----------|
| **PNG** | Chart images | High-resolution (2x scale), transparent background |
| **PDF** | Reports | Multi-page support, titles, timestamps |
| **CSV** | Data transfer | Standard comma-separated values |
| **Excel** | Analysis | Auto-calculated column widths, multi-sheet support |
| **JSON** | Backup/Restore | Dashboard configuration import/export |
| **Markdown** | Documentation | Chat conversation export |

### Export Locations

| Component | Export Options |
|-----------|---------------|
| **Charts** | PNG, PDF, CSV, Excel (via dropdown menu) |
| **Dashboards** | PDF (full page), JSON (configuration) |
| **Conversations** | Markdown, PDF |
| **Query Results** | CSV, Excel, Power BI |

### Power BI Integration

The Power BI export dialog allows you to:
- Specify table name for your data
- Set optional report name
- Create `.pbix` files ready for Power BI Desktop

---

## 📊 Apache Superset

Apache Superset provides enterprise-grade BI capabilities alongside the AI-powered React UI.

### Features

| Feature | Description |
|---------|-------------|
| **SQL Lab** | Full SQL IDE with syntax highlighting and query history |
| **40+ Charts** | Extensive visualization library |
| **Scheduled Reports** | Email reports on schedule |
| **Dashboard Embedding** | Embed dashboards in the React app |
| **Role-Based Access** | Native user management and permissions |

### Starting Superset

```bash
# Start Superset with dependencies
docker-compose -f docker/docker-compose.yml --env-file .env --profile superset up -d

# Wait for initialization (~60 seconds), then setup database connection
python scripts/setup_superset.py

# Access Superset
# URL: http://localhost:8088
# Username: admin
# Password: LocalLLM@2024! (or SUPERSET_ADMIN_PASSWORD)
```

### Embedding Dashboards

Superset dashboards can be embedded in the React application:

1. Create and publish a dashboard in Superset
2. Navigate to **Superset Reports** in the React app sidebar
3. Click on a dashboard to view it embedded
4. Use the external link button to open in full Superset

For detailed usage instructions, see [docs/superset-guide.md](docs/superset-guide.md).

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

### 🖥️ Streamlit UI Testing

For comprehensive Streamlit UI testing instructions and automated test scripts, see **[docs/STREAMLIT_TESTING.md](docs/STREAMLIT_TESTING.md)**.

**Quick Test (Windows):**
```bash
# Check system status
check-status.bat

# Start all services
start-all.bat

# Run Streamlit UI
test-streamlit.bat
```

The testing guide includes:
- ✅ Automated setup scripts (Windows batch files)
- ✅ Step-by-step manual testing procedures
- ✅ 7 comprehensive test cases (streaming, database queries, caching, etc.)
- ✅ Troubleshooting checklist
- ✅ Expected behavior and performance metrics

**Recent Fix:** Streamlit UI now properly manages MCP server sessions using `async with agent:` context manager, matching the CLI implementation pattern.

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
+-----------------------------------------------------------------------------+
|                           User Interfaces                                    |
|  +------------------+  +----------------------+  +------------------------+  |
|  |  ⌨️ CLI (Typer)  |  |  🌐 Streamlit Web UI |  |  ⚛️ React Frontend     |  |
|  +--------+---------+  +-----------+----------+  +-----------+------------+  |
+-----------|-----------------------|--------------------------|---------------+
            |                       |                          |
            v                       v                          v
+-----------------------------------------------------------------------------+
|                         🤖 Pydantic AI Agent                                |
|  +-----------------------------------------------------------------------+  |
|  |  System Prompt + Tool Orchestration + Conversation + RAG Context      |  |
|  +-----------------------------------------------------------------------+  |
+------------------------------------+----------------------------------------+
                                     |
            +------------------------+------------------------+
            |                        |                        |
            v                        v                        v
+--------------------+  +----------------------------+  +---------------------+
|  🦙 LLM Provider   |  |      🔌 MCP Servers        |  |  🧠 RAG Pipeline   |
|  +--------------+  |  |  +----------------------+ |  |  +---------------+   |
|  | Ollama       |  |  |  | MSSQL MCP Server     | |  |  | 📄 PDF/DOCX   |   |
|  | Foundry Local|  |  |  | (SQL Server Access)  | |  |  | 🔢 Embeddings |   |
|  +--------------+  |  |  +----------------------+ |  |  | 🔍 Search     |   |
+--------------------+  +----------------------------+  |  +---------------+  |
                                     |                  +----------+----------+
                                     v                             |
          +--------------------------+-----------------------------+
          |                                                        |
          v                                                        v
+----------------------------+              +--------------------------------+
|   🗃️ SQL Server 2022      |              |   🗃️ SQL Server 2025          |
|   (Sample Database)        |              |   (Backend + Vectors)          |
|   ResearchAnalytics        |              |   LLM_BackEnd                  |
|   Port: 1433               |              |   Port: 1434                   |
+----------------------------+              |   +------------------------+   |
                                            |   | VECTOR(768) Native     |   |
+----------------------------+              |   | Cosine Similarity      |   |
|  🔴 Redis Stack            |              |   +------------------------+   |
|   (Caching + Fallback)     |              +--------------------------------+
+----------------------------+
```

### 🔧 Tech Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| LLM Runtime | Ollama / Foundry Local | Local model inference |
| Agent Framework | Pydantic AI | Orchestration & tools |
| MCP Server | MSSQL MCP (Node.js) | SQL Server access |
| Backend API | FastAPI + Uvicorn | REST API |
| Frontend | React 19 + Vite | Modern web UI |
| Web UI | Streamlit | Alternative interface |
| CLI | Typer + Rich | Terminal interface |
| Sample Database | SQL Server 2022 | Demo data (ResearchAnalytics) |
| Backend Database | SQL Server 2025 | App state + native vectors (LLM_BackEnd) |
| ORM | SQLAlchemy 2.0 + Alembic | Database models |
| Vector Store (Primary) | SQL Server 2025 VECTOR | Native similarity search |
| Vector Store (Fallback) | Redis Stack | Alternative vector search |
| Hybrid Search | Full-Text + Vector | RRF-based result fusion |
| Document Processing | Docling | 14+ document formats |
| Embeddings | Ollama (nomic-embed-text) | 768-dimensional vectors |
| BI Platform | Apache Superset | Enterprise analytics |
| Validation | Pydantic v2 | Type-safe models |

### 📁 Project Structure

```
local-llm-research-agent/
├── src/
│   ├── agent/          # 🤖 Pydantic AI agent
│   ├── api/            # 🚀 FastAPI backend
│   │   ├── models/     # SQLAlchemy ORM models
│   │   └── routes/     # API endpoints
│   ├── rag/            # 🧠 RAG pipeline
│   │   ├── embedder.py             # Ollama embeddings
│   │   ├── mssql_vector_store.py   # SQL Server 2025 vectors + hybrid search (primary)
│   │   ├── redis_vector_store.py   # Redis vectors + hybrid search (fallback)
│   │   ├── docling_processor.py    # Docling document processing (14+ formats)
│   │   ├── document_processor.py   # Legacy PDF/DOCX parsing
│   │   ├── vector_store_base.py    # Base class for vector stores
│   │   └── schema_indexer.py       # DB schema indexing
│   ├── providers/      # 🦙 LLM provider abstraction
│   ├── mcp/            # 🔌 MCP client and config
│   ├── cli/            # ⌨️ Command-line interface
│   ├── ui/             # 🌐 Streamlit web interface
│   ├── models/         # 📋 Pydantic data models
│   └── utils/          # ⚙️ Configuration and logging
├── frontend/           # ⚛️ React frontend
├── alembic/            # 🗄️ Database migrations
├── data/               # 📁 Uploads and cache
├── docker/             # 🐳 Docker configuration
│   ├── docker-compose.yml
│   ├── Dockerfile.api
│   ├── init/           # Sample database init scripts
│   └── init-backend/   # Backend database init scripts (SQL Server 2025)
│       ├── 01-create-llm-backend.sql    # Database + schemas
│       ├── 02-create-app-schema.sql     # Conversations, messages, dashboards
│       ├── 03-create-vectors-schema.sql # Native VECTOR tables
│       └── 04-create-hybrid-search.sql  # Full-text indexes + RRF procedures
├── tests/              # 🧪 Test suite
├── docs/               # 📚 Documentation
└── examples/           # 💡 Usage examples
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
- [Apache Superset](https://superset.apache.org/) - BI platform

---

*Last Updated: January 2026*
