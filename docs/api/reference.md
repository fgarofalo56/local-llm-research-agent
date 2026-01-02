# Complete API Reference

## Table of Contents

1. [Health Endpoints](#health-endpoints)
2. [Document Endpoints](#document-endpoints)
3. [Conversation Endpoints](#conversation-endpoints)
4. [Query Endpoints](#query-endpoints)
5. [Dashboard Endpoints](#dashboard-endpoints)
6. [Agent Endpoints](#agent-endpoints)
7. [MCP Server Endpoints](#mcp-server-endpoints)
8. [Settings Endpoints](#settings-endpoints)
9. [Alert Endpoints](#alert-endpoints)
10. [Scheduled Query Endpoints](#scheduled-query-endpoints)
11. [Superset Endpoints](#superset-endpoints)

---

## Health Endpoints

### Get Health Status

**GET** `/api/health`

Check health of all services including SQL Server, Redis, Ollama, and Superset.

**Response:** `200 OK`

```json
{
  "status": "healthy",
  "services": [
    {
      "name": "sql_server",
      "status": "healthy",
      "latency_ms": 2.45
    },
    {
      "name": "redis",
      "status": "healthy",
      "latency_ms": 1.23
    },
    {
      "name": "ollama",
      "status": "healthy",
      "latency_ms": 15.67
    },
    {
      "name": "superset",
      "status": "unknown",
      "message": "Not available"
    }
  ]
}
```

**cURL Example:**

```bash
curl -X GET http://localhost:8000/api/health
```

---

### Readiness Check

**GET** `/api/health/ready`

Simple readiness check for Kubernetes probes.

**Response:** `200 OK`

```json
{
  "status": "ready"
}
```

---

### Liveness Check

**GET** `/api/health/live`

Simple liveness check for Kubernetes probes.

**Response:** `200 OK`

```json
{
  "status": "alive"
}
```

---

### Get Services Status

**GET** `/api/health/services`

Get detailed status of configured services including MCP servers.

**Response:** `200 OK`

```json
{
  "api": {
    "status": "running",
    "version": "2.1.0"
  },
  "redis": {
    "status": "connected"
  },
  "mcp_servers": [
    {
      "id": "mssql",
      "name": "MSSQL MCP Server",
      "type": "stdio",
      "enabled": true
    }
  ]
}
```

---

## Document Endpoints

### List Documents

**GET** `/api/documents`

List all uploaded documents with optional filtering.

**Query Parameters:**
- `skip` (int): Items to skip (default: 0)
- `limit` (int): Items to return (default: 20)
- `tag` (string): Filter by tag

**Response:** `200 OK`

```json
{
  "documents": [
    {
      "id": 1,
      "filename": "a1b2c3d4.pdf",
      "original_filename": "research.pdf",
      "mime_type": "application/pdf",
      "file_size": 2048576,
      "chunk_count": 42,
      "processing_status": "completed",
      "error_message": null,
      "tags": ["research", "2024"],
      "created_at": "2024-12-18T10:30:00Z",
      "processed_at": "2024-12-18T10:35:00Z"
    }
  ],
  "total": 1
}
```

**cURL Example:**

```bash
curl -X GET "http://localhost:8000/api/documents?skip=0&limit=20"

# Filter by tag
curl -X GET "http://localhost:8000/api/documents?tag=research"
```

---

### Get All Tags

**GET** `/api/documents/tags/all`

Get all unique tags across all documents.

**Response:** `200 OK`

```json
{
  "tags": ["2024", "important", "research"],
  "total": 3
}
```

---

### Upload Document

**POST** `/api/documents`

Upload a new document for processing. Supported formats: PDF, DOCX.

**Request:**
- `file` (file): Document file (max size configurable, default 50MB)

**Response:** `200 OK`

```json
{
  "id": 1,
  "filename": "a1b2c3d4.pdf",
  "original_filename": "research.pdf",
  "mime_type": "application/pdf",
  "file_size": 2048576,
  "chunk_count": null,
  "processing_status": "pending",
  "error_message": null,
  "tags": [],
  "created_at": "2024-12-18T10:30:00Z",
  "processed_at": null
}
```

**cURL Example:**

```bash
curl -X POST http://localhost:8000/api/documents \
  -F "file=@research.pdf"
```

---

### Get Document

**GET** `/api/documents/{document_id}`

Get details of a specific document.

**Path Parameters:**
- `document_id` (int): Document ID

**Response:** `200 OK`

```json
{
  "id": 1,
  "filename": "a1b2c3d4.pdf",
  "original_filename": "research.pdf",
  "mime_type": "application/pdf",
  "file_size": 2048576,
  "chunk_count": 42,
  "processing_status": "completed",
  "error_message": null,
  "tags": ["research"],
  "created_at": "2024-12-18T10:30:00Z",
  "processed_at": "2024-12-18T10:35:00Z"
}
```

---

### Update Document Tags

**PATCH** `/api/documents/{document_id}/tags`

Update tags for a document.

**Path Parameters:**
- `document_id` (int): Document ID

**Request Body:**

```json
{
  "tags": ["research", "2024", "important"]
}
```

**Response:** `200 OK`

```json
{
  "id": 1,
  "filename": "a1b2c3d4.pdf",
  "original_filename": "research.pdf",
  "mime_type": "application/pdf",
  "file_size": 2048576,
  "chunk_count": 42,
  "processing_status": "completed",
  "error_message": null,
  "tags": ["research", "2024", "important"],
  "created_at": "2024-12-18T10:30:00Z",
  "processed_at": "2024-12-18T10:35:00Z"
}
```

**cURL Example:**

```bash
curl -X PATCH http://localhost:8000/api/documents/1/tags \
  -H "Content-Type: application/json" \
  -d '{"tags": ["research", "2024"]}'
```

---

### Reprocess Document

**POST** `/api/documents/{document_id}/reprocess`

Reprocess a failed or stuck document.

**Path Parameters:**
- `document_id` (int): Document ID

**Response:** `200 OK`

```json
{
  "id": 1,
  "filename": "a1b2c3d4.pdf",
  "original_filename": "research.pdf",
  "mime_type": "application/pdf",
  "file_size": 2048576,
  "chunk_count": null,
  "processing_status": "pending",
  "error_message": null,
  "tags": ["research"],
  "created_at": "2024-12-18T10:30:00Z",
  "processed_at": null
}
```

---

### Recover Stuck Documents

**POST** `/api/documents/recover-stuck`

Recover documents stuck in 'processing' status.

**Response:** `200 OK`

```json
{
  "recovered_count": 2,
  "document_ids": [5, 7],
  "message": "Recovered 2 stuck document(s) and queued for reprocessing"
}
```

---

### Delete Document

**DELETE** `/api/documents/{document_id}`

Delete a document and its embeddings.

**Path Parameters:**
- `document_id` (int): Document ID

**Response:** `200 OK`

```json
{
  "status": "deleted",
  "document_id": 1
}
```

---

## Conversation Endpoints

### List Conversations

**GET** `/api/conversations`

List all conversations.

**Query Parameters:**
- `skip` (int): Items to skip (default: 0)
- `limit` (int): Items to return (default: 20)
- `include_archived` (bool): Include archived conversations (default: false)

**Response:** `200 OK`

```json
{
  "conversations": [
    {
      "id": 1,
      "title": "Analysis Session",
      "created_at": "2024-12-18T10:00:00Z",
      "updated_at": "2024-12-18T10:30:00Z",
      "is_archived": false,
      "message_count": 5
    }
  ],
  "total": 1
}
```

---

### Create Conversation

**POST** `/api/conversations`

Create a new conversation.

**Request Body:**

```json
{
  "title": "Analysis Session"
}
```

**Response:** `200 OK`

```json
{
  "id": 1,
  "title": "Analysis Session",
  "created_at": "2024-12-18T10:00:00Z",
  "updated_at": "2024-12-18T10:00:00Z",
  "is_archived": false,
  "message_count": 0
}
```

**cURL Example:**

```bash
curl -X POST http://localhost:8000/api/conversations \
  -H "Content-Type: application/json" \
  -d '{"title": "Analysis Session"}'
```

---

### Get Conversation

**GET** `/api/conversations/{conversation_id}`

Get conversation with all messages.

**Path Parameters:**
- `conversation_id` (int): Conversation ID

**Response:** `200 OK`

```json
{
  "id": 1,
  "title": "Analysis Session",
  "created_at": "2024-12-18T10:00:00Z",
  "updated_at": "2024-12-18T10:30:00Z",
  "is_archived": false,
  "message_count": 2,
  "messages": [
    {
      "id": 1,
      "conversation_id": 1,
      "role": "user",
      "content": "What are the active projects?",
      "tool_calls": null,
      "tokens_used": 15,
      "created_at": "2024-12-18T10:05:00Z"
    },
    {
      "id": 2,
      "conversation_id": 1,
      "role": "assistant",
      "content": "There are 5 active projects...",
      "tool_calls": "[...]",
      "tokens_used": 45,
      "created_at": "2024-12-18T10:06:00Z"
    }
  ]
}
```

---

### List Messages

**GET** `/api/conversations/{conversation_id}/messages`

List messages in a conversation.

**Path Parameters:**
- `conversation_id` (int): Conversation ID

**Query Parameters:**
- `skip` (int): Items to skip (default: 0)
- `limit` (int): Items to return (default: 100)

**Response:** `200 OK`

```json
{
  "messages": [
    {
      "id": 1,
      "conversation_id": 1,
      "role": "user",
      "content": "What are the active projects?",
      "tool_calls": null,
      "tokens_used": 15,
      "created_at": "2024-12-18T10:05:00Z"
    }
  ],
  "total": 1
}
```

---

### Add Message

**POST** `/api/conversations/{conversation_id}/messages`

Add a message to conversation.

**Path Parameters:**
- `conversation_id` (int): Conversation ID

**Request Body:**

```json
{
  "role": "user",
  "content": "What projects are active?",
  "tool_calls": null,
  "tokens_used": 15
}
```

**Response:** `200 OK`

```json
{
  "id": 1,
  "conversation_id": 1,
  "role": "user",
  "content": "What are the active projects?",
  "tool_calls": null,
  "tokens_used": 15,
  "created_at": "2024-12-18T10:05:00Z"
}
```

---

### Update Conversation

**PATCH** `/api/conversations/{conversation_id}`

Update conversation title or archive status.

**Path Parameters:**
- `conversation_id` (int): Conversation ID

**Query Parameters:**
- `title` (string): New title
- `is_archived` (bool): Archive status

**Response:** `200 OK`

```json
{
  "status": "updated",
  "conversation_id": 1
}
```

**cURL Example:**

```bash
curl -X PATCH "http://localhost:8000/api/conversations/1?title=Updated Title&is_archived=false"
```

---

### Delete Conversation

**DELETE** `/api/conversations/{conversation_id}`

Delete conversation and all messages.

**Path Parameters:**
- `conversation_id` (int): Conversation ID

**Response:** `200 OK`

```json
{
  "status": "deleted",
  "conversation_id": 1
}
```

---

## Query Endpoints

### List Queries

**GET** `/api/queries`

List query history (alias for `/api/queries/history`).

**Query Parameters:**
- `skip` (int): Items to skip (default: 0)
- `limit` (int): Items to return (default: 50)
- `is_favorite` (bool): Filter by favorite status (default: false)

**Response:** `200 OK`

```json
{
  "queries": [
    {
      "id": 1,
      "conversation_id": null,
      "natural_language": "Show me active projects",
      "generated_sql": "SELECT * FROM Projects WHERE Status = 'Active'",
      "result_row_count": 5,
      "execution_time_ms": 245,
      "is_favorite": false,
      "created_at": "2024-12-18T10:30:00Z"
    }
  ],
  "total": 1
}
```

---

### Execute Query

**POST** `/api/queries/execute`

Execute a SQL query and return results (SELECT only).

**Request Body:**

```json
{
  "query": "SELECT * FROM Researchers WHERE Department = 'AI' LIMIT 10"
}
```

**Response:** `200 OK`

```json
{
  "data": [
    {
      "ResearcherID": 1,
      "FirstName": "Alice",
      "LastName": "Johnson",
      "Department": "AI",
      "Specialization": "Neural Networks"
    }
  ],
  "columns": ["ResearcherID", "FirstName", "LastName", "Department", "Specialization"],
  "row_count": 1,
  "execution_time_ms": 145
}
```

**cURL Example:**

```bash
curl -X POST http://localhost:8000/api/queries/execute \
  -H "Content-Type: application/json" \
  -d '{"query": "SELECT * FROM Projects LIMIT 10"}'
```

---

### List Saved Queries

**GET** `/api/queries/saved`

List saved queries.

**Query Parameters:**
- `skip` (int): Items to skip (default: 0)
- `limit` (int): Items to return (default: 50)

**Response:** `200 OK`

```json
{
  "queries": [
    {
      "id": 1,
      "name": "Active Projects",
      "description": "All active projects",
      "query": "SELECT * FROM Projects WHERE Status = 'Active'",
      "tags": "[\"analysis\"]",
      "created_at": "2024-12-18T10:00:00Z"
    }
  ],
  "total": 1
}
```

---

### Create Saved Query

**POST** `/api/queries/saved`

Save a query for reuse.

**Request Body:**

```json
{
  "name": "Active Projects",
  "description": "All active projects in the database",
  "query": "SELECT * FROM Projects WHERE Status = 'Active'"
}
```

**Response:** `200 OK`

```json
{
  "id": 1,
  "name": "Active Projects",
  "description": "All active projects in the database",
  "query": "SELECT * FROM Projects WHERE Status = 'Active'",
  "tags": null,
  "created_at": "2024-12-18T10:00:00Z"
}
```

---

### Get Saved Query

**GET** `/api/queries/saved/{query_id}`

Get a saved query.

**Path Parameters:**
- `query_id` (int): Query ID

**Response:** `200 OK`

```json
{
  "id": 1,
  "name": "Active Projects",
  "description": "All active projects in the database",
  "query": "SELECT * FROM Projects WHERE Status = 'Active'",
  "tags": null,
  "created_at": "2024-12-18T10:00:00Z"
}
```

---

### Update Saved Query

**PUT** `/api/queries/saved/{query_id}`

Update a saved query.

**Path Parameters:**
- `query_id` (int): Query ID

**Request Body:**

```json
{
  "name": "Active Projects Updated",
  "description": "All currently active projects",
  "query": "SELECT * FROM Projects WHERE Status = 'Active' ORDER BY CreatedDate DESC"
}
```

**Response:** `200 OK`

```json
{
  "id": 1,
  "name": "Active Projects Updated",
  "description": "All currently active projects",
  "query": "SELECT * FROM Projects WHERE Status = 'Active' ORDER BY CreatedDate DESC",
  "tags": null,
  "created_at": "2024-12-18T10:00:00Z"
}
```

---

### Delete Saved Query

**DELETE** `/api/queries/saved/{query_id}`

Delete a saved query.

**Path Parameters:**
- `query_id` (int): Query ID

**Response:** `200 OK`

```json
{
  "status": "deleted",
  "query_id": 1
}
```

---

### Toggle Query Favorite

**POST** `/api/queries/history/{query_id}/favorite`

Toggle favorite status for a query.

**Path Parameters:**
- `query_id` (int): Query ID

**Response:** `200 OK`

```json
{
  "status": "updated",
  "query_id": 1,
  "is_favorite": true
}
```

---

## Dashboard Endpoints

### List Dashboards

**GET** `/api/dashboards`

List all dashboards.

**Query Parameters:**
- `skip` (int): Items to skip (default: 0)
- `limit` (int): Items to return (default: 20)

**Response:** `200 OK`

```json
{
  "dashboards": [
    {
      "id": 1,
      "name": "Analytics Dashboard",
      "description": "Main analytics dashboard",
      "created_at": "2024-12-18T10:00:00Z",
      "updated_at": "2024-12-18T10:00:00Z"
    }
  ],
  "total": 1
}
```

---

### Create Dashboard

**POST** `/api/dashboards`

Create a new dashboard.

**Request Body:**

```json
{
  "name": "Analytics Dashboard",
  "description": "Main analytics dashboard"
}
```

**Response:** `201 Created`

```json
{
  "id": 1,
  "name": "Analytics Dashboard",
  "description": "Main analytics dashboard",
  "created_at": "2024-12-18T10:00:00Z",
  "updated_at": "2024-12-18T10:00:00Z"
}
```

---

### Get Dashboard

**GET** `/api/dashboards/{dashboard_id}`

Get dashboard with all widgets.

**Path Parameters:**
- `dashboard_id` (int): Dashboard ID

**Response:** `200 OK`

```json
{
  "id": 1,
  "name": "Analytics Dashboard",
  "description": "Main analytics dashboard",
  "widgets": [
    {
      "id": 1,
      "dashboard_id": 1,
      "widget_type": "bar",
      "title": "Projects by Department",
      "query": "SELECT Department, COUNT(*) FROM Projects GROUP BY Department",
      "chart_config": {
        "xKey": "Department",
        "yKeys": ["count"]
      },
      "position": {"x": 0, "y": 0, "w": 6, "h": 4},
      "refresh_interval": null,
      "created_at": "2024-12-18T10:00:00Z",
      "updated_at": "2024-12-18T10:00:00Z"
    }
  ],
  "created_at": "2024-12-18T10:00:00Z",
  "updated_at": "2024-12-18T10:00:00Z"
}
```

---

### Add Widget

**POST** `/api/dashboards/{dashboard_id}/widgets`

Add a widget to dashboard.

**Path Parameters:**
- `dashboard_id` (int): Dashboard ID

**Request Body:**

```json
{
  "widget_type": "bar",
  "title": "Projects by Department",
  "query": "SELECT Department, COUNT(*) AS count FROM Projects GROUP BY Department",
  "chart_config": {
    "xKey": "Department",
    "yKeys": ["count"],
    "colors": ["#8884d8"]
  },
  "position": {
    "x": 0,
    "y": 0,
    "w": 6,
    "h": 4
  },
  "refresh_interval": 300
}
```

**Response:** `201 Created`

```json
{
  "id": 1,
  "dashboard_id": 1,
  "widget_type": "bar",
  "title": "Projects by Department",
  "query": "SELECT Department, COUNT(*) FROM Projects GROUP BY Department",
  "chart_config": "{\"xKey\": \"Department\", \"yKeys\": [\"count\"]}",
  "position": "{\"x\": 0, \"y\": 0, \"w\": 6, \"h\": 4}",
  "refresh_interval": 300,
  "created_at": "2024-12-18T10:00:00Z",
  "updated_at": "2024-12-18T10:00:00Z"
}
```

---

### Update Widget

**PATCH** `/api/dashboards/{dashboard_id}/widgets/{widget_id}`

Update a widget.

**Path Parameters:**
- `dashboard_id` (int): Dashboard ID
- `widget_id` (int): Widget ID

**Request Body:**

```json
{
  "title": "Projects by Department (Updated)",
  "refresh_interval": 600
}
```

**Response:** `200 OK`

```json
{
  "id": 1,
  "dashboard_id": 1,
  "widget_type": "bar",
  "title": "Projects by Department (Updated)",
  "query": "SELECT Department, COUNT(*) FROM Projects GROUP BY Department",
  "chart_config": "{\"xKey\": \"Department\", \"yKeys\": [\"count\"]}",
  "position": "{\"x\": 0, \"y\": 0, \"w\": 6, \"h\": 4}",
  "refresh_interval": 600,
  "created_at": "2024-12-18T10:00:00Z",
  "updated_at": "2024-12-18T10:00:00Z"
}
```

---

### Delete Widget

**DELETE** `/api/dashboards/{dashboard_id}/widgets/{widget_id}`

Delete a widget.

**Path Parameters:**
- `dashboard_id` (int): Dashboard ID
- `widget_id` (int): Widget ID

**Response:** `200 OK`

```json
{
  "status": "deleted",
  "widget_id": 1
}
```

---

### Delete Dashboard

**DELETE** `/api/dashboards/{dashboard_id}`

Delete a dashboard and all its widgets.

**Path Parameters:**
- `dashboard_id` (int): Dashboard ID

**Response:** `200 OK`

```json
{
  "status": "deleted",
  "dashboard_id": 1
}
```

---

## Agent Endpoints

### Chat

**POST** `/api/agent/chat`

Send a message to the research agent.

**Request Body:**

```json
{
  "message": "What are the active projects?",
  "conversation_id": 1,
  "use_rag": true,
  "mcp_servers": ["mssql"]
}
```

**Response:** `200 OK`

```json
{
  "response": "There are 5 active projects...",
  "conversation_id": 1,
  "sources": [
    {
      "type": "document",
      "source": "research.pdf",
      "similarity": 0.95
    }
  ],
  "tool_calls": []
}
```

---

### RAG Search

**POST** `/api/agent/search`

Search the RAG vector store for relevant documents.

**Request Body:**

```json
{
  "query": "machine learning techniques",
  "top_k": 5,
  "source_type": "document"
}
```

**Response:** `200 OK`

```json
{
  "results": [
    {
      "source": "research.pdf",
      "chunk": "Machine learning techniques include...",
      "similarity": 0.95,
      "source_type": "document"
    }
  ],
  "query": "machine learning techniques"
}
```

**cURL Example:**

```bash
curl -X POST http://localhost:8000/api/agent/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "neural networks",
    "top_k": 5,
    "source_type": "document"
  }'
```

---

## MCP Server Endpoints

### List MCP Servers

**GET** `/api/mcp-servers`

List all configured MCP servers.

**Response:** `200 OK`

```json
{
  "servers": [
    {
      "id": "mssql",
      "name": "MSSQL MCP Server",
      "description": "SQL Server database access",
      "type": "stdio",
      "command": "node",
      "args": ["/path/to/mssql/index.js"],
      "url": null,
      "enabled": true,
      "built_in": true,
      "status": "connected",
      "tools": [
        "list_tables",
        "describe_table",
        "read_data",
        "insert_data",
        "update_data",
        "create_table",
        "drop_table",
        "create_index"
      ]
    }
  ],
  "total": 1
}
```

---

### Create MCP Server

**POST** `/api/mcp-servers`

Add a new MCP server configuration.

**Request Body:**

```json
{
  "id": "custom-tool",
  "name": "Custom Tool Server",
  "description": "My custom MCP server",
  "type": "stdio",
  "command": "node",
  "args": ["/path/to/server/index.js"],
  "url": null,
  "env": {
    "API_KEY": "secret"
  },
  "enabled": true
}
```

**Response:** `201 Created`

```json
{
  "id": "custom-tool",
  "name": "Custom Tool Server",
  "description": "My custom MCP server",
  "type": "stdio",
  "command": "node",
  "args": ["/path/to/server/index.js"],
  "url": null,
  "enabled": true,
  "built_in": false,
  "status": "connected",
  "tools": []
}
```

---

### Update MCP Server

**PATCH** `/api/mcp-servers/{server_id}`

Update MCP server configuration.

**Path Parameters:**
- `server_id` (string): Server ID

**Request Body:**

```json
{
  "enabled": false,
  "name": "Custom Tool Server (Disabled)"
}
```

**Response:** `200 OK`

```json
{
  "id": "custom-tool",
  "name": "Custom Tool Server (Disabled)",
  "description": "My custom MCP server",
  "type": "stdio",
  "command": "node",
  "args": ["/path/to/server/index.js"],
  "url": null,
  "enabled": false,
  "built_in": false,
  "status": "disconnected",
  "tools": []
}
```

---

### Delete MCP Server

**DELETE** `/api/mcp-servers/{server_id}`

Remove MCP server configuration.

**Path Parameters:**
- `server_id` (string): Server ID

**Response:** `200 OK`

```json
{
  "status": "deleted",
  "server_id": "custom-tool"
}
```

---

## Settings Endpoints

### Get Application Settings

**GET** `/api/settings`

Get current application configuration.

**Response:** `200 OK`

```json
{
  "llm_provider": "ollama",
  "ollama_model": "qwen3:30b",
  "embedding_model": "nomic-embed-text",
  "sql_server_host": "localhost",
  "sql_database_name": "ResearchAnalytics",
  "chunk_size": 512,
  "chunk_overlap": 50,
  "rag_top_k": 5,
  "max_upload_size_mb": 50,
  "debug": false
}
```

---

### List Themes

**GET** `/api/settings/themes`

List all available themes.

**Response:** `200 OK`

```json
{
  "themes": [
    {
      "id": 1,
      "name": "light",
      "display_name": "Light Mode",
      "is_preset": true,
      "is_active": true,
      "config": "{\"primary\": \"#0066cc\", \"background\": \"#ffffff\"}",
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-01T00:00:00Z"
    },
    {
      "id": 2,
      "name": "dark",
      "display_name": "Dark Mode",
      "is_preset": true,
      "is_active": false,
      "config": "{\"primary\": \"#00ccff\", \"background\": \"#1a1a1a\"}",
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-01T00:00:00Z"
    }
  ],
  "active_theme": "light"
}
```

---

### Create Theme

**POST** `/api/settings/themes`

Create a new custom theme.

**Request Body:**

```json
{
  "name": "custom",
  "display_name": "Custom Theme",
  "config": "{\"primary\": \"#ff6600\", \"background\": \"#f5f5f5\"}"
}
```

**Response:** `201 Created`

```json
{
  "id": 3,
  "name": "custom",
  "display_name": "Custom Theme",
  "is_preset": false,
  "is_active": false,
  "config": "{\"primary\": \"#ff6600\", \"background\": \"#f5f5f5\"}",
  "created_at": "2024-12-18T10:00:00Z",
  "updated_at": "2024-12-18T10:00:00Z"
}
```

---

### Set Active Theme

**POST** `/api/settings/themes/{theme_id}/activate`

Set a theme as active.

**Path Parameters:**
- `theme_id` (int): Theme ID

**Response:** `200 OK`

```json
{
  "status": "activated",
  "theme_id": 2,
  "theme_name": "dark"
}
```

---

## Alert Endpoints

### List Alerts

**GET** `/api/alerts`

List all data alerts.

**Query Parameters:**
- `skip` (int): Items to skip (default: 0)
- `limit` (int): Items to return (default: 50)
- `active_only` (bool): Only active alerts (default: false)

**Response:** `200 OK`

```json
{
  "alerts": [
    {
      "id": 1,
      "name": "High Activity Alert",
      "query": "SELECT COUNT(*) FROM Projects WHERE Status = 'Active'",
      "condition": "greater_than",
      "threshold": 10,
      "is_active": true,
      "last_checked_at": "2024-12-18T10:30:00Z",
      "last_triggered_at": "2024-12-18T10:25:00Z",
      "last_value": "12",
      "created_at": "2024-12-18T10:00:00Z"
    }
  ],
  "total": 1
}
```

---

### Create Alert

**POST** `/api/alerts`

Create a new data alert.

**Request Body:**

```json
{
  "name": "High Activity Alert",
  "query": "SELECT COUNT(*) FROM Projects WHERE Status = 'Active'",
  "condition": "greater_than",
  "threshold": 10
}
```

**Response:** `201 Created`

```json
{
  "id": 1,
  "name": "High Activity Alert",
  "query": "SELECT COUNT(*) FROM Projects WHERE Status = 'Active'",
  "condition": "greater_than",
  "threshold": 10,
  "is_active": true,
  "last_checked_at": null,
  "last_triggered_at": null,
  "last_value": null,
  "created_at": "2024-12-18T10:00:00Z"
}
```

---

### Update Alert

**PATCH** `/api/alerts/{alert_id}`

Update an alert configuration.

**Path Parameters:**
- `alert_id` (int): Alert ID

**Request Body:**

```json
{
  "threshold": 15,
  "is_active": false
}
```

**Response:** `200 OK`

```json
{
  "id": 1,
  "name": "High Activity Alert",
  "query": "SELECT COUNT(*) FROM Projects WHERE Status = 'Active'",
  "condition": "greater_than",
  "threshold": 15,
  "is_active": false,
  "last_checked_at": null,
  "last_triggered_at": null,
  "last_value": null,
  "created_at": "2024-12-18T10:00:00Z"
}
```

---

### Check Alert

**POST** `/api/alerts/{alert_id}/check`

Manually check if an alert should trigger.

**Path Parameters:**
- `alert_id` (int): Alert ID

**Response:** `200 OK`

```json
{
  "alert_id": 1,
  "name": "High Activity Alert",
  "current_value": 12,
  "threshold": 10,
  "condition": "greater_than",
  "triggered": true,
  "status": "checked"
}
```

---

### Delete Alert

**DELETE** `/api/alerts/{alert_id}`

Delete an alert.

**Path Parameters:**
- `alert_id` (int): Alert ID

**Response:** `200 OK`

```json
{
  "status": "deleted",
  "alert_id": 1
}
```

---

## Scheduled Query Endpoints

### List Scheduled Queries

**GET** `/api/scheduled-queries`

List all scheduled queries.

**Query Parameters:**
- `skip` (int): Items to skip (default: 0)
- `limit` (int): Items to return (default: 50)
- `active_only` (bool): Only active queries (default: false)

**Response:** `200 OK`

```json
{
  "queries": [
    {
      "id": 1,
      "name": "Daily Report",
      "query": "SELECT COUNT(*) FROM Projects WHERE CreatedDate >= CAST(GETDATE() AS DATE)",
      "cron_expression": "0 8 * * *",
      "is_active": true,
      "last_run_at": "2024-12-18T08:00:00Z",
      "next_run_at": "2024-12-19T08:00:00Z",
      "created_at": "2024-12-18T10:00:00Z"
    }
  ],
  "total": 1
}
```

---

### Create Scheduled Query

**POST** `/api/scheduled-queries`

Create a new scheduled query.

**Request Body:**

```json
{
  "name": "Daily Report",
  "query": "SELECT COUNT(*) FROM Projects WHERE CreatedDate >= CAST(GETDATE() AS DATE)",
  "cron_expression": "0 8 * * *"
}
```

**Response:** `201 Created`

```json
{
  "id": 1,
  "name": "Daily Report",
  "query": "SELECT COUNT(*) FROM Projects WHERE CreatedDate >= CAST(GETDATE() AS DATE)",
  "cron_expression": "0 8 * * *",
  "is_active": true,
  "last_run_at": null,
  "next_run_at": "2024-12-19T08:00:00Z",
  "created_at": "2024-12-18T10:00:00Z"
}
```

**Cron Expression Format:**
- `0 8 * * *` - Daily at 8 AM
- `0 0 * * MON` - Every Monday at midnight
- `0 9 1 * *` - First day of month at 9 AM
- `0 0 * * 1-5` - Weekdays at midnight

---

### Update Scheduled Query

**PATCH** `/api/scheduled-queries/{query_id}`

Update a scheduled query.

**Path Parameters:**
- `query_id` (int): Query ID

**Request Body:**

```json
{
  "cron_expression": "0 9 * * *",
  "is_active": false
}
```

**Response:** `200 OK`

```json
{
  "id": 1,
  "name": "Daily Report",
  "query": "SELECT COUNT(*) FROM Projects WHERE CreatedDate >= CAST(GETDATE() AS DATE)",
  "cron_expression": "0 9 * * *",
  "is_active": false,
  "last_run_at": null,
  "next_run_at": null,
  "created_at": "2024-12-18T10:00:00Z"
}
```

---

### Run Scheduled Query

**POST** `/api/scheduled-queries/{query_id}/run`

Manually execute a scheduled query.

**Path Parameters:**
- `query_id` (int): Query ID

**Response:** `200 OK`

```json
{
  "query_id": 1,
  "name": "Daily Report",
  "row_count": 15,
  "status": "executed"
}
```

---

### Delete Scheduled Query

**DELETE** `/api/scheduled-queries/{query_id}`

Delete a scheduled query.

**Path Parameters:**
- `query_id` (int): Query ID

**Response:** `200 OK`

```json
{
  "status": "deleted",
  "query_id": 1
}
```

---

## Superset Endpoints

### Superset Health

**GET** `/api/superset/health`

Check Superset health status.

**Response:** `200 OK`

```json
{
  "status": "healthy",
  "url": "http://localhost:8088",
  "error": null
}
```

---

### List Superset Dashboards

**GET** `/api/superset/dashboards`

List all Superset dashboards.

**Response:** `200 OK`

```json
{
  "dashboards": [
    {
      "id": 1,
      "dashboard_title": "Sales Dashboard",
      "slug": "sales-dashboard",
      "description": "Sales metrics and trends",
      "published": true,
      "created_on": "2024-01-01T10:00:00Z",
      "changed_on": "2024-12-18T10:00:00Z",
      "charts": []
    }
  ],
  "count": 1
}
```

---

### Get Superset Embed URL

**GET** `/api/superset/embed/{dashboard_id}`

Get embed URL with guest token for a dashboard.

**Path Parameters:**
- `dashboard_id` (int): Superset dashboard ID

**Response:** `200 OK`

```json
{
  "embed_url": "http://localhost:8088/superset/dashboard-permalink/abc123",
  "dashboard_id": "1"
}
```

---

## Rate Limits

Currently, no rate limits are enforced. This may change in future versions.

## Pagination

All list endpoints use offset/limit pagination:

```
GET /api/documents?skip=0&limit=20
```

The response includes a `total` field indicating the total number of available items.

## Best Practices

1. **Always check health before making requests**: `GET /api/health`
2. **Use WebSockets for real-time chat**: Reduces latency and server load
3. **Batch document uploads**: Group related documents with tags
4. **Cache saved queries**: Reuse common queries to reduce API calls
5. **Set up monitoring**: Use health endpoints in production systems

## Error Handling

See [Error Codes Reference](./errors.md) for complete error documentation.

## Next Steps

- [WebSocket Documentation](./websockets.md)
- [Error Codes Reference](./errors.md)
- Return to [API Overview](./README.md)
