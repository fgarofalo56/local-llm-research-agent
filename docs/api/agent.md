# Agent API Reference

> **ResearchAgent class and factory functions**

---

## Module: `src.agent.research_agent`

### Classes

#### `ResearchAgent`

Main agent class for SQL Server data analytics research.

```python
class ResearchAgent:
    def __init__(
        self,
        provider: LLMProvider | None = None,
        provider_type: ProviderType | str | None = None,
        model_name: str | None = None,
        readonly: bool | None = None,
        minimal_prompt: bool = False,
        cache_enabled: bool | None = None,
        explain_mode: bool = False,
        # Legacy parameters (backwards compatible)
        ollama_host: str | None = None,
        ollama_model: str | None = None,
    )
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `provider` | `LLMProvider \| None` | `None` | Pre-configured provider instance |
| `provider_type` | `ProviderType \| str \| None` | `None` | Provider type ("ollama" or "foundry_local") |
| `model_name` | `str \| None` | `None` | Model name/alias |
| `readonly` | `bool \| None` | From settings | Enable read-only mode |
| `minimal_prompt` | `bool` | `False` | Use minimal system prompt |
| `cache_enabled` | `bool \| None` | From settings | Enable response caching |
| `explain_mode` | `bool` | `False` | Enable query explanations |
| `ollama_host` | `str \| None` | `None` | (Legacy) Ollama server URL |
| `ollama_model` | `str \| None` | `None` | (Legacy) Ollama model name |

**Example:**

```python
# Basic usage
agent = ResearchAgent()

# With specific provider
agent = ResearchAgent(
    provider_type="ollama",
    model_name="llama3.1:8b",
)

# With all options
agent = ResearchAgent(
    provider_type="foundry_local",
    model_name="phi-4",
    readonly=True,
    cache_enabled=True,
    explain_mode=True,
)

# Legacy compatibility
agent = ResearchAgent(
    ollama_host="http://localhost:11434",
    ollama_model="qwen2.5:7b-instruct",
)
```

---

### Instance Methods

#### `async chat(message: str) -> str`

Send a message and get a response.

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `message` | `str` | User message |

**Returns:** `str` - Agent response

**Raises:** `ResearchAgentError` - If chat fails

**Example:**

```python
response = await agent.chat("What tables are in the database?")
print(response)
```

---

#### `async chat_stream(message: str) -> AsyncIterator[str]`

Send a message and stream the response.

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `message` | `str` | User message |

**Yields:** `str` - Response chunks

**Raises:** `ResearchAgentError` - If streaming fails

**Example:**

```python
async for chunk in agent.chat_stream("Describe the Users table"):
    print(chunk, end="", flush=True)
print()  # Newline after streaming
```

---

#### `async chat_with_details(message: str) -> ChatResponse`

Send a message and get detailed response with metadata.

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `message` | `str` | User message |

**Returns:** `ChatResponse` - Response with timing and tool call info

**Example:**

```python
result = await agent.chat_with_details("Count researchers")
print(f"Response: {result.content}")
print(f"Duration: {result.duration_ms}ms")
print(f"Tools used: {result.tool_calls}")
```

---

#### `clear_history() -> None`

Clear conversation history.

**Example:**

```python
agent.clear_history()
assert agent.turn_count == 0
```

---

#### `get_history() -> list[dict[str, str]]`

Get conversation history.

**Returns:** List of message dictionaries with `role` and `content` keys.

**Example:**

```python
history = agent.get_history()
for msg in history:
    print(f"{msg['role']}: {msg['content'][:50]}...")
```

---

### Properties

#### `turn_count: int`

Number of conversation turns (user messages sent).

```python
print(f"Conversation has {agent.turn_count} turns")
```

#### `readonly: bool`

Whether agent is in read-only mode.

```python
if agent.readonly:
    print("Agent cannot modify data")
```

#### `cache_enabled: bool`

Whether response caching is enabled.

```python
if agent.cache_enabled:
    print("Responses are being cached")
```

#### `rate_limit_enabled: bool`

Whether rate limiting is enabled. Can be set at runtime.

```python
agent.rate_limit_enabled = True
```

---

### Cache Methods

#### `get_cache_stats() -> CacheStats`

Get cache statistics.

**Returns:** `CacheStats` with hits, misses, size, etc.

```python
stats = agent.get_cache_stats()
print(f"Cache hits: {stats.hits}")
print(f"Cache misses: {stats.misses}")
print(f"Hit rate: {stats.hit_rate:.1%}")
```

#### `clear_cache() -> None`

Clear all cached responses.

```python
agent.clear_cache()
```

#### `invalidate_cache(pattern: str | None = None) -> int`

Invalidate cache entries matching pattern.

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `pattern` | `str \| None` | Optional pattern to match |

**Returns:** Number of invalidated entries

```python
count = agent.invalidate_cache("users")
print(f"Invalidated {count} cache entries")
```

---

### Rate Limiting Methods

#### `get_rate_limit_stats() -> RateLimitStats`

Get rate limiting statistics.

**Returns:** `RateLimitStats` with request counts

```python
stats = agent.get_rate_limit_stats()
print(f"Total requests: {stats.total_requests}")
print(f"Rejected: {stats.rejected_requests}")
```

#### `reset_rate_limit_stats() -> None`

Reset rate limiting statistics.

```python
agent.reset_rate_limit_stats()
```

---

### Factory Functions

#### `create_research_agent(**kwargs) -> ResearchAgent`

Factory function to create a configured agent.

**Parameters:** Same as `ResearchAgent.__init__`

**Returns:** Configured `ResearchAgent` instance

**Example:**

```python
from src.agent.research_agent import create_research_agent

# Default configuration from .env
agent = create_research_agent()

# Override specific settings
agent = create_research_agent(
    provider_type="foundry_local",
    readonly=True,
)
```

---

### Context Manager

#### `ResearchAgentContext`

Async context manager for agent lifecycle.

```python
from src.agent.research_agent import ResearchAgentContext

async with ResearchAgentContext() as agent:
    response = await agent.chat("Hello")
    # Agent resources cleaned up automatically
```

---

### Exceptions

#### `ResearchAgentError`

Base exception for agent errors.

```python
from src.agent.research_agent import ResearchAgentError

try:
    await agent.chat("query")
except ResearchAgentError as e:
    print(f"Agent error: {e}")
```

#### `ProviderConnectionError`

Raised when provider connection fails.

```python
from src.agent.research_agent import ProviderConnectionError

try:
    await agent.chat("query")
except ProviderConnectionError as e:
    print(f"Provider unavailable: {e}")
```

---

### Legacy Alias

#### `OllamaConnectionError`

Deprecated alias for `ProviderConnectionError`.

```python
# Deprecated - use ProviderConnectionError instead
from src.agent.research_agent import OllamaConnectionError
```

---

## Usage Patterns

### Basic Chat Loop

```python
async def chat_loop():
    agent = create_research_agent()
    
    while True:
        user_input = input("You: ")
        if user_input.lower() in ("quit", "exit"):
            break
        
        response = await agent.chat(user_input)
        print(f"Agent: {response}")

asyncio.run(chat_loop())
```

### With Error Handling

```python
async def safe_chat(agent, message):
    try:
        return await agent.chat(message)
    except ProviderConnectionError:
        return "Sorry, the LLM provider is not available."
    except ResearchAgentError as e:
        return f"Error: {e}"
```

### Streaming with Progress

```python
async def stream_with_progress(agent, message):
    print("Agent: ", end="")
    full_response = []
    
    async for chunk in agent.chat_stream(message):
        print(chunk, end="", flush=True)
        full_response.append(chunk)
    
    print()  # Newline
    return "".join(full_response)
```

---

*See also: [Providers API](providers.md), [Models API](models.md)*
