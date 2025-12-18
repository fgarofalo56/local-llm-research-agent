# Providers API Reference

> **LLM Provider implementations for Ollama and Foundry Local**

---

## Module: `src.providers`

### Provider Types

```python
from src.providers import ProviderType

class ProviderType(str, Enum):
    OLLAMA = "ollama"
    FOUNDRY_LOCAL = "foundry_local"
```

---

### Factory Function

#### `create_provider(provider_type, model_name, **kwargs) -> LLMProvider`

Create a provider instance based on type.

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `provider_type` | `str \| ProviderType \| None` | From settings | Provider type |
| `model_name` | `str \| None` | From settings | Model name |
| `**kwargs` | `dict` | - | Provider-specific options |

**Returns:** `LLMProvider` instance

**Example:**

```python
from src.providers import create_provider

# Use settings defaults
provider = create_provider()

# Specify provider type
provider = create_provider(provider_type="ollama")

# Full configuration
provider = create_provider(
    provider_type="foundry_local",
    model_name="phi-4",
)
```

---

## Base Classes

### `LLMProvider` (Abstract)

Base class for all LLM providers.

```python
from src.providers.base import LLMProvider

class LLMProvider(ABC):
    @property
    @abstractmethod
    def provider_type(self) -> ProviderType: ...
    
    @property
    @abstractmethod
    def model_name(self) -> str: ...
    
    @property
    @abstractmethod
    def endpoint(self) -> str: ...
    
    @abstractmethod
    def get_model(self) -> OpenAIModel: ...
    
    @abstractmethod
    async def check_connection(self) -> ProviderStatus: ...
    
    @abstractmethod
    async def list_models(self) -> list[str]: ...
    
    @abstractmethod
    def supports_tool_calling(self) -> bool: ...
```

---

### `ProviderStatus`

Status information from connection check.

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

**Example:**

```python
status = await provider.check_connection()

if status.available:
    print(f"Connected to {status.provider_type.value}")
    print(f"Model: {status.model_name}")
    print(f"Version: {status.version}")
else:
    print(f"Error: {status.error}")
```

---

## OllamaProvider

### Module: `src.providers.ollama`

Provider for Ollama local LLM inference.

```python
from src.providers.ollama import OllamaProvider

class OllamaProvider(LLMProvider):
    def __init__(
        self,
        model_name: str = "qwen2.5:7b-instruct",
        host: str = "http://localhost:11434",
        timeout: int = 120,
    )
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `model_name` | `str` | `"qwen2.5:7b-instruct"` | Ollama model name |
| `host` | `str` | `"http://localhost:11434"` | Ollama server URL |
| `timeout` | `int` | `120` | Request timeout (seconds) |

**Example:**

```python
from src.providers.ollama import OllamaProvider

provider = OllamaProvider(
    model_name="llama3.1:8b",
    host="http://localhost:11434",
)

# Check connection
status = await provider.check_connection()
print(f"Available: {status.available}")

# List models
models = await provider.list_models()
print(f"Models: {models}")

# Get Pydantic AI model
model = provider.get_model()
```

---

### Tool-Capable Models

Models known to support tool calling:

```python
from src.providers.ollama import OLLAMA_TOOL_CAPABLE_MODELS

# ['qwen2.5', 'qwen2', 'llama3.1', 'llama3.2', 'llama3.3',
#  'mistral', 'mixtral', 'command-r', 'firefunction',
#  'hermes', 'nous-hermes']
```

**Check support:**

```python
if provider.supports_tool_calling():
    print("Model supports tool calling")
else:
    print("Warning: Model may not support tools")
```

---

### Properties

| Property | Type | Description |
|----------|------|-------------|
| `provider_type` | `ProviderType` | Always `ProviderType.OLLAMA` |
| `model_name` | `str` | Configured model name |
| `endpoint` | `str` | OpenAI-compatible endpoint (with `/v1`) |

```python
print(provider.endpoint)  # http://localhost:11434/v1
```

---

## FoundryLocalProvider

### Module: `src.providers.foundry`

Provider for Microsoft Foundry Local inference.

```python
from src.providers.foundry import FoundryLocalProvider

class FoundryLocalProvider(LLMProvider):
    def __init__(
        self,
        model_name: str = "phi-4",
        endpoint: str | None = None,
        api_key: str = "",
        timeout: int = 120,
    )
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `model_name` | `str` | `"phi-4"` | Model alias |
| `endpoint` | `str \| None` | `"http://127.0.0.1:53760"` | API endpoint |
| `api_key` | `str` | `""` | API key (optional for local) |
| `timeout` | `int` | `120` | Request timeout (seconds) |

**Example:**

```python
from src.providers.foundry import FoundryLocalProvider

provider = FoundryLocalProvider(
    model_name="phi-4",
    endpoint="http://127.0.0.1:53760",
)

# Check connection
status = await provider.check_connection()

# List available models
models = await provider.list_models()
```

---

### SDK Auto-Start

Start Foundry Local automatically using the SDK:

```python
from src.providers.foundry import FoundryLocalProvider

# Requires: pip install foundry-local-sdk
provider = FoundryLocalProvider.start_with_sdk("phi-4")

# Provider is now configured with running instance
status = await provider.check_connection()
```

**Requirements:**
- `foundry-local-sdk` package installed
- First run downloads model (~2-4GB depending on model)

---

### Tool-Capable Models

```python
from src.providers.foundry import FOUNDRY_TOOL_CAPABLE_MODELS

# ['phi-4', 'phi-3', 'mistral', 'llama', 'qwen']
```

---

### Properties

| Property | Type | Description |
|----------|------|-------------|
| `provider_type` | `ProviderType` | Always `ProviderType.FOUNDRY_LOCAL` |
| `model_name` | `str` | Configured model alias |
| `endpoint` | `str` | OpenAI-compatible endpoint (with `/v1`) |

```python
print(provider.endpoint)  # http://127.0.0.1:53760/v1
```

---

## Common Patterns

### Provider Selection at Runtime

```python
from src.providers import create_provider, ProviderType

def get_provider(use_foundry: bool = False):
    if use_foundry:
        return create_provider(provider_type=ProviderType.FOUNDRY_LOCAL)
    return create_provider(provider_type=ProviderType.OLLAMA)
```

### Connection Retry

```python
import asyncio

async def wait_for_provider(provider, max_attempts=10):
    for attempt in range(max_attempts):
        status = await provider.check_connection()
        if status.available:
            return True
        print(f"Waiting for provider... ({attempt + 1}/{max_attempts})")
        await asyncio.sleep(2)
    return False
```

### Provider Health Check

```python
async def check_all_providers():
    results = {}
    
    for ptype in ProviderType:
        try:
            provider = create_provider(provider_type=ptype)
            status = await provider.check_connection()
            results[ptype.value] = {
                "available": status.available,
                "model": status.model_name,
                "error": status.error,
            }
        except Exception as e:
            results[ptype.value] = {
                "available": False,
                "error": str(e),
            }
    
    return results
```

### Fallback Provider

```python
async def get_available_provider():
    """Try Ollama first, fall back to Foundry Local."""
    
    # Try Ollama
    ollama = create_provider(provider_type="ollama")
    status = await ollama.check_connection()
    if status.available:
        return ollama
    
    # Try Foundry Local
    foundry = create_provider(provider_type="foundry_local")
    status = await foundry.check_connection()
    if status.available:
        return foundry
    
    raise RuntimeError("No LLM provider available")
```

---

## Error Handling

```python
from src.providers.base import ProviderStatus

async def safe_check(provider) -> ProviderStatus:
    try:
        return await provider.check_connection()
    except Exception as e:
        return ProviderStatus(
            available=False,
            provider_type=provider.provider_type,
            model_name=None,
            endpoint=provider.endpoint,
            error=str(e),
        )
```

---

*See also: [Agent API](agent.md), [Ollama Guide](../guides/ollama.md), [Foundry Local Guide](../guides/foundry-local.md)*
