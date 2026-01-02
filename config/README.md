# Configuration Management

This directory contains YAML-based configuration files for the Local LLM Research Agent application.

## Overview

The application uses a centralized `ConfigService` that supports:

- **Multi-environment configuration** (default, development, production)
- **Environment variable substitution** with defaults
- **Dot notation access** for nested values
- **Type conversion** (boolean, integer, float, string)
- **Hot reload** in development mode
- **Configuration validation**

## Configuration Files

| File | Purpose |
|------|---------|
| `default.yaml` | Base configuration with sensible defaults |
| `development.yaml` | Development overrides (debug mode, short cache TTL, etc.) |
| `production.yaml` | Production overrides (security, performance tuning, etc.) |

## Environment Selection

The active environment is determined by the `ENVIRONMENT` environment variable:

```bash
# Development (default)
ENVIRONMENT=development

# Production
ENVIRONMENT=production
```

## Configuration Structure

### Application Settings

```yaml
app:
  name: "Local LLM Research Agent"
  debug: false           # Override per environment
  log_level: "INFO"      # INFO, DEBUG, WARNING, ERROR
```

### Database Configuration

```yaml
database:
  sample:               # SQL Server 2022 - Sample database
    host: "${SQL_SERVER_HOST:-localhost}"
    port: "${SQL_SERVER_PORT:-1433}"
    name: "${SQL_DATABASE_NAME:-ResearchAnalytics}"
    username: "${SQL_USERNAME:-sa}"
    password: "${SQL_PASSWORD}"
    trust_cert: "${SQL_TRUST_SERVER_CERTIFICATE:-true}"
    encrypt: "${SQL_ENCRYPT:-true}"

  backend:              # SQL Server 2025 - Backend database
    host: "${BACKEND_DB_HOST:-localhost}"
    port: "${BACKEND_DB_PORT:-1434}"
    name: "${BACKEND_DB_NAME:-LLM_BackEnd}"
    username: "${BACKEND_DB_USERNAME}"
    password: "${BACKEND_DB_PASSWORD}"
    trust_cert: "${BACKEND_DB_TRUST_CERT:-true}"
```

### LLM Provider Configuration

```yaml
ollama:
  host: "${OLLAMA_HOST:-http://localhost:11434}"
  model: "${OLLAMA_MODEL:-qwen3:30b}"
  embedding_model: "${EMBEDDING_MODEL:-nomic-embed-text}"

foundry:
  endpoint: "${FOUNDRY_ENDPOINT:-http://127.0.0.1:53760}"
  model: "${FOUNDRY_MODEL:-phi-4}"
  auto_start: "${FOUNDRY_AUTO_START:-false}"

llm_provider: "${LLM_PROVIDER:-ollama}"  # ollama or foundry_local
```

### Cache Configuration

```yaml
cache:
  enabled: "${CACHE_ENABLED:-true}"
  ttl_seconds: "${CACHE_TTL_SECONDS:-3600}"
  max_size: "${CACHE_MAX_SIZE:-1000}"
```

### Vector Store Configuration

```yaml
vector_store:
  type: "${VECTOR_STORE_TYPE:-mssql}"  # mssql or redis
  dimensions: "${VECTOR_DIMENSIONS:-768}"

redis:
  url: "${REDIS_URL:-redis://localhost:6379}"
```

### RAG Configuration

```yaml
rag:
  chunk_size: "${CHUNK_SIZE:-500}"
  chunk_overlap: "${CHUNK_OVERLAP:-50}"
  top_k: "${RAG_TOP_K:-5}"
```

## Environment Variable Substitution

Configuration values support environment variable substitution with two formats:

### Required Variable

```yaml
password: "${SQL_PASSWORD}"
```

If `SQL_PASSWORD` is not set, the value will be an empty string and a warning will be logged.

### Variable with Default

```yaml
host: "${SQL_SERVER_HOST:-localhost}"
```

If `SQL_SERVER_HOST` is not set, the default value `localhost` will be used.

## Type Conversion

Values are automatically converted to appropriate types:

- **Boolean**: `true`, `false`, `yes`, `no`, `1`, `0` (case-insensitive)
- **Integer**: Numeric values without decimal points
- **Float**: Numeric values with decimal points
- **String**: Everything else

Examples:

```yaml
cache:
  enabled: "true"           # Converted to boolean: True
  ttl_seconds: "3600"       # Converted to integer: 3600
  max_size: "1000"          # Converted to integer: 1000
```

## Usage

### Basic Usage

```python
from src.services.config_service import get_config

# Get singleton instance
config = get_config()

# Access configuration using dot notation
app_name = config.get("app.name")
db_host = config.get("database.sample.host")

# Access with default value
custom_value = config.get("custom.setting", default="default_value")
```

### Environment-Specific Configuration

```python
import os
from src.services.config_service import ConfigService

# Set environment
os.environ["ENVIRONMENT"] = "production"

# Reset instance to load new environment
ConfigService.reset_instance()
config = ConfigService.get_instance()

# Check environment
print(f"Environment: {config.environment}")
print(f"Debug Mode: {config.get('app.debug')}")
```

### Validation

```python
from src.services.config_service import get_config

config = get_config()

# Validate configuration
errors = config.validate()
if errors:
    for error in errors:
        print(f"Error: {error}")
else:
    print("Configuration is valid!")
```

### Hot Reload (Development Only)

```python
from src.services.config_service import get_config

config = get_config()

# Modify environment variables
os.environ["CACHE_TTL_SECONDS"] = "7200"

# Reload configuration
config.reload()

# Access updated value
print(config.get("cache.ttl_seconds"))  # 7200
```

## Environment-Specific Overrides

### Development Environment

```yaml
# config/development.yaml
app:
  debug: true
  log_level: "DEBUG"

cache:
  ttl_seconds: 300        # 5 minutes
  max_size: 100

rate_limit:
  enabled: false

mcp:
  debug: true
```

### Production Environment

```yaml
# config/production.yaml
app:
  debug: false
  log_level: "INFO"

cache:
  ttl_seconds: 7200       # 2 hours
  max_size: 5000

rate_limit:
  enabled: true
  rpm: 100
  burst: 20

mcp:
  debug: false
  readonly: true          # Enable readonly mode for safety
```

## Best Practices

1. **Use environment variables for secrets**: Never commit sensitive values to YAML files
2. **Provide sensible defaults**: Use `${VAR:-default}` format for optional settings
3. **Validate configuration**: Call `config.validate()` on application startup
4. **Use production environment in deployment**: Set `ENVIRONMENT=production`
5. **Leverage hot reload in development**: Use `config.reload()` to pick up changes

## Migration from Settings Class

The existing `Settings` class in `src/utils/config.py` is being gradually replaced by `ConfigService`:

```python
# Old approach (Pydantic Settings)
from src.utils.config import settings
db_host = settings.sql_server_host

# New approach (ConfigService)
from src.services.config_service import get_config
config = get_config()
db_host = config.get("database.sample.host")
```

Both approaches will coexist during the transition period. New features should use `ConfigService`.

## Examples

See `examples/config_service_example.py` for comprehensive usage examples.

## Troubleshooting

### Missing Environment Variables

If you see warnings about missing environment variables:

```
WARNING: Environment variable not found: SQL_PASSWORD
```

Solutions:
1. Set the environment variable in your `.env` file
2. Export it in your shell: `export SQL_PASSWORD=YourPassword`
3. Provide a default in the YAML: `"${SQL_PASSWORD:-default_password}"`

### Configuration Validation Errors

Run validation to identify issues:

```python
from src.services.config_service import get_config

config = get_config()
errors = config.validate()
for error in errors:
    print(error)
```

### Environment Not Loading

Ensure `ENVIRONMENT` is set before importing ConfigService:

```python
import os
os.environ["ENVIRONMENT"] = "production"

from src.services.config_service import get_config
config = get_config()
```

## Testing

ConfigService includes comprehensive test coverage in `tests/test_config_service.py`:

```bash
# Run ConfigService tests
uv run pytest tests/test_config_service.py -v

# Run all configuration tests
uv run pytest tests/ -k "config" -v
```
