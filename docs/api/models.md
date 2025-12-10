# Models API Reference

> **Data models and schemas used throughout the application**

---

## Module: `src.models`

### Chat Models

#### `src.models.chat`

##### `ChatMessage`

Represents a single chat message.

```python
from src.models.chat import ChatMessage

class ChatMessage(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: dict[str, Any] = Field(default_factory=dict)
```

**Example:**

```python
message = ChatMessage(
    role="user",
    content="What tables are in the database?",
)
print(message.model_dump())
```

##### `Conversation`

Represents a full conversation with history.

```python
from src.models.chat import Conversation

class Conversation(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    messages: list[ChatMessage] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    metadata: dict[str, Any] = Field(default_factory=dict)
    total_duration_ms: int = 0
```

**Methods:**

| Method | Description |
|--------|-------------|
| `add_message(role, content)` | Add a message to conversation |
| `get_messages()` | Get all messages as dicts |
| `clear()` | Clear all messages |
| `turn_count` | Property: number of user turns |

**Example:**

```python
conversation = Conversation()
conversation.add_message("user", "Hello")
conversation.add_message("assistant", "Hi there!")

print(f"Turns: {conversation.turn_count}")
print(f"Messages: {len(conversation.messages)}")
```

##### `ChatResponse`

Response from agent with metadata.

```python
from src.models.chat import ChatResponse

class ChatResponse(BaseModel):
    content: str
    duration_ms: int = 0
    tool_calls: list[str] = Field(default_factory=list)
    cached: bool = False
    model: str | None = None
```

---

### SQL Result Models

#### `src.models.sql_results`

##### `SQLResult`

Represents SQL query results.

```python
from src.models.sql_results import SQLResult

class SQLResult(BaseModel):
    columns: list[str]
    rows: list[list[Any]]
    row_count: int
    execution_time_ms: int = 0
    query: str | None = None
```

**Example:**

```python
result = SQLResult(
    columns=["id", "name", "email"],
    rows=[
        [1, "Alice", "alice@example.com"],
        [2, "Bob", "bob@example.com"],
    ],
    row_count=2,
)

# Convert to pandas DataFrame
df = result.to_dataframe()
```

##### `TableInfo`

Information about a database table.

```python
class TableInfo(BaseModel):
    name: str
    schema_name: str = "dbo"
    columns: list[ColumnInfo] = Field(default_factory=list)
    row_count: int | None = None
```

##### `ColumnInfo`

Information about a table column.

```python
class ColumnInfo(BaseModel):
    name: str
    data_type: str
    nullable: bool = True
    is_primary_key: bool = False
    default_value: str | None = None
```

---

### Provider Models

#### `src.providers.base`

##### `ProviderType`

Enum of supported provider types.

```python
from src.providers.base import ProviderType

class ProviderType(str, Enum):
    OLLAMA = "ollama"
    FOUNDRY_LOCAL = "foundry_local"
```

##### `ProviderStatus`

Status from provider health check.

```python
from src.providers.base import ProviderStatus

@dataclass
class ProviderStatus:
    available: bool
    provider_type: ProviderType
    model_name: str | None
    endpoint: str
    version: str | None = None
    error: str | None = None
```

---

### Configuration Models

#### `src.utils.config`

##### `SqlAuthType`

SQL Server authentication types.

```python
from src.utils.config import SqlAuthType

class SqlAuthType(str, Enum):
    SQL_AUTH = "sql"
    WINDOWS_AUTH = "windows"
    AZURE_AD_INTERACTIVE = "azure_ad_interactive"
    AZURE_AD_SERVICE_PRINCIPAL = "azure_ad_service_principal"
    AZURE_AD_MANAGED_IDENTITY = "azure_ad_managed_identity"
    AZURE_AD_DEFAULT = "azure_ad_default"
```

##### `Settings`

Application settings (Pydantic Settings).

```python
from src.utils.config import settings, Settings

# Access settings
print(settings.llm_provider)
print(settings.ollama_model)
print(settings.sql_auth_type)

# Check properties
if settings.is_azure_sql:
    print("Using Azure SQL")

if settings.requires_azure_auth:
    print("Azure AD authentication required")
```

**Key Settings:**

| Setting | Type | Description |
|---------|------|-------------|
| `llm_provider` | `str` | "ollama" or "foundry_local" |
| `ollama_host` | `str` | Ollama server URL |
| `ollama_model` | `str` | Ollama model name |
| `foundry_endpoint` | `str` | Foundry Local endpoint |
| `foundry_model` | `str` | Foundry Local model |
| `sql_server_host` | `str` | SQL Server hostname |
| `sql_database_name` | `str` | Database name |
| `sql_auth_type` | `SqlAuthType` | Authentication type |
| `cache_enabled` | `bool` | Response caching |
| `rate_limit_enabled` | `bool` | Rate limiting |

---

### Cache Models

#### `src.utils.cache`

##### `CacheStats`

Cache statistics.

```python
from src.utils.cache import CacheStats

@dataclass
class CacheStats:
    hits: int
    misses: int
    size: int
    max_size: int
    hit_rate: float
```

---

### Rate Limiter Models

#### `src.utils.rate_limiter`

##### `RateLimitStats`

Rate limiting statistics.

```python
from src.utils.rate_limiter import RateLimitStats

@dataclass
class RateLimitStats:
    total_requests: int
    rejected_requests: int
    current_window_requests: int
    window_reset_time: datetime | None
```

---

### Health Models

#### `src.utils.health`

##### `HealthStatus`

Health check status enum.

```python
from src.utils.health import HealthStatus

class HealthStatus(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
```

##### `ComponentHealth`

Health check result for a component.

```python
from src.utils.health import ComponentHealth

@dataclass
class ComponentHealth:
    name: str
    status: HealthStatus
    message: str = ""
    latency_ms: float | None = None
    details: dict[str, Any] = field(default_factory=dict)
```

##### `SystemHealth`

Overall system health.

```python
from src.utils.health import SystemHealth

@dataclass
class SystemHealth:
    status: HealthStatus
    components: list[ComponentHealth]
    timestamp: datetime
```

---

## Type Patterns

### Using Models with Type Safety

```python
from src.models.chat import ChatMessage, Conversation
from src.providers.base import ProviderStatus, ProviderType

def process_message(msg: ChatMessage) -> str:
    return f"[{msg.role}] {msg.content}"

def check_provider(status: ProviderStatus) -> bool:
    if status.available:
        print(f"Using {status.provider_type.value}")
        return True
    print(f"Error: {status.error}")
    return False
```

### Serialization

All Pydantic models support JSON serialization:

```python
from src.models.chat import ChatMessage

message = ChatMessage(role="user", content="Hello")

# To dict
data = message.model_dump()

# To JSON string
json_str = message.model_dump_json()

# From dict
msg2 = ChatMessage.model_validate(data)

# From JSON
msg3 = ChatMessage.model_validate_json(json_str)
```

---

*See also: [Agent API](agent.md), [Utilities API](utilities.md)*
