# API Reference

> **Complete API documentation for the Local LLM Research Agent**

This section documents the programmatic interfaces for integrating with and extending the Local LLM Research Agent.

---

## Table of Contents

- [Core Components](#core-components)
- [Agent API](agent.md) - ResearchAgent class and factory functions
- [Providers API](providers.md) - LLM provider implementations
- [MCP Client API](mcp-client.md) - MCP server integration
- [Models API](models.md) - Data models and schemas
- [Utilities API](utilities.md) - Helper functions and utilities

---

## Core Components

### Quick Reference

| Component | Module | Primary Class | Purpose |
|-----------|--------|---------------|---------|
| Agent | `src.agent.research_agent` | `ResearchAgent` | Main chat agent |
| Providers | `src.providers` | `LLMProvider` | LLM backends |
| MCP Client | `src.mcp.client` | `MCPClientManager` | MCP server management |
| Models | `src.models` | Various | Data structures |
| Config | `src.utils.config` | `Settings` | Configuration |

---

## Installation for Development

```python
# Install with dev dependencies
uv sync --dev

# Or with pip
pip install -e ".[dev]"
```

---

## Basic Usage

### Creating an Agent

```python
from src.agent.research_agent import ResearchAgent, create_research_agent

# Method 1: Using factory function (recommended)
agent = create_research_agent(
    provider_type="ollama",  # or "foundry_local"
    readonly=True,
)

# Method 2: Direct instantiation
agent = ResearchAgent(
    provider_type="ollama",
    ollama_host="http://localhost:11434",
    ollama_model="qwen2.5:7b-instruct",
    readonly=True,
    cache_enabled=True,
)
```

### Chat Interaction

```python
import asyncio

async def main():
    agent = create_research_agent()
    
    # Simple chat
    response = await agent.chat("What tables are in the database?")
    print(response)
    
    # Streaming chat
    async for chunk in agent.chat_stream("Describe the Users table"):
        print(chunk, end="", flush=True)
    
    # Get conversation history
    history = agent.get_history()
    print(f"Turns: {agent.turn_count}")

asyncio.run(main())
```

### Using Providers Directly

```python
from src.providers import create_provider, ProviderType
from src.providers.ollama import OllamaProvider
from src.providers.foundry import FoundryLocalProvider

# Using factory
provider = create_provider(provider_type="ollama")

# Direct instantiation
ollama = OllamaProvider(
    model_name="qwen2.5:7b-instruct",
    host="http://localhost:11434",
)

foundry = FoundryLocalProvider(
    model_name="phi-4",
    endpoint="http://127.0.0.1:55588",
)

# Check connection
status = await provider.check_connection()
print(f"Available: {status.available}")
print(f"Model: {status.model_name}")
```

### Accessing Configuration

```python
from src.utils.config import settings, reload_settings

# Read settings
print(f"Provider: {settings.llm_provider}")
print(f"Database: {settings.sql_database_name}")
print(f"Auth Type: {settings.sql_auth_type}")

# Check Azure SQL
if settings.is_azure_sql:
    print("Connected to Azure SQL Database")

# Reload settings (after .env changes)
reload_settings()
```

---

## API Documentation Files

| File | Description |
|------|-------------|
| [agent.md](agent.md) | ResearchAgent class, factory functions, context managers |
| [providers.md](providers.md) | OllamaProvider, FoundryLocalProvider, base classes |
| [mcp-client.md](mcp-client.md) | MCPClientManager, MSSQL server configuration |
| [models.md](models.md) | ChatMessage, Conversation, SQLResult models |
| [utilities.md](utilities.md) | Config, logging, caching, rate limiting, health checks |

---

## Type Safety

The API uses comprehensive type hints and Pydantic models:

```python
from src.models.chat import ChatMessage, Conversation
from src.providers.base import ProviderStatus, ProviderType

# All models are Pydantic BaseModel
message = ChatMessage(
    role="user",
    content="What tables exist?",
)

# Enums for type safety
provider_type = ProviderType.OLLAMA
```

---

## Error Handling

```python
from src.agent.research_agent import ResearchAgentError, ProviderConnectionError

try:
    response = await agent.chat("Query something")
except ProviderConnectionError as e:
    print(f"Provider unavailable: {e}")
except ResearchAgentError as e:
    print(f"Agent error: {e}")
```

---

## Async Support

All I/O operations are async:

```python
import asyncio
from src.agent.research_agent import ResearchAgent

async def example():
    agent = ResearchAgent()
    
    # Async chat
    response = await agent.chat("Hello")
    
    # Async streaming
    async for chunk in agent.chat_stream("Tell me more"):
        print(chunk, end="")
    
    # Async provider check
    status = await agent.provider.check_connection()

# Run with asyncio
asyncio.run(example())
```

---

## Extension Points

### Custom Providers

```python
from src.providers.base import LLMProvider, ProviderStatus, ProviderType

class CustomProvider(LLMProvider):
    @property
    def provider_type(self) -> ProviderType:
        return ProviderType.OLLAMA  # or create new enum
    
    def get_model(self):
        # Return Pydantic AI compatible model
        pass
    
    async def check_connection(self) -> ProviderStatus:
        # Implement connection check
        pass
```

### Custom MCP Servers

```python
from src.mcp.client import MCPClientManager

# Add custom MCP server configuration
manager = MCPClientManager()
# Configure additional servers via mcp_config.json
```

---

*See individual API documentation files for detailed reference.*
