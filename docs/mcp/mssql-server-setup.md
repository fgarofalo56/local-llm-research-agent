# MSSQL MCP Server Setup Guide

> **Complete installation and configuration guide for the Microsoft SQL Server MCP Server**

---

## Table of Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Authentication Methods](#authentication-methods)
- [Testing the Connection](#testing-the-connection)
- [Integration with Project](#integration-with-project)
- [Common Issues](#common-issues)
- [Advanced Configuration](#advanced-configuration)

---

## Overview

The MSSQL MCP Server provides AI agents with tools to interact with Microsoft SQL Server databases. It supports multiple authentication methods and both read-only and read-write operations.

### Available Implementations

| Implementation | Language | Best For | Status |
|----------------|----------|----------|--------|
| **Node.js** | JavaScript/TypeScript | Production, Azure SQL | ✅ Recommended |
| **Python** | Python 3.11+ | Experimental, local dev | ⚠️ Experimental |

This guide focuses on the **Node.js implementation** as the primary option.

---

## Prerequisites

### Required Software

| Software | Minimum Version | Installation |
|----------|----------------|--------------|
| **Node.js** | v18.0.0+ | [nodejs.org](https://nodejs.org/) |
| **npm** | v8.0.0+ | Included with Node.js |
| **Git** | Latest | [git-scm.com](https://git-scm.com/) |

### SQL Server Access

You need access to one of:

- **Local SQL Server** (Express, Developer, or Enterprise)
- **Docker SQL Server** (via docker-compose in this project)
- **Azure SQL Database**
- **SQL Server on Azure VM**
- **SQL Database in Microsoft Fabric**

### Verify Prerequisites

```bash
# Check Node.js version
node --version
# Output: v18.0.0 or higher

# Check npm version
npm --version
# Output: v8.0.0 or higher

# Check Git
git --version
# Output: git version 2.x.x
```

---

## Installation

### Step 1: Clone the Repository

```bash
# Clone the Azure SQL-AI-samples repository
git clone https://github.com/Azure-Samples/SQL-AI-samples.git

# Navigate to the Node.js MCP server
cd SQL-AI-samples/MssqlMcp/Node
```

### Step 2: Install Dependencies

```bash
# Install Node.js packages
npm install

# Output should show:
# added XXX packages in YYs
```

### Step 3: Build the Server

The server is TypeScript-based and needs to be compiled:

```bash
# Build TypeScript to JavaScript
npm run build

# Or if no build script exists:
npx tsc
```

### Step 4: Verify Installation

```bash
# Check that the compiled JavaScript exists
ls dist/index.js
# On Windows: dir dist\index.js

# You should see: dist/index.js
```

### Step 5: Note the Path

**CRITICAL:** Record the full path to `dist/index.js` - you'll need it for configuration.

```bash
# On Windows (PowerShell):
(Get-Item dist/index.js).FullName
# Output: C:\path\to\SQL-AI-samples\MssqlMcp\Node\dist\index.js

# On Windows (Command Prompt):
cd
# Then add: \SQL-AI-samples\MssqlMcp\Node\dist\index.js

# On Linux/Mac:
realpath dist/index.js
# Output: /home/user/SQL-AI-samples/MssqlMcp/Node/dist/index.js
```

---

## Configuration

### Project .env File

Add the MCP server path to your project's `.env` file:

```bash
# Navigate to project root
cd E:\Repos\GitHub\MyDemoRepos\local-llm-research-agent

# Edit .env file
notepad .env  # Windows
nano .env     # Linux/Mac
```

Add these lines:

```bash
# ------------------------------------------
# MSSQL MCP Server Configuration
# ------------------------------------------

# Path to the MSSQL MCP Server (ABSOLUTE PATH!)
MCP_MSSQL_PATH=C:\Projects\SQL-AI-samples\MssqlMcp\Node\dist\index.js

# Read-only mode (true = safer for exploration)
MCP_MSSQL_READONLY=false

# Enable debug logging
MCP_DEBUG=false

# ------------------------------------------
# SQL Server Connection
# ------------------------------------------

# Hostname (localhost for Docker, FQDN for Azure)
SQL_SERVER_HOST=localhost

# Port (1433 for sample DB, 1434 for backend DB)
SQL_SERVER_PORT=1433

# Database name
SQL_DATABASE_NAME=ResearchAnalytics

# Connection encryption
SQL_ENCRYPT=true
SQL_TRUST_SERVER_CERTIFICATE=true

# ------------------------------------------
# Authentication (see Authentication section)
# ------------------------------------------

# Authentication type
SQL_AUTH_TYPE=sql

# SQL Server authentication
SQL_USERNAME=sa
SQL_PASSWORD=LocalLLM@2024!
```

### MCP Configuration File

The `mcp_config.json` file is already configured with environment variable references:

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
        "ENCRYPT": "${SQL_ENCRYPT}",
        "READONLY": "${MCP_MSSQL_READONLY}",
        "AUTH_TYPE": "${SQL_AUTH_TYPE}",
        "SQL_USERNAME": "${SQL_USERNAME}",
        "SQL_PASSWORD": "${SQL_PASSWORD}"
      }
    }
  }
}
```

**No changes needed** - it reads from `.env` automatically!

---

## Authentication Methods

The MSSQL MCP Server supports multiple authentication methods.

### Option 1: SQL Server Authentication (Default)

**Best for:** Local development, Docker containers

**Configuration:**

```bash
SQL_AUTH_TYPE=sql
SQL_USERNAME=sa
SQL_PASSWORD=LocalLLM@2024!
```

**Pros:**
- Simple setup
- Works everywhere
- No domain required

**Cons:**
- Less secure than integrated auth
- Requires password management

---

### Option 2: Windows Authentication

**Best for:** On-premises SQL Server on Windows domain

**Configuration:**

```bash
SQL_AUTH_TYPE=windows
SQL_USERNAME=
SQL_PASSWORD=
```

**Pros:**
- Secure, no passwords
- Uses current Windows identity
- Leverages Active Directory

**Cons:**
- Windows-only
- Requires domain membership

**Notes:**
- Leave `SQL_USERNAME` and `SQL_PASSWORD` empty
- User running the application must have SQL Server access
- Works best on Windows Server environments

---

### Option 3: Azure AD Interactive

**Best for:** Development with Azure SQL Database

**Configuration:**

```bash
SQL_AUTH_TYPE=azure_ad_interactive
SQL_SERVER_HOST=myserver.database.windows.net
SQL_DATABASE_NAME=mydb
SQL_ENCRYPT=true
SQL_TRUST_SERVER_CERTIFICATE=false
```

**Pros:**
- Secure, no passwords
- Multi-factor authentication
- Centralized identity management

**Cons:**
- Requires browser for login
- Not suitable for automation

**Process:**
1. Application starts MCP server
2. Browser opens for Azure AD login
3. User authenticates
4. Token cached for session
5. Subsequent operations use cached token

---

### Option 4: Azure AD Service Principal

**Best for:** Automated/unattended scenarios, CI/CD

**Configuration:**

```bash
SQL_AUTH_TYPE=azure_ad_service_principal
AZURE_TENANT_ID=12345678-1234-1234-1234-123456789abc
AZURE_CLIENT_ID=87654321-4321-4321-4321-cba987654321
AZURE_CLIENT_SECRET=your-secret-here
SQL_SERVER_HOST=myserver.database.windows.net
SQL_DATABASE_NAME=mydb
SQL_ENCRYPT=true
SQL_TRUST_SERVER_CERTIFICATE=false
```

**Pros:**
- Automated, no user interaction
- Secure credential management
- Audit trail in Azure AD

**Cons:**
- Requires Azure AD app registration
- More complex setup

**Setup Steps:**

1. **Create Azure AD App Registration**
   ```bash
   az ad app create --display-name "LLM Research Agent"
   ```

2. **Create Service Principal**
   ```bash
   az ad sp create-for-rbac --name "LLM Research Agent"
   ```

3. **Grant SQL Database Access**
   ```sql
   CREATE USER [LLM Research Agent] FROM EXTERNAL PROVIDER;
   ALTER ROLE db_datareader ADD MEMBER [LLM Research Agent];
   ALTER ROLE db_datawriter ADD MEMBER [LLM Research Agent];
   ```

---

### Option 5: Azure Managed Identity

**Best for:** Azure-hosted applications (VMs, App Service, Functions)

**Configuration:**

```bash
SQL_AUTH_TYPE=azure_ad_managed_identity

# Optional: for user-assigned managed identity
AZURE_CLIENT_ID=your-user-assigned-mi-client-id

SQL_SERVER_HOST=myserver.database.windows.net
SQL_DATABASE_NAME=mydb
SQL_ENCRYPT=true
SQL_TRUST_SERVER_CERTIFICATE=false
```

**Pros:**
- No credentials to manage
- Automatic token rotation
- Secure and auditable

**Cons:**
- Azure-only
- Requires managed identity configuration

---

### Option 6: Azure AD Default Credential

**Best for:** Local development with Azure CLI

**Configuration:**

```bash
SQL_AUTH_TYPE=azure_ad_default
SQL_SERVER_HOST=myserver.database.windows.net
SQL_DATABASE_NAME=mydb
SQL_ENCRYPT=true
SQL_TRUST_SERVER_CERTIFICATE=false
```

**Authentication chain:**
1. Environment variables (AZURE_CLIENT_ID, etc.)
2. Managed Identity
3. Azure CLI (`az login`)
4. Azure PowerShell
5. Interactive browser

**Pros:**
- Flexible fallback chain
- Works in multiple scenarios
- No configuration needed if Azure CLI logged in

**Cons:**
- Can be unpredictable
- May prompt unexpectedly

---

## Testing the Connection

### Method 1: Direct Server Test

Test the MCP server directly:

```bash
# Set environment variables (Windows PowerShell)
$env:SERVER_NAME="localhost"
$env:DATABASE_NAME="ResearchAnalytics"
$env:TRUST_SERVER_CERTIFICATE="true"
$env:AUTH_TYPE="sql"
$env:SQL_USERNAME="sa"
$env:SQL_PASSWORD="LocalLLM@2024!"

# Run the server
node C:\path\to\SQL-AI-samples\MssqlMcp\Node\dist\index.js

# On Linux/Mac:
export SERVER_NAME=localhost
export DATABASE_NAME=ResearchAnalytics
export TRUST_SERVER_CERTIFICATE=true
export AUTH_TYPE=sql
export SQL_USERNAME=sa
export SQL_PASSWORD="LocalLLM@2024!"

node /path/to/SQL-AI-samples/MssqlMcp/Node/dist/index.js
```

**Expected output:**
- Server starts without errors
- Waits for MCP protocol messages on stdin/stdout

Press Ctrl+C to stop.

---

### Method 2: Test SQL Connection

Before testing MCP, verify SQL Server is accessible:

```bash
# Using sqlcmd (Windows/Linux)
sqlcmd -S localhost -d ResearchAnalytics -U sa -P "LocalLLM@2024!" -Q "SELECT 1"

# Expected output:
# -----------
#           1
# (1 rows affected)

# Test Azure SQL Database
sqlcmd -S myserver.database.windows.net -d mydb -U myuser -P "password" -Q "SELECT 1"
```

---

### Method 3: Test via Application

The most comprehensive test:

```bash
# Start Docker services (if using Docker SQL Server)
cd E:\Repos\GitHub\MyDemoRepos\local-llm-research-agent
docker-compose -f docker/docker-compose.yml --env-file .env up -d mssql

# Start the backend API
uv run uvicorn src.api.main:app --reload

# Check health endpoint
curl http://localhost:8000/api/health

# Test MCP server status
curl http://localhost:8000/api/mcp

# Start frontend
cd frontend
npm run dev

# Open browser: http://localhost:5173
# Try query: "What tables are in the database?"
```

---

### Method 4: Python Test Script

Create a test script `test_mcp_connection.py`:

```python
import asyncio
from src.mcp.server_manager import MCPServerManager

async def test_connection():
    """Test MSSQL MCP server connection."""
    manager = MCPServerManager()

    try:
        print("Testing MSSQL MCP server connection...")

        async with manager.mssql_server_context() as server:
            print("✅ Server connected!")

            # List available tools
            tools = await server.list_tools()
            print(f"✅ Found {len(tools)} tools:")
            for tool in tools:
                print(f"   - {tool.name}: {tool.description}")

        print("\n✅ All tests passed!")

    except Exception as e:
        print(f"❌ Connection failed: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(test_connection())
```

Run the test:

```bash
uv run python test_mcp_connection.py
```

**Expected output:**
```
Testing MSSQL MCP server connection...
✅ Server connected!
✅ Found 8 tools:
   - list_tables: Lists all tables in the connected database
   - describe_table: Get schema information for a specific table
   - read_data: Query and retrieve data from tables
   - insert_data: Insert new rows into tables
   - update_data: Modify existing data in tables
   - create_table: Create new database tables
   - drop_table: Delete tables from the database
   - create_index: Create indexes for query optimization

✅ All tests passed!
```

---

## Integration with Project

The MSSQL MCP server is automatically integrated with the agent framework.

### How It Works

1. **Startup:** When the agent initializes, it reads `mcp_config.json`
2. **Server Creation:** `MCPClientManager` creates `MCPServerStdio` instances
3. **Tool Registration:** Agent discovers tools via `list_tools()`
4. **Execution:** When user queries require database access, agent calls appropriate tools
5. **Cleanup:** Context manager ensures proper server shutdown

### Code Flow

```python
# src/agent/research_agent.py

from pydantic_ai import Agent
from src.mcp.client import MCPClientManager

# Create MCP client manager
mcp_manager = MCPClientManager()

# Get MSSQL server
mssql_server = mcp_manager.get_mssql_server()

# Create agent with MCP toolset
agent = Agent(
    model=model,
    system_prompt="You are a helpful SQL data analyst.",
    toolsets=[mssql_server]  # Tools automatically registered
)

# Use the agent
async with agent:
    result = await agent.run("Show me the top 10 researchers by salary")
    # Agent automatically uses read_data tool
```

### Available Tools

Once configured, these tools are available to the AI agent:

| Tool | Read-Only Safe | Description |
|------|----------------|-------------|
| `list_tables` | ✅ | List all database tables |
| `describe_table` | ✅ | Get table schema |
| `read_data` | ✅ | Query table data |
| `insert_data` | ❌ | Insert new rows |
| `update_data` | ❌ | Modify existing rows |
| `create_table` | ❌ | Create new table |
| `drop_table` | ❌ | Delete table |
| `create_index` | ❌ | Create index |

**Read-Only Mode:** Set `MCP_MSSQL_READONLY=true` to block write operations.

---

## Common Issues

### Issue 1: "MCP_MSSQL_PATH is not set"

**Cause:** Environment variable not configured

**Solution:**
```bash
# Add to .env file
MCP_MSSQL_PATH=C:\path\to\SQL-AI-samples\MssqlMcp\Node\dist\index.js
```

---

### Issue 2: "MCP_MSSQL_PATH does not exist"

**Cause:** Path is incorrect or server not built

**Solution:**
```bash
# Verify path exists
ls "C:\path\to\SQL-AI-samples\MssqlMcp\Node\dist\index.js"

# If missing, rebuild
cd C:\path\to\SQL-AI-samples\MssqlMcp\Node
npm run build
```

---

### Issue 3: "Login failed for user"

**Cause:** Incorrect credentials or authentication type

**Solution:**
```bash
# Verify credentials
sqlcmd -S localhost -U sa -P "LocalLLM@2024!" -Q "SELECT 1"

# Check .env file
SQL_AUTH_TYPE=sql
SQL_USERNAME=sa
SQL_PASSWORD=LocalLLM@2024!
```

---

### Issue 4: "Certificate chain was issued by an authority that is not trusted"

**Cause:** Self-signed certificate not trusted

**Solution:**
```bash
# Trust self-signed certificates
SQL_TRUST_SERVER_CERTIFICATE=true
```

---

### Issue 5: "Connection timeout"

**Cause:** SQL Server not running or network issue

**Solution:**
```bash
# Check SQL Server is running (Docker)
docker ps | grep mssql

# Start if not running
docker-compose -f docker/docker-compose.yml --env-file .env up -d mssql

# Check network connectivity
ping localhost
telnet localhost 1433
```

---

### Issue 6: "Node.js version too old"

**Cause:** Node.js < v18

**Solution:**
```bash
# Check version
node --version

# Update Node.js from https://nodejs.org/
# Or use nvm:
nvm install 18
nvm use 18
```

---

## Advanced Configuration

### Performance Tuning

```bash
# Increase timeout for slow queries
MCP_TIMEOUT=60

# Connection pool settings (set in SQL Server)
SQL_POOL_SIZE=10
SQL_POOL_IDLE_TIMEOUT=30000
```

### Debug Logging

Enable verbose logging to troubleshoot issues:

```bash
# In .env
MCP_DEBUG=true
LOG_LEVEL=DEBUG

# Run server with debug output
DEBUG=* node /path/to/dist/index.js
```

### Multiple Database Connections

Configure multiple MCP servers in `mcp_config.json`:

```json
{
  "mcpServers": {
    "mssql_research": {
      "command": "node",
      "args": ["${MCP_MSSQL_PATH}"],
      "env": {
        "SERVER_NAME": "localhost",
        "DATABASE_NAME": "ResearchAnalytics",
        "AUTH_TYPE": "sql",
        "SQL_USERNAME": "${SQL_USERNAME}",
        "SQL_PASSWORD": "${SQL_PASSWORD}"
      }
    },
    "mssql_backend": {
      "command": "node",
      "args": ["${MCP_MSSQL_PATH}"],
      "env": {
        "SERVER_NAME": "localhost:1434",
        "DATABASE_NAME": "LLM_BackEnd",
        "AUTH_TYPE": "sql",
        "SQL_USERNAME": "${SQL_USERNAME}",
        "SQL_PASSWORD": "${SQL_PASSWORD}"
      }
    }
  }
}
```

### Custom SQL Permissions

Grant minimal permissions for security:

```sql
-- Create dedicated MCP user
CREATE LOGIN mcp_agent WITH PASSWORD = 'SecurePassword123!';
CREATE USER mcp_agent FOR LOGIN mcp_agent;

-- Read-only access
GRANT SELECT ON SCHEMA::dbo TO mcp_agent;

-- Read-write access (if needed)
GRANT INSERT, UPDATE, DELETE ON SCHEMA::dbo TO mcp_agent;

-- Specific tables only
GRANT SELECT ON dbo.Researchers TO mcp_agent;
GRANT SELECT ON dbo.Projects TO mcp_agent;
```

---

## Next Steps

1. **Test the connection** using the methods above
2. **Review tools reference:** [MSSQL MCP Tools](../reference/mssql_mcp_tools.md)
3. **Try sample queries** in the application
4. **Enable read-only mode** for safe exploration
5. **Build custom servers:** [Custom Server Development](custom-server-development.md)

---

## Resources

- [MSSQL MCP Server GitHub](https://github.com/Azure-Samples/SQL-AI-samples/tree/main/MssqlMcp)
- [MSSQL MCP Tools Reference](../reference/mssql_mcp_tools.md)
- [Troubleshooting Guide](troubleshooting.md)
- [Main README](README.md)

---

*Last Updated: December 2024*
