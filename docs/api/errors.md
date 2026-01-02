# Error Codes Reference

Complete reference of all error codes returned by the Local LLM Research Analytics API, with solutions and examples.

## HTTP Status Codes

| Code | Status | Description |
|------|--------|-------------|
| 200 | OK | Request succeeded |
| 201 | Created | Resource created successfully |
| 204 | No Content | Request succeeded, no content to return |
| 400 | Bad Request | Invalid request parameters or format |
| 401 | Unauthorized | Authentication required (not implemented yet) |
| 403 | Forbidden | Access denied |
| 404 | Not Found | Resource not found |
| 405 | Method Not Allowed | HTTP method not allowed for endpoint |
| 409 | Conflict | Resource already exists or conflict |
| 413 | Payload Too Large | Request body or file exceeds maximum size |
| 422 | Unprocessable Entity | Request validation failed |
| 500 | Internal Server Error | Server error |
| 503 | Service Unavailable | Service temporarily unavailable |

---

## Error Response Format

All errors follow this standard format:

```json
{
  "detail": "Human-readable error message"
}
```

Some endpoints may include additional context:

```json
{
  "detail": "Error message",
  "error_code": "ERROR_CODE",
  "error_details": "Additional information about the error"
}
```

---

## Document Errors

### 413 - File Too Large

**When:** Uploaded file exceeds maximum size

```json
{
  "detail": "File too large. Maximum size is 50MB"
}
```

**Causes:**
- File size exceeds `MAX_UPLOAD_SIZE_MB` setting
- Default limit is 50MB

**Solutions:**
1. Check file size: `ls -lh file.pdf`
2. Compress or split file into smaller parts
3. Increase `MAX_UPLOAD_SIZE_MB` in `.env`

**Example Fix:**

```bash
# Check file size
ls -lh research.pdf

# Compress PDF
pdftk research.pdf cat output research-compressed.pdf

# Upload compressed version
curl -X POST http://localhost:8000/api/documents \
  -F "file=@research-compressed.pdf"
```

---

### 400 - Unsupported File Type

**When:** File format not supported

```json
{
  "detail": "Unsupported file type. Supported: ['.pdf', '.docx']"
}
```

**Causes:**
- File extension not in supported list
- Correct extension but corrupted file

**Solutions:**
1. Convert file to supported format (PDF or DOCX)
2. Check file extension is correct
3. Verify file is not corrupted

**Supported Formats:**
- PDF (`.pdf`)
- Word Documents (`.docx`)

**Example Fix:**

```bash
# Convert DOC to DOCX
libreoffice --headless --convert-to docx document.doc

# Convert TXT to PDF
enscript -B -p output.pdf input.txt

# Upload
curl -X POST http://localhost:8000/api/documents -F "file=@output.pdf"
```

---

### 404 - Document Not Found

**When:** Document ID doesn't exist

```json
{
  "detail": "Document not found"
}
```

**Causes:**
- Invalid document ID
- Document deleted
- Wrong database/environment

**Solutions:**
1. List documents to find correct ID: `GET /api/documents`
2. Verify document wasn't deleted
3. Check you're accessing correct API instance

**Example:**

```bash
# List documents
curl http://localhost:8000/api/documents

# Get specific document (replace 999 with actual ID)
curl http://localhost:8000/api/documents/1
```

---

### 400 - Cannot Reprocess Document

**When:** Document status doesn't allow reprocessing

```json
{
  "detail": "Cannot reprocess document with status 'pending'"
}
```

**Valid Statuses for Reprocessing:**
- `pending` - Can reprocess
- `processing` - Can reprocess (stuck document)
- `failed` - Can reprocess
- `completed` - Can reprocess

**Invalid Statuses:**
- Any others

**Solutions:**
1. Check document status: `GET /api/documents/{id}`
2. Use `/recover-stuck` endpoint for processing issues
3. Wait for document to reach valid status

**Example:**

```bash
# Check status
curl http://localhost:8000/api/documents/1 | jq '.processing_status'

# Reprocess failed document
curl -X POST http://localhost:8000/api/documents/1/reprocess

# Recover stuck documents
curl -X POST http://localhost:8000/api/documents/recover-stuck
```

---

## Conversation Errors

### 404 - Conversation Not Found

**When:** Conversation ID doesn't exist

```json
{
  "detail": "Conversation not found"
}
```

**Solutions:**
1. List conversations: `GET /api/conversations`
2. Create new conversation: `POST /api/conversations`

**Example:**

```bash
# List conversations
curl http://localhost:8000/api/conversations

# Create new conversation
curl -X POST http://localhost:8000/api/conversations \
  -H "Content-Type: application/json" \
  -d '{"title": "New Chat"}'
```

---

## Query Errors

### 400 - Query Contains Forbidden Keyword

**When:** Query attempts dangerous operation

```json
{
  "detail": "Query contains forbidden keyword: DROP"
}
```

**Security Restrictions:**
- Only SELECT statements allowed
- Forbidden keywords: DROP, DELETE, TRUNCATE, INSERT, UPDATE, ALTER, CREATE, EXEC, EXECUTE

**Solutions:**
1. Use only SELECT statements
2. Contact admin if you need write access
3. Use MCP tools for write operations

**Valid Query:**

```bash
curl -X POST http://localhost:8000/api/queries/execute \
  -H "Content-Type: application/json" \
  -d '{"query": "SELECT * FROM Projects LIMIT 10"}'
```

**Invalid Query:**

```bash
# This will fail - DELETE not allowed
curl -X POST http://localhost:8000/api/queries/execute \
  -H "Content-Type: application/json" \
  -d '{"query": "DELETE FROM Projects"}'
```

---

### 400 - Only SELECT Allowed

**When:** Query doesn't start with SELECT

```json
{
  "detail": "Only SELECT statements are allowed for direct execution"
}
```

**Solutions:**
1. Use SELECT to query data
2. Use MCP tools for write operations
3. Check query syntax

---

### 404 - Query Not Found

**When:** Query ID doesn't exist

```json
{
  "detail": "Query not found"
}
```

**Solutions:**
1. List saved queries: `GET /api/queries/saved`
2. Create new saved query: `POST /api/queries/saved`

---

## Dashboard Errors

### 404 - Dashboard Not Found

**When:** Dashboard ID doesn't exist

```json
{
  "detail": "Dashboard not found"
}
```

**Solutions:**
1. List dashboards: `GET /api/dashboards`
2. Create new dashboard: `POST /api/dashboards`

---

### 404 - Widget Not Found

**When:** Widget ID doesn't exist

```json
{
  "detail": "Widget not found"
}
```

**Solutions:**
1. List widgets: `GET /api/dashboards/{dashboard_id}`
2. Create new widget: `POST /api/dashboards/{dashboard_id}/widgets`

---

## MCP Server Errors

### 503 - MCP Server Unavailable

**When:** MCP server not responding

```json
{
  "detail": "MCP server not available"
}
```

**Causes:**
- Server process crashed
- Connection refused
- Port not listening

**Solutions:**
1. Check MCP server status: `GET /api/health/services`
2. Restart MCP server
3. Check server logs
4. Verify configuration

**Example:**

```bash
# Check health
curl http://localhost:8000/api/health/services | jq '.mcp_servers'

# List servers
curl http://localhost:8000/api/mcp-servers

# Restart via Docker
docker-compose restart mssql-mcp  # If using Docker
```

---

### 400 - Invalid MCP Server Configuration

**When:** Server configuration invalid

```json
{
  "detail": "Invalid MCP server configuration"
}
```

**Causes:**
- Missing required fields
- Invalid JSON in environment variables
- Missing command or URL

**Solutions:**
1. Check MCP configuration in `mcp_config.json`
2. Validate JSON syntax
3. Ensure command path exists

**Valid Configuration:**

```json
{
  "id": "mssql",
  "name": "MSSQL MCP Server",
  "type": "stdio",
  "command": "node",
  "args": ["/path/to/mssql/index.js"],
  "enabled": true
}
```

---

## Settings & Configuration Errors

### 400 - Invalid Theme Configuration

**When:** Theme configuration invalid

```json
{
  "detail": "Invalid theme configuration"
}
```

**Causes:**
- Invalid JSON in config
- Missing required theme fields
- Invalid color values

**Solutions:**
1. Validate JSON: `jq . theme.json`
2. Check required fields
3. Use valid hex color codes

**Valid Theme:**

```json
{
  "name": "custom",
  "display_name": "Custom Theme",
  "config": "{\"primary\": \"#0066cc\", \"background\": \"#ffffff\"}"
}
```

---

## Alert Errors

### 404 - Alert Not Found

**When:** Alert ID doesn't exist

```json
{
  "detail": "Alert not found"
}
```

**Solutions:**
1. List alerts: `GET /api/alerts`
2. Create new alert: `POST /api/alerts`

---

### 400 - Invalid Alert Condition

**When:** Condition not recognized

```json
{
  "detail": "Invalid alert condition"
}
```

**Valid Conditions:**
- `greater_than` - Trigger when value > threshold
- `less_than` - Trigger when value < threshold
- `equals` - Trigger when value = threshold
- `changes` - Trigger when value changes

**Example:**

```bash
curl -X POST http://localhost:8000/api/alerts \
  -H "Content-Type: application/json" \
  -d '{
    "name": "High Activity",
    "query": "SELECT COUNT(*) FROM Projects",
    "condition": "greater_than",
    "threshold": 10
  }'
```

---

## Scheduled Query Errors

### 404 - Scheduled Query Not Found

**When:** Query ID doesn't exist

```json
{
  "detail": "Scheduled query not found"
}
```

---

### 400 - Invalid Cron Expression

**When:** Cron expression format invalid

```json
{
  "detail": "Invalid cron expression"
}
```

**Valid Cron Format:** `minute hour day month weekday`

**Examples:**
- `0 8 * * *` - 8 AM daily
- `0 0 1 * *` - 1st day of month
- `0 9 * * 1-5` - 9 AM weekdays
- `*/15 * * * *` - Every 15 minutes

**Solutions:**
1. Validate cron expression: https://crontab.guru/
2. Test expression before saving

---

## Agent Errors

### 503 - Vector Store Unavailable

**When:** RAG vector store not available

```json
{
  "detail": "Vector store not available"
}
```

**Causes:**
- No documents indexed
- Vector store service down
- Database connection failed

**Solutions:**
1. Upload documents: `POST /api/documents`
2. Check health: `GET /api/health`
3. Check database connection

---

### 400 - Agent Error

**When:** Agent processing fails

```json
{
  "detail": "Agent processing error details"
}
```

**Common Causes:**
- LLM provider unavailable
- Invalid message format
- Memory/resource constraints
- Tool execution failed

**Solutions:**
1. Check provider health: `GET /api/health`
2. Verify message format
3. Check server logs
4. Reduce message complexity

---

## Superset Integration Errors

### 503 - Cannot Connect to Superset

**When:** Superset service unavailable

```json
{
  "detail": "Cannot connect to Superset: Connection refused"
}
```

**Causes:**
- Superset not running
- Wrong URL configuration
- Network connectivity issue

**Solutions:**
1. Check Superset status: `curl http://localhost:8088`
2. Verify URL in `.env`: `SUPERSET_URL=http://localhost:8088`
3. Restart Superset service

**Example:**

```bash
# Start Superset
docker-compose up -d superset

# Check health
curl http://localhost:8000/api/superset/health
```

---

### 500 - Failed to Authenticate with Superset

**When:** Superset credentials invalid

```json
{
  "detail": "Failed to authenticate with Superset"
}
```

**Causes:**
- Wrong username/password
- User account disabled
- Superset API changed

**Solutions:**
1. Verify credentials in `.env`:
   ```
   SUPERSET_ADMIN_USER=admin
   SUPERSET_ADMIN_PASSWORD=LocalLLM@2024!
   ```
2. Check user exists in Superset
3. Reset password via Superset UI

---

## Common HTTP Errors

### 422 - Unprocessable Entity

**When:** Request validation fails

```json
{
  "detail": [
    {
      "loc": ["body", "query"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

**Solutions:**
1. Check required fields are present
2. Validate field types
3. Review request schema

**Example:**

```bash
# Missing required 'query' field
curl -X POST http://localhost:8000/api/queries/execute \
  -H "Content-Type: application/json" \
  -d '{}'

# Error response shows missing field

# Correct request
curl -X POST http://localhost:8000/api/queries/execute \
  -H "Content-Type: application/json" \
  -d '{"query": "SELECT 1"}'
```

---

### 500 - Internal Server Error

**When:** Server encounters unexpected error

```json
{
  "detail": "Internal server error"
}
```

**Solutions:**
1. Check server logs
2. Verify all services are running
3. Try simpler request
4. Contact support with request details

**Debugging:**

```bash
# View API logs
docker logs local-agent-api

# Check health
curl http://localhost:8000/api/health

# Test basic endpoint
curl http://localhost:8000
```

---

## Error Codes by Endpoint

### Documents

| Endpoint | Error Code | Status | Message |
|----------|-----------|--------|---------|
| POST /api/documents | 413 | File Too Large | File exceeds max size |
| POST /api/documents | 400 | Unsupported Type | File type not supported |
| GET /api/documents/{id} | 404 | Not Found | Document not found |
| POST /api/documents/{id}/reprocess | 400 | Invalid Status | Cannot reprocess |
| POST /api/documents/{id}/reprocess | 404 | File Missing | Document file not found |

### Conversations

| Endpoint | Error Code | Status | Message |
|----------|-----------|--------|---------|
| GET /api/conversations/{id} | 404 | Not Found | Conversation not found |
| POST /api/conversations/{id}/messages | 404 | Not Found | Conversation not found |

### Queries

| Endpoint | Error Code | Status | Message |
|----------|-----------|--------|---------|
| POST /api/queries/execute | 400 | Forbidden Keyword | Query forbidden |
| POST /api/queries/execute | 400 | Not SELECT | Only SELECT allowed |
| GET /api/queries/saved/{id} | 404 | Not Found | Query not found |

---

## Debugging Tips

### 1. Enable Debug Logging

```bash
# Set debug mode
export DEBUG=true

# Restart API
uv run uvicorn src.api.main:app --reload
```

### 2. Check Service Health

```bash
# All services
curl http://localhost:8000/api/health

# Specific services
curl http://localhost:8000/api/health/services
```

### 3. View Logs

```bash
# API logs
docker logs -f local-agent-api

# Docker Compose logs
docker-compose logs -f api

# Streaming logs
tail -f logs/api.log
```

### 4. Test Basic Connectivity

```bash
# Test API running
curl http://localhost:8000

# Test database
docker exec local-agent-mssql sqlcmd -S . -U sa -P "LocalLLM@2024!" -Q "SELECT 1"

# Test Redis
redis-cli ping

# Test Ollama
curl http://localhost:11434/api/tags
```

### 5. Use Browser DevTools

```javascript
// In browser console
fetch('http://localhost:8000/api/health')
  .then(r => r.json())
  .then(data => console.log(JSON.stringify(data, null, 2)))
  .catch(e => console.error(e))
```

---

## Getting Help

If you encounter an error not documented here:

1. Check server logs: `docker logs local-agent-api`
2. Search issue tracker: GitHub Issues
3. Review documentation: `/docs/`
4. Enable debug logging and try again
5. Post details to support with:
   - Full error message
   - Request URL and body
   - Server logs
   - Reproduction steps

---

## Error Recovery

### Connection Lost

```javascript
// Implement automatic reconnection
class RetryableRequest {
  static async execute(fn, maxRetries = 3) {
    for (let i = 0; i < maxRetries; i++) {
      try {
        return await fn();
      } catch (e) {
        if (i === maxRetries - 1) throw e;
        await new Promise(r => setTimeout(r, Math.pow(2, i) * 1000));
      }
    }
  }
}

// Usage
const response = await RetryableRequest.execute(() =>
  fetch('http://localhost:8000/api/documents')
);
```

### Service Temporarily Unavailable

```python
import time
import httpx

def fetch_with_retry(url: str, max_retries: int = 5):
    for i in range(max_retries):
        try:
            response = httpx.get(url, timeout=5)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 503:
                wait_time = 2 ** i  # Exponential backoff
                print(f"Service unavailable, retrying in {wait_time}s")
                time.sleep(wait_time)
            else:
                raise
```

---

See [API Overview](./README.md) for general information and [Complete Reference](./reference.md) for endpoint details.
