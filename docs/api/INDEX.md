# API Documentation Index

Complete index of all API documentation for the Local LLM Research Analytics API.

## Quick Links

### For Getting Started
- **[API Overview & Quick Start](./README.md)** - Start here for introduction and common use cases
- **[Interactive Docs](http://localhost:8000/docs)** - Swagger UI (live testing)
- **[API Schema](http://localhost:8000/openapi.json)** - OpenAPI 3.0 specification

### For Implementation
- **[Complete Endpoint Reference](./reference.md)** - Detailed documentation of all 60+ endpoints
- **[WebSocket Protocol](./websockets.md)** - Real-time communication with examples
- **[Error Codes & Solutions](./errors.md)** - All error codes with troubleshooting

### For Development
- **[Agent API](./agent.md)** - Research agent implementation
- **[Providers API](./providers.md)** - LLM provider integrations
- **[MCP Client API](./mcp-client.md)** - MCP server integration
- **[RAG Pipeline](./rag.md)** - Document retrieval and embeddings
- **[Data Models](./models.md)** - Pydantic data structures
- **[Utilities](./utilities.md)** - Helper functions and configuration
- **[FastAPI Backend](./fastapi.md)** - Backend infrastructure

## Documentation by Category

### API Endpoints (60+ total)

| Category | Count | Reference |
|----------|-------|-----------|
| Health & Monitoring | 4 | [Link](./reference.md#health-endpoints) |
| Documents & RAG | 8 | [Link](./reference.md#document-endpoints) |
| Conversations & Chat | 7 | [Link](./reference.md#conversation-endpoints) |
| Queries & SQL | 8 | [Link](./reference.md#query-endpoints) |
| Dashboards | 7 | [Link](./reference.md#dashboard-endpoints) |
| Agent & AI | 2 | [Link](./reference.md#agent-endpoints) |
| MCP Servers | 4 | [Link](./reference.md#mcp-server-endpoints) |
| Settings | 4 | [Link](./reference.md#settings-endpoints) |
| Alerts | 5 | [Link](./reference.md#alert-endpoints) |
| Scheduled Queries | 5 | [Link](./reference.md#scheduled-query-endpoints) |
| Superset Integration | 3 | [Link](./reference.md#superset-endpoints) |

### WebSocket Endpoints

Located in: [WebSocket Protocol Documentation](./websockets.md)

1. **Agent Chat WebSocket** - `ws://localhost:8000/ws/agent/{conversation_id}`
2. **Alert Notifications WebSocket** - `ws://localhost:8000/ws/alerts`

## Error Codes & Troubleshooting

Located in: [Error Codes Reference](./errors.md)

- HTTP status codes (8 types)
- Document errors (4 types)
- Query errors (3 types)
- Service errors (3 types)
- 30+ detailed error codes with solutions
- Debugging and recovery patterns

## API Usage Examples

### Basic Examples

Health check:
```bash
curl http://localhost:8000/api/health
```

Create conversation:
```bash
curl -X POST http://localhost:8000/api/conversations \
  -H "Content-Type: application/json" \
  -d '{"title": "Analysis"}'
```

Execute query:
```bash
curl -X POST http://localhost:8000/api/queries/execute \
  -H "Content-Type: application/json" \
  -d '{"query": "SELECT * FROM Projects LIMIT 10"}'
```

### Complete Workflows

See [Common Use Cases](./README.md#common-use-cases) for:
- Chat with context
- Upload and search documents
- Execute and save queries
- Create dashboards

## File Organization

```
docs/api/
├── INDEX.md              # This file
├── README.md             # Quick start (290 lines)
├── reference.md          # All endpoints (1,820 lines)
├── websockets.md         # WebSocket guide (754 lines)
├── errors.md             # Error codes (860 lines)
├── agent.md              # Agent API (415 lines)
├── providers.md          # Providers (399 lines)
├── mcp-client.md         # MCP client (394 lines)
├── models.md             # Data models (379 lines)
├── utilities.md          # Utilities (428 lines)
├── fastapi.md            # FastAPI (582 lines)
└── rag.md                # RAG pipeline (699 lines)
```

**Total: 7,020 lines of documentation**

## Quick Navigation

| Need | Document |
|------|----------|
| Getting started | [README.md](./README.md) |
| Specific endpoint | [reference.md](./reference.md) |
| Real-time features | [websockets.md](./websockets.md) |
| Error help | [errors.md](./errors.md) |
| Agent details | [agent.md](./agent.md) |
| Test and debug | [errors.md#troubleshooting](./errors.md#troubleshooting) |

## Performance Tips

- Use WebSockets for real-time
- Batch messages for efficiency
- Enable Redis caching
- Monitor health endpoints
- Use pagination for large data

See [WebSocket Performance](./websockets.md#performance-considerations)

## Support

- **API Health:** http://localhost:8000/api/health
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
- **OpenAPI:** http://localhost:8000/openapi.json

---

**API Version:** 2.2.0 | **Updated:** December 18, 2025
**Navigation:** [Overview](./README.md) | [Endpoints](./reference.md) | [WebSockets](./websockets.md) | [Errors](./errors.md)
