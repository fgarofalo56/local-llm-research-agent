# Chat Methods Testing Examples

This directory contains test scripts demonstrating the three chat methods:
1. `chat()` - Basic text response with caching
2. `chat_stream()` - Streaming chunks for UX
3. `chat_with_details()` - Full metadata response

## 🚀 Quick Start

### Full Featured Test (Recommended)
```bash
uv run python examples/test_chat_methods.py
```
Beautiful Rich-formatted output showing all three methods with:
- Streaming visualization
- Caching demonstration
- Metadata tables
- Summary comparison

### Quick Test (Minimal)
```bash
uv run python examples/test_chat_quick.py
```
Simple console output without fancy formatting. Good for:
- Quick verification
- Debugging
- CI/CD pipelines

### Individual Method Tests
```bash
# Test just chat()
uv run python examples/test_individual_methods.py chat

# Test just chat_stream()
uv run python examples/test_individual_methods.py stream

# Test just chat_with_details()
uv run python examples/test_individual_methods.py details

# Test all three
uv run python examples/test_individual_methods.py
```

## 📋 Prerequisites

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

## 🎯 What Each Test Shows

### test_chat_methods.py
- ✅ Session management (one context for all methods)
- ✅ Caching effectiveness (speed comparison)
- ✅ Streaming visualization (typing effect)
- ✅ Metadata extraction (tokens, duration, model)
- ✅ Summary table comparing all three

**Output example:**
```
=======================================================================
Method 1: chat()
Simple text response with caching
=======================================================================

→ Sending: What tables are in the database?
✓ Response (1250ms):
┌────────────────────────────────────────────────┐
│ The database contains: Researchers, Projects...│
└────────────────────────────────────────────────┘

→ Sending SAME message again (testing cache):
✓ Cached response (5ms) - 250x faster!

=======================================================================
Method 2: chat_stream()
AsyncIterator yielding text chunks
=======================================================================

→ Sending: List all researchers
✓ Streaming response:
──────────────────────────────────────────────────────────────────
Here are the researchers in the database: [chunks appear gradually]
──────────────────────────────────────────────────────────────────

✓ Streaming complete:
  • Duration: 1100ms
  • Chunks: 55
  • Total length: 1234 chars
  • Tokens: 450 (input: 25, output: 425)
```

### test_chat_quick.py
Simple text output - perfect for CI/CD or quick verification:
```
============================================================
Quick Chat Methods Test
============================================================

1. Creating agent...
2. Entering agent context...
   ✓ MCP sessions established

============================================================
TEST 1: chat() - Basic response
============================================================
Response: The database contains the following tables...
Length: 850 chars

✓ All tests complete!
```

### test_individual_methods.py
Test methods in isolation - good for debugging specific issues:
```bash
# Example: Debug just streaming
uv run python examples/test_individual_methods.py stream

=== Testing chat_stream() ===

Streaming query results:

------------------------------------------------------------
Department 1: AI Research
Department 2: Data Science
...
------------------------------------------------------------

Chunks received: 45
Stats: {'token_usage': TokenUsage(total=380, input=20, output=360)}

✓ Test complete
```

## 🔍 Verifying Session Management

All tests demonstrate proper session management:

```
>>> ENTERING AGENT CONTEXT (MCP sessions established) <<<
✓ MCP sessions established and ready

[Multiple chat method calls here - all reuse the same session]

>>> EXITING AGENT CONTEXT (MCP sessions closed) <<<
```

**What to look for:**
- ✅ "MCP sessions established" appears ONCE at start
- ✅ No additional session establishment between messages
- ✅ "MCP sessions closed" appears ONCE at end

**Red flags (bug not fixed):**
- ❌ Multiple "sessions established" messages
- ❌ POST requests on every message (check logs)
- ❌ Slow performance between messages

## 🐛 Debugging

### Enable Debug Logging
```bash
# In .env
LOG_LEVEL=DEBUG

# Then run tests and grep for POST requests
uv run python examples/test_chat_methods.py 2>&1 | grep "POST"
```

### Check Session IDs
```bash
# Look for Mcp-Session-Id headers in logs
uv run python examples/test_chat_methods.py 2>&1 | grep -i "session-id"

# Should see SAME session ID reused across all messages
```

### Network Inspection
```bash
# Monitor HTTP traffic (requires Wireshark or tcpdump)
# Look for POST to http://localhost:8051/mcp
# Should see: 1 POST at startup, then tool calls with session ID
```

## 📊 Performance Expectations

**With proper session management (after fix):**
| Method | First Call | Subsequent Calls |
|--------|------------|------------------|
| `chat()` | 800-1500ms | 1-10ms (cached) |
| `chat_stream()` | 800-1500ms | 800-1500ms (no cache) |
| `chat_with_details()` | 800-1500ms | 800-1500ms (no cache) |

**With broken session management (before fix):**
| Method | Every Call |
|--------|------------|
| All methods | +200-500ms overhead from reconnection |

## 🎓 Learning Examples

### How to Use chat() in Your Code
```python
from src.agent.core import ResearchAgent

agent = ResearchAgent(mcp_servers=["mssql"])

async with agent:
    # Simple API endpoint
    response = await agent.chat("What tables exist?")
    return {"answer": response}
```

### How to Use chat_stream() in CLI
```python
async with agent:
    # Interactive chat loop
    user_input = input("You: ")
    print("Agent: ", end="", flush=True)
    
    async for chunk in agent.chat_stream(user_input):
        print(chunk, end="", flush=True)
    
    print()  # New line after streaming
```

### How to Use chat_with_details() for Monitoring
```python
async with agent:
    response = await agent.chat_with_details("Complex query")
    
    # Log metrics
    logger.info(
        "agent_query",
        duration_ms=response.duration_ms,
        tokens=response.token_usage.total_tokens,
        success=response.success,
        model=response.model
    )
    
    return response.content
```

## 🆘 Troubleshooting

### "Agent not initialized" error
```bash
# Check MCP servers are configured and enabled
cat mcp_config.json | jq '.mcpServers'

# Verify Docker containers running
docker ps | grep mssql
```

### Slow responses
```bash
# Check Ollama is running
curl http://localhost:11434/api/tags

# Verify model is pulled
ollama list | grep qwen3
```

### No caching in chat()
```bash
# Check cache is enabled in .env
grep CACHE .env

# Verify message is EXACT match (case-sensitive)
# Cache only works for identical messages
```

## 📝 Notes

- All tests use **local Ollama** for inference (no external APIs)
- Tests connect to **local SQL Server** in Docker
- First run may be slow (model loading, database connection)
- Caching only works with `chat()` method
- Streaming is simulated (20 char chunks) - not true LLM streaming

## 🔗 Related Documentation

- Main docs: `../CLAUDE.md`
- Session bug fix: `../MCP_SESSION_BUG_FIX.md`
- Agent source: `../src/agent/core.py`
- CLI source: `../src/cli/chat.py`
