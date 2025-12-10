# Utilities API Reference

> **Helper functions and utilities for configuration, logging, caching, and more**

---

## Configuration

### Module: `src.utils.config`

#### `settings`

Global settings instance.

```python
from src.utils.config import settings

# Access any setting
print(settings.ollama_host)
print(settings.sql_database_name)
print(settings.cache_enabled)
```

#### `get_settings() -> Settings`

Get the current settings instance.

```python
from src.utils.config import get_settings

s = get_settings()
print(s.llm_provider)
```

#### `reload_settings() -> Settings`

Reload settings from environment (useful after .env changes).

```python
from src.utils.config import reload_settings

# After modifying .env
settings = reload_settings()
```

#### Key Properties

```python
# Check if using Azure SQL
if settings.is_azure_sql:
    print("Connected to Azure SQL Database")

# Check if Azure auth required
if settings.requires_azure_auth:
    print("Using Azure AD authentication")

# Get display-friendly auth type
print(settings.get_auth_display())  # e.g., "SQL Auth (sa)"

# Get MCP environment variables
env = settings.get_mcp_env()
```

---

## Logging

### Module: `src.utils.logger`

#### `get_logger(name: str) -> Logger`

Get a structured logger instance.

```python
from src.utils.logger import get_logger

logger = get_logger(__name__)

# Structured logging
logger.info("operation_started", user="alice", action="query")
logger.debug("sql_executed", query="SELECT * FROM Users", rows=10)
logger.error("connection_failed", host="localhost", error="timeout")
```

#### `configure_logging(level: str, format: str)`

Configure global logging settings.

```python
from src.utils.logger import configure_logging

configure_logging(level="DEBUG", format="json")
```

---

## Caching

### Module: `src.utils.cache`

#### `ResponseCache[T]`

Generic response cache with TTL support.

```python
from src.utils.cache import ResponseCache

cache: ResponseCache[str] = ResponseCache(
    max_size=100,
    ttl_seconds=3600,  # 1 hour
    enabled=True,
)

# Store value
cache.set("key1", "value1")

# Retrieve value
value = cache.get("key1")  # Returns "value1" or None

# Check if exists
if cache.has("key1"):
    print("Found in cache")

# Get stats
stats = cache.get_stats()
print(f"Hit rate: {stats.hit_rate:.1%}")

# Clear cache
cache.clear()

# Invalidate by pattern
count = cache.invalidate("user_*")
```

#### `get_response_cache(**kwargs) -> ResponseCache`

Factory function to create configured cache.

```python
from src.utils.cache import get_response_cache

cache = get_response_cache(
    max_size=200,
    ttl_seconds=7200,
    enabled=True,
)
```

#### `CacheStats`

Cache statistics dataclass.

```python
from src.utils.cache import CacheStats

@dataclass
class CacheStats:
    hits: int
    misses: int
    size: int
    max_size: int
    hit_rate: float  # Computed property
```

---

## Rate Limiting

### Module: `src.utils.rate_limiter`

#### `RateLimiter`

Token bucket rate limiter.

```python
from src.utils.rate_limiter import RateLimiter

limiter = RateLimiter(
    requests_per_minute=60,
    burst_size=10,
    enabled=True,
)

# Acquire permission (blocks if rate limited)
await limiter.acquire()

# Try to acquire without blocking
if limiter.try_acquire():
    # Proceed with request
    pass

# Get stats
stats = limiter.get_stats()
print(f"Total requests: {stats.total_requests}")
print(f"Rejected: {stats.rejected_requests}")

# Reset stats
limiter.reset_stats()

# Enable/disable at runtime
limiter.enabled = False
```

#### `get_rate_limiter(**kwargs) -> RateLimiter`

Factory function to create configured rate limiter.

```python
from src.utils.rate_limiter import get_rate_limiter

limiter = get_rate_limiter(
    requests_per_minute=30,
    enabled=True,
)
```

---

## Health Checks

### Module: `src.utils.health`

#### `check_ollama_health() -> ComponentHealth`

Check Ollama server health.

```python
from src.utils.health import check_ollama_health

health = await check_ollama_health()
print(f"Status: {health.status.value}")
print(f"Message: {health.message}")
```

#### `check_foundry_health() -> ComponentHealth`

Check Foundry Local health.

```python
from src.utils.health import check_foundry_health

health = await check_foundry_health()
if health.status == HealthStatus.HEALTHY:
    print("Foundry Local is running")
```

#### `check_database_health() -> ComponentHealth`

Check SQL Server database health.

```python
from src.utils.health import check_database_health

health = await check_database_health()
print(f"Latency: {health.latency_ms}ms")
```

#### `check_system_health() -> SystemHealth`

Check all components and return system health.

```python
from src.utils.health import check_system_health, HealthStatus

system = await check_system_health()

print(f"Overall: {system.status.value}")
for component in system.components:
    icon = "" if component.status == HealthStatus.HEALTHY else ""
    print(f"  {icon} {component.name}: {component.message}")
```

---

## History Management

### Module: `src.utils.history`

#### `ConversationHistory`

Manages conversation persistence.

```python
from src.utils.history import ConversationHistory
from src.models.chat import Conversation

history = ConversationHistory()

# Save conversation
conversation = Conversation()
conversation.add_message("user", "Hello")
conversation.add_message("assistant", "Hi!")

session_id = history.save(conversation)
print(f"Saved as: {session_id}")

# List saved sessions
sessions = history.list_sessions()
for session in sessions:
    print(f"{session.id}: {session.created_at}")

# Load a session
loaded = history.load(session_id)
print(f"Loaded {len(loaded.messages)} messages")

# Delete a session
history.delete(session_id)
```

---

## Export

### Module: `src.utils.export`

#### `export_conversation(conversation, format, path)`

Export conversation to file.

```python
from src.utils.export import export_conversation
from src.models.chat import Conversation

conversation = Conversation()
# ... add messages ...

# Export to JSON
export_conversation(conversation, format="json", path="chat.json")

# Export to CSV
export_conversation(conversation, format="csv", path="chat.csv")

# Export to Markdown
export_conversation(conversation, format="markdown", path="chat.md")
```

#### Supported Formats

| Format | Extension | Description |
|--------|-----------|-------------|
| `json` | `.json` | Full conversation with metadata |
| `csv` | `.csv` | Messages as rows |
| `markdown` | `.md` | Formatted for reading |

---

## MCP Configuration

### Module: `src.mcp.mssql_config`

#### `MSSQLConfig`

MSSQL MCP server configuration.

```python
from src.mcp.mssql_config import MSSQLConfig

config = MSSQLConfig(
    server_name="localhost",
    database_name="ResearchAnalytics",
    auth_type=SqlAuthType.SQL_AUTH,
    username="sa",
    password="password",
    readonly=True,
)

# Get environment for subprocess
env = config.get_env()
```

---

## Patterns

### Conditional Caching

```python
from src.utils.cache import get_response_cache

# Enable cache only in production
import os
cache = get_response_cache(
    enabled=os.getenv("ENVIRONMENT") == "production",
    max_size=500,
)
```

### Health Check Integration

```python
from src.utils.health import check_system_health, HealthStatus

async def ensure_healthy():
    health = await check_system_health()
    if health.status == HealthStatus.UNHEALTHY:
        unhealthy = [c for c in health.components 
                     if c.status == HealthStatus.UNHEALTHY]
        raise RuntimeError(f"Unhealthy: {[c.name for c in unhealthy]}")
```

### Logging Best Practices

```python
from src.utils.logger import get_logger

logger = get_logger(__name__)

# Use structured fields
logger.info("request_started", 
    method="chat",
    user_id="abc123",
    cache_enabled=True,
)

# Log errors with context
try:
    result = await some_operation()
except Exception as e:
    logger.error("operation_failed",
        error=str(e),
        error_type=type(e).__name__,
    )
    raise
```

---

*See also: [Agent API](agent.md), [Models API](models.md)*
