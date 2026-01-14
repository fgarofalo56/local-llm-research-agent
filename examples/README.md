# Examples

This directory contains usage examples demonstrating various features of the Local LLM Research Agent.

## Quick Start Examples

### Basic Chat
```bash
uv run python examples/basic_chat.py
```
Simple chat interaction with the agent.

### SQL Query Example
```bash
uv run python examples/sql_query_example.py
```
Demonstrates querying SQL Server data through natural language.

### Streaming Example
```bash
uv run python examples/streaming_example.py
```
Shows how to use streaming responses for real-time output.

### Multi-Tool Example
```bash
uv run python examples/multi_tool_example.py
```
Demonstrates using multiple MCP tools in a single session.

## Feature-Specific Examples

| Example | Description |
|---------|-------------|
| `rag_search_example.py` | RAG knowledge base search and retrieval |
| `multi_mcp_example.py` | Working with multiple MCP servers |
| `redis_cache_example.py` | Redis caching integration |
| `vector_store_factory_example.py` | Vector store abstraction usage |
| `config_service_example.py` | Configuration service patterns |
| `query_profiler_example.py` | Query performance profiling |
| `websocket_manager_example.py` | WebSocket connection management |
| `retry_example.py` | Retry logic and error handling |

## Prerequisites

1. **Docker containers running:**
   ```bash
   docker-compose -f docker/docker-compose.yml --env-file .env up -d
   ```

2. **Ollama running with model:**
   ```bash
   ollama serve
   ollama pull qwen3:30b
   ```

3. **MCP servers configured:**
   - Check `mcp_config.json` has enabled servers
   - At minimum need `mssql` server for database queries

## Related Documentation

- Main docs: `../README.md`
- Agent architecture: `../CLAUDE.md`
- API docs: `../docs/api/`
- Test suite: `../tests/`
