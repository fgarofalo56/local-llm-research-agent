# MCP Client API Reference

> **MCP (Model Context Protocol) server integration and management**

---

## Overview

The MCP client manages connections to MCP servers that provide tools to the agent. The primary MCP server is the MSSQL MCP Server for SQL Server database access.

---

## Module: `src.mcp.client`

### `MCPClientManager`

Manages MCP server connections and configuration.

```python
from src.mcp.client import MCPClientManager

class MCPClientManager:
    def __init__(self, config_path: str | None = None):
        """
        Initialize MCP client manager.
        
        Args:
            config_path: Path to mcp_config.json (optional)
        """
```

**Example:**

```python
manager = MCPClientManager()

# Get MSSQL MCP server instance
mssql_server = manager.get_mssql_server()

# Use with agent
from pydantic_ai import Agent
agent = Agent(
    model=model,
    toolsets=[mssql_server],
)
```

---

### Methods

#### `get_mssql_server() -> MCPServerStdio`

Get the configured MSSQL MCP server instance.

**Returns:** `MCPServerStdio` - Pydantic AI MCP server instance

**Example:**

```python
manager = MCPClientManager()
server = manager.get_mssql_server()

# Server can be used as agent toolset
agent = Agent(model=model, toolsets=[server])
```

#### `get_server(name: str) -> MCPServerStdio | None`

Get a specific MCP server by name.

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `name` | `str` | Server name from config |

**Returns:** `MCPServerStdio` or `None` if not found

**Example:**

```python
# Get custom server
server = manager.get_server("custom-mcp")
if server:
    agent = Agent(model=model, toolsets=[server])
```

#### `list_servers() -> list[str]`

List configured MCP server names.

**Returns:** List of server names

**Example:**

```python
servers = manager.list_servers()
print(f"Configured servers: {servers}")
# ['mssql', 'filesystem', ...]
```

---

## Module: `src.mcp.mssql_config`

### `MSSQLConfig`

Configuration for MSSQL MCP server.

```python
from src.mcp.mssql_config import MSSQLConfig
from src.utils.config import SqlAuthType

class MSSQLConfig:
    def __init__(
        self,
        server_name: str,
        database_name: str,
        auth_type: SqlAuthType = SqlAuthType.SQL_AUTH,
        username: str = "",
        password: str = "",
        port: int = 1433,
        encrypt: bool = True,
        trust_server_certificate: bool = True,
        readonly: bool = False,
        azure_tenant_id: str = "",
        azure_client_id: str = "",
        azure_client_secret: str = "",
    )
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `server_name` | `str` | Required | SQL Server hostname |
| `database_name` | `str` | Required | Database name |
| `auth_type` | `SqlAuthType` | `SQL_AUTH` | Authentication type |
| `username` | `str` | `""` | SQL username |
| `password` | `str` | `""` | SQL password |
| `port` | `int` | `1433` | SQL Server port |
| `encrypt` | `bool` | `True` | Encrypt connection |
| `trust_server_certificate` | `bool` | `True` | Trust server cert |
| `readonly` | `bool` | `False` | Read-only mode |
| `azure_tenant_id` | `str` | `""` | Azure AD tenant |
| `azure_client_id` | `str` | `""` | Azure AD client |
| `azure_client_secret` | `str` | `""` | Azure AD secret |

---

### Methods

#### `get_env() -> dict[str, str]`

Get environment variables for MCP server subprocess.

**Returns:** Dictionary of environment variables

**Example:**

```python
config = MSSQLConfig(
    server_name="localhost",
    database_name="ResearchAnalytics",
    auth_type=SqlAuthType.SQL_AUTH,
    username="sa",
    password="password",
)

env = config.get_env()
# {
#     "SERVER_NAME": "localhost",
#     "DATABASE_NAME": "ResearchAnalytics",
#     "AUTH_TYPE": "sql",
#     "SQL_USERNAME": "sa",
#     "SQL_PASSWORD": "password",
#     ...
# }
```

#### `validate() -> bool`

Validate configuration completeness.

**Returns:** `True` if valid

**Raises:** `ValueError` if invalid

**Example:**

```python
try:
    config.validate()
except ValueError as e:
    print(f"Invalid config: {e}")
```

---

### Authentication Examples

#### SQL Authentication

```python
config = MSSQLConfig(
    server_name="localhost",
    database_name="ResearchAnalytics",
    auth_type=SqlAuthType.SQL_AUTH,
    username="sa",
    password="LocalLLM@2024!",
)
```

#### Windows Authentication

```python
config = MSSQLConfig(
    server_name="sqlserver.company.local",
    database_name="Analytics",
    auth_type=SqlAuthType.WINDOWS_AUTH,
)
```

#### Azure AD Interactive

```python
config = MSSQLConfig(
    server_name="myserver.database.windows.net",
    database_name="mydb",
    auth_type=SqlAuthType.AZURE_AD_INTERACTIVE,
    encrypt=True,
    trust_server_certificate=False,
)
```

#### Azure AD Service Principal

```python
config = MSSQLConfig(
    server_name="myserver.database.windows.net",
    database_name="mydb",
    auth_type=SqlAuthType.AZURE_AD_SERVICE_PRINCIPAL,
    azure_tenant_id="tenant-guid",
    azure_client_id="client-guid",
    azure_client_secret="secret",
)
```

#### Azure Managed Identity

```python
config = MSSQLConfig(
    server_name="myserver.database.windows.net",
    database_name="mydb",
    auth_type=SqlAuthType.AZURE_AD_MANAGED_IDENTITY,
    azure_client_id="user-assigned-identity-id",  # Optional
)
```

---

## MCP Configuration File

### `mcp_config.json`

The MCP configuration file defines server connections:

```json
{
  "mcpServers": {
    "mssql": {
      "command": "node",
      "args": ["${MCP_MSSQL_PATH}"],
      "env": {
        "SERVER_NAME": "${SQL_SERVER_HOST}",
        "DATABASE_NAME": "${SQL_DATABASE_NAME}",
        "TRUST_SERVER_CERTIFICATE": "${SQL_TRUST_SERVER_CERTIFICATE}",
        "READONLY": "${MCP_MSSQL_READONLY}"
      }
    }
  }
}
```

### Environment Variable Expansion

Variables are expanded from the environment:

| Syntax | Description |
|--------|-------------|
| `${VAR}` | Required variable |
| `${VAR:-default}` | Variable with default |

---

## MSSQL MCP Tools Reference

The MSSQL MCP Server provides these tools:

### Schema Discovery

| Tool | Description | Read-Only |
|------|-------------|-----------|
| `list_tables` | List all tables in database | Yes |
| `describe_table` | Get table schema details | Yes |

### Data Access

| Tool | Description | Read-Only |
|------|-------------|-----------|
| `read_data` | Query data with conditions | Yes |

### Data Modification (Write Mode Only)

| Tool | Description | Read-Only |
|------|-------------|-----------|
| `insert_data` | Insert rows | No |
| `update_data` | Modify existing data | No |
| `delete_data` | Delete rows | No |

### Schema Management (Write Mode Only)

| Tool | Description | Read-Only |
|------|-------------|-----------|
| `create_table` | Create new tables | No |
| `drop_table` | Delete tables | No |
| `create_index` | Create indexes | No |

---

## Usage Patterns

### Read-Only Mode

```python
from src.mcp.mssql_config import MSSQLConfig

# Safe for exploration
config = MSSQLConfig(
    server_name="production-server",
    database_name="ProdDB",
    readonly=True,  # Blocks write operations
)
```

### With Agent

```python
from src.mcp.client import MCPClientManager
from src.agent.research_agent import ResearchAgent

manager = MCPClientManager()
mssql_server = manager.get_mssql_server()

# Agent uses MCP server for tools
agent = ResearchAgent()
response = await agent.chat("What tables are in the database?")
# Agent uses list_tables tool via MCP
```

### Direct Tool Access

```python
from pydantic_ai.mcp import MCPServerStdio

# Start MCP server
async with mssql_server:
    # List available tools
    tools = await mssql_server.list_tools()
    for tool in tools:
        print(f"Tool: {tool.name}")
        print(f"  Description: {tool.description}")
```

---

## Error Handling

```python
from src.mcp.client import MCPClientManager

try:
    manager = MCPClientManager()
    server = manager.get_mssql_server()
except FileNotFoundError as e:
    print(f"MCP server not found: {e}")
except ValueError as e:
    print(f"Invalid configuration: {e}")
```

---

*See also: [Agent API](agent.md), [MSSQL MCP Tools Reference](../reference/mssql_mcp_tools.md)*
