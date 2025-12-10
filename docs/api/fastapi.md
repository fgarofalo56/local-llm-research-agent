# FastAPI Backend API Reference

> **Phase 2.1: Backend Infrastructure**

The FastAPI backend provides a REST API for all agent operations, document management, conversations, and RAG search.

---

## Overview

| Property | Value |
|----------|-------|
| Base URL | `http://localhost:8000` |
| API Prefix | `/api` |
| Docs | `/docs` (Swagger UI) |
| ReDoc | `/redoc` |
| Version | 2.1.0 |

---

## Quick Start

```bash
# Start the server
uv run uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000

# Health check
curl http://localhost:8000/api/health

# API documentation
open http://localhost:8000/docs
```

---

## Endpoints

### Health Check (`/api/health`)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health` | GET | Basic health check |
| `/api/health/detailed` | GET | Detailed service status |
| `/api/health/metrics` | GET | System metrics (CPU, memory, etc.) |

#### GET `/api/health`

Returns basic health status.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-12-10T12:00:00Z",
  "version": "2.1.0"
}
```

#### GET `/api/health/detailed`

Returns detailed status of all services.

**Response:**
```json
{
  "status": "healthy",
  "services": {
    "database": {"status": "connected", "latency_ms": 5},
    "redis": {"status": "connected", "latency_ms": 2},
    "ollama": {"status": "running", "model": "qwen3:30b"},
    "mcp": {"status": "ready", "servers": 1}
  },
  "timestamp": "2025-12-10T12:00:00Z"
}
```

#### GET `/api/health/metrics`

Returns system performance metrics.

**Response:**
```json
{
  "cpu_percent": 25.5,
  "memory_percent": 45.2,
  "disk_percent": 60.0,
  "uptime_seconds": 3600,
  "request_count": 150
}
```

---

### Documents (`/api/documents`)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/documents` | GET | List all documents |
| `/api/documents` | POST | Upload a document |
| `/api/documents/{id}` | GET | Get document by ID |
| `/api/documents/{id}` | DELETE | Delete a document |
| `/api/documents/search` | POST | RAG vector search |
| `/api/documents/schema/index` | POST | Index database schema |

#### POST `/api/documents`

Upload a document for RAG indexing.

**Request:**
- Content-Type: `multipart/form-data`
- Body: `file` (PDF, DOCX, TXT, MD)

**Response:**
```json
{
  "id": 1,
  "filename": "report.pdf",
  "content_type": "application/pdf",
  "size_bytes": 102400,
  "chunk_count": 15,
  "indexed_at": "2025-12-10T12:00:00Z"
}
```

#### POST `/api/documents/search`

Search documents using RAG vector similarity.

**Request:**
```json
{
  "query": "What are the project requirements?",
  "top_k": 5,
  "source_type": "document"
}
```

**Response:**
```json
{
  "results": [
    {
      "content": "The project requires...",
      "source": "requirements.pdf",
      "score": 0.92,
      "document_id": "doc_123",
      "chunk_index": 3
    }
  ],
  "query": "What are the project requirements?",
  "total_results": 5
}
```

#### POST `/api/documents/schema/index`

Index the database schema for RAG context.

**Response:**
```json
{
  "status": "indexed",
  "tables_indexed": 8,
  "chunks_created": 24
}
```

---

### Conversations (`/api/conversations`)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/conversations` | GET | List conversations |
| `/api/conversations` | POST | Create conversation |
| `/api/conversations/{id}` | GET | Get conversation with messages |
| `/api/conversations/{id}` | PATCH | Update conversation |
| `/api/conversations/{id}` | DELETE | Delete conversation |
| `/api/conversations/{id}/messages` | POST | Add message |

#### GET `/api/conversations`

List all conversations.

**Query Parameters:**
- `skip`: Pagination offset (default: 0)
- `limit`: Max results (default: 20)
- `include_archived`: Include archived (default: false)

**Response:**
```json
{
  "conversations": [
    {
      "id": 1,
      "title": "Database Analysis",
      "created_at": "2025-12-10T12:00:00Z",
      "updated_at": "2025-12-10T12:30:00Z",
      "is_archived": false,
      "message_count": 10
    }
  ],
  "total": 5
}
```

#### POST `/api/conversations/{id}/messages`

Add a message to a conversation.

**Request:**
```json
{
  "role": "user",
  "content": "Show me all active projects",
  "tool_calls": null,
  "tokens_used": 15
}
```

**Response:**
```json
{
  "id": 42,
  "conversation_id": 1,
  "role": "user",
  "content": "Show me all active projects",
  "tool_calls": null,
  "tokens_used": 15,
  "created_at": "2025-12-10T12:35:00Z"
}
```

---

### Queries (`/api/queries`)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/queries/history` | GET | List query history |
| `/api/queries/history/{id}/favorite` | POST | Toggle favorite |
| `/api/queries/history/{id}` | DELETE | Delete from history |
| `/api/queries/saved` | GET | List saved queries |
| `/api/queries/saved` | POST | Save a query |
| `/api/queries/saved/{id}` | GET | Get saved query |
| `/api/queries/saved/{id}` | PUT | Update saved query |
| `/api/queries/saved/{id}` | DELETE | Delete saved query |

#### GET `/api/queries/history`

Get query execution history.

**Query Parameters:**
- `skip`: Pagination offset (default: 0)
- `limit`: Max results (default: 50)
- `favorites_only`: Only favorites (default: false)

**Response:**
```json
{
  "queries": [
    {
      "id": 1,
      "conversation_id": 1,
      "natural_language": "Show all researchers",
      "generated_sql": "SELECT * FROM Researchers",
      "result_row_count": 23,
      "execution_time_ms": 45,
      "is_favorite": true,
      "created_at": "2025-12-10T12:00:00Z"
    }
  ],
  "total": 50
}
```

---

### Dashboards (`/api/dashboards`)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/dashboards` | GET | List dashboards |
| `/api/dashboards` | POST | Create dashboard |
| `/api/dashboards/{id}` | GET | Get dashboard with widgets |
| `/api/dashboards/{id}` | PUT | Update dashboard |
| `/api/dashboards/{id}` | DELETE | Delete dashboard |
| `/api/dashboards/{id}/share` | POST | Create share link |
| `/api/dashboards/{id}/widgets` | POST | Add widget |
| `/api/dashboards/{id}/widgets/{wid}` | PUT | Update widget |
| `/api/dashboards/{id}/widgets/{wid}` | DELETE | Delete widget |

#### POST `/api/dashboards/{id}/widgets`

Add a widget to a dashboard.

**Request:**
```json
{
  "widget_type": "chart",
  "title": "Active Projects",
  "query": "SELECT Status, COUNT(*) FROM Projects GROUP BY Status",
  "chart_config": "{\"type\": \"pie\"}",
  "position": "{\"x\": 0, \"y\": 0, \"w\": 4, \"h\": 3}",
  "refresh_interval": 300
}
```

---

### MCP Servers (`/api/mcp`)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/mcp` | GET | List MCP servers |
| `/api/mcp/{name}` | GET | Get server details |
| `/api/mcp/{name}/tools` | GET | List server tools |

#### GET `/api/mcp`

List all configured MCP servers.

**Response:**
```json
{
  "servers": [
    {
      "name": "mssql",
      "command": "node",
      "status": "ready",
      "tool_count": 8
    }
  ]
}
```

#### GET `/api/mcp/{name}/tools`

List tools available on an MCP server.

**Response:**
```json
{
  "server": "mssql",
  "tools": [
    {"name": "list_tables", "description": "List all tables in database"},
    {"name": "describe_table", "description": "Get table schema"},
    {"name": "read_data", "description": "Query data from tables"}
  ]
}
```

---

### Settings (`/api/settings`)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/settings/theme` | GET | Get theme config |
| `/api/settings/theme` | PUT | Update theme |

#### PUT `/api/settings/theme`

Update theme configuration.

**Request:**
```json
{
  "mode": "dark",
  "primary_color": "#1976d2",
  "font_family": "Inter"
}
```

---

### Agent (`/api/agent`)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/agent/chat` | POST | Send message to agent |

#### POST `/api/agent/chat`

Send a message to the research agent.

**Request:**
```json
{
  "message": "What tables are in the database?",
  "conversation_id": 1,
  "include_rag_context": true
}
```

**Response:**
```json
{
  "response": "The database contains the following tables...",
  "tool_calls": [
    {"tool": "list_tables", "result": "[...]"}
  ],
  "tokens_used": 150,
  "rag_context": ["Schema: Researchers table..."]
}
```

---

## Error Responses

All endpoints return standard error responses:

```json
{
  "detail": "Error message describing the issue"
}
```

| Status Code | Meaning |
|-------------|---------|
| 400 | Bad Request - Invalid input |
| 404 | Not Found - Resource doesn't exist |
| 422 | Validation Error - Invalid data format |
| 500 | Internal Server Error |

---

## Database Models

The API uses SQLAlchemy ORM models stored in SQL Server:

| Model | Table | Description |
|-------|-------|-------------|
| Conversation | conversations | Chat sessions |
| Message | messages | Chat messages |
| Dashboard | dashboards | Dashboard configurations |
| DashboardWidget | dashboard_widgets | Widget configurations |
| QueryHistory | query_history | SQL execution history |
| SavedQuery | saved_queries | Saved/favorite queries |
| Document | documents | Uploaded documents |
| DataAlert | data_alerts | Alert configurations |
| ScheduledQuery | scheduled_queries | Scheduled reports |
| MCPServerConfig | mcp_server_configs | MCP server settings |
| ThemeConfig | theme_configs | UI theme settings |

---

## Configuration

Environment variables for the API:

```bash
# FastAPI
API_HOST=0.0.0.0
API_PORT=8000

# Database
DATABASE_URL=mssql+aioodbc://sa:password@localhost:1433/ResearchAnalytics?driver=ODBC+Driver+18+for+SQL+Server&TrustServerCertificate=yes

# Redis
REDIS_URL=redis://localhost:6379

# Uploads
UPLOAD_DIR=data/uploads
MAX_UPLOAD_SIZE_MB=50
```

---

*Last Updated: December 2025* (Phase 2.1)
