# 🔌 MSSQL MCP Server Tools Reference

> **Complete reference for SQL Server tools available through the Model Context Protocol**

---

## 📑 Table of Contents

- [Overview](#-overview)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Tools Reference](#-tools-reference)
- [Authentication](#-authentication)
- [Security](#-security)
- [Troubleshooting](#-troubleshooting)
- [Resources](#-resources)

---

## 🎯 Overview

The MSSQL MCP Server provides MCP tools for interacting with Microsoft SQL Server databases. It enables AI agents to query, analyze, and manage SQL data.

### Supported Databases

| Database Type | Status | Notes |
|---------------|--------|-------|
| SQL Server (on-premises) | ✅ | All versions |
| Azure SQL Database | ✅ | Recommended |
| SQL Database in Fabric | ✅ | Via Entra auth |
| Azure SQL Managed Instance | ✅ | Supported |

### Available Implementations

| Implementation | Language | Status |
|----------------|----------|--------|
| **Node.js** | JavaScript/TypeScript | ✅ Primary |
| **.NET** | C# | ✅ Alternative |

---

## 📦 Installation

### Step 1: Clone Repository

```bash
git clone https://github.com/Azure-Samples/SQL-AI-samples.git
cd SQL-AI-samples/MssqlMcp/Node
```

### Step 2: Install Dependencies

```bash
npm install
```

### Step 3: Verify Installation

```bash
# Server file location
ls dist/index.js
```

> 💡 **Tip:** Note the full path to `dist/index.js` - you'll need this for configuration.

---

## ⚙️ Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SERVER_NAME` | ✅ | - | SQL Server hostname |
| `DATABASE_NAME` | ✅ | - | Target database |
| `TRUST_SERVER_CERTIFICATE` | ❌ | `false` | Trust self-signed certs |
| `READONLY` | ❌ | `false` | Read-only mode |

```bash
# Example environment
export SERVER_NAME=localhost
export DATABASE_NAME=ResearchAnalytics
export TRUST_SERVER_CERTIFICATE=true
export READONLY=false
```

### MCP Configuration File

Create `mcp_config.json`:

```json
{
  "mcpServers": {
    "mssql": {
      "command": "node",
      "args": ["/path/to/MssqlMcp/Node/dist/index.js"],
      "env": {
        "SERVER_NAME": "localhost",
        "DATABASE_NAME": "ResearchAnalytics",
        "TRUST_SERVER_CERTIFICATE": "true",
        "READONLY": "false"
      }
    }
  }
}
```

---

## 🛠️ Tools Reference

### Quick Reference Table

| Tool | Description | Read-Only Safe |
|------|-------------|----------------|
| `list_tables` | List all database tables | ✅ |
| `describe_table` | Get table schema | ✅ |
| `read_data` | Query table data | ✅ |
| `insert_data` | Insert new rows | ❌ |
| `update_data` | Modify existing rows | ❌ |
| `create_table` | Create new table | ❌ |
| `drop_table` | Delete table | ❌ |
| `create_index` | Create index | ❌ |

---

### 📋 list_tables

Lists all tables in the connected database.

**Use Case:** Schema discovery, understanding database structure

**Parameters:** None

**Example Prompts:**
```
"What tables are in the database?"
"Show me all available tables"
"List the database schema"
```

**Response:** Array of table names

---

### 📊 describe_table

Get detailed schema information for a specific table.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `table_name` | string | ✅ | Name of the table |

**Use Case:** Understanding table structure, column types, constraints

**Example Prompts:**
```
"What columns does the Researchers table have?"
"Describe the Projects table schema"
"What's the structure of the Publications table?"
```

**Response:** Column names, data types, nullable status, primary/foreign keys

---

### 🔍 read_data

Query and retrieve data from a table.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `table_name` | string | ✅ | Table to query |
| `conditions` | object | ❌ | WHERE clause conditions |
| `limit` | number | ❌ | Max rows to return |
| `order_by` | string | ❌ | Column to sort by |

**Use Case:** Data retrieval, analysis, exploration

**Example Prompts:**
```
"Show me the top 10 researchers by salary"
"Get all projects in the AI department"
"What are the most cited publications?"
"Find experiments completed this month"
```

**Response:** Array of row objects

---

### ➕ insert_data

Insert new rows into a table. Supports batch operations.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `table_name` | string | ✅ | Target table |
| `data` | object/array | ✅ | Row(s) to insert |

**Use Case:** Data population, adding records

**Example Prompts:**
```
"Add a new researcher named John Smith"
"Insert a project: AI Research, budget $50000"
"Create a new publication record"
```

**Response:** Number of rows inserted, generated IDs

> ⚠️ **Warning:** Blocked in read-only mode (`READONLY=true`)

---

### ✏️ update_data

Modify existing data in a table.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `table_name` | string | ✅ | Table to update |
| `conditions` | object | ✅ | WHERE clause conditions |
| `updates` | object | ✅ | Column values to set |

**Use Case:** Data maintenance, corrections

**Example Prompts:**
```
"Update the status to 'completed' for project 5"
"Change the budget of project AI-001 to $75000"
"Mark researcher 12 as inactive"
```

**Response:** Number of rows updated

> ⚠️ **Warning:** Blocked in read-only mode (`READONLY=true`)

---

### 🆕 create_table

Create a new table in the database.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `table_name` | string | ✅ | Name for new table |
| `columns` | array | ✅ | Column definitions |

**Use Case:** Schema management, new feature setup

**Example Prompts:**
```
"Create a logs table with timestamp and message columns"
"Make a new audit_trail table"
```

**Response:** Success confirmation

> ⚠️ **Warning:** Blocked in read-only mode (`READONLY=true`)

---

### 🗑️ drop_table

Delete a table from the database.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `table_name` | string | ✅ | Table to delete |

**Use Case:** Schema cleanup, test data removal

**Example Prompts:**
```
"Remove the temp_data table"
"Delete the old_logs table"
```

**Response:** Success confirmation

> ⚠️ **Warning:** Blocked in read-only mode (`READONLY=true`). This is a destructive operation!

---

### 📈 create_index

Create an index on a table for query optimization.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `table_name` | string | ✅ | Target table |
| `index_name` | string | ✅ | Name for the index |
| `columns` | array | ✅ | Columns to index |

**Use Case:** Performance optimization

**Example Prompts:**
```
"Create an index on the email column"
"Add an index for faster researcher lookups"
```

**Response:** Success confirmation

---

## 🔐 Authentication

### Supported Methods

| Method | Best For | Configuration |
|--------|----------|---------------|
| **Microsoft Entra** | Azure SQL | Interactive browser auth |
| **SQL Authentication** | Local SQL Server | Username/password |
| **Windows Auth** | On-premises | Integrated security |

### Microsoft Entra (Default for Node.js)

Opens browser for interactive authentication:

1. Run the MCP server
2. Browser opens for login
3. Authenticate with Azure AD account
4. Token cached for session

> 💡 **Tip:** Ensure your Entra user has appropriate database permissions.

### SQL Server Authentication

For username/password authentication:

```bash
export SQL_USERNAME=your_user
export SQL_PASSWORD=your_password
```

### Windows Authentication

For integrated Windows authentication:

```bash
# Leave credentials empty - uses current Windows user
export SQL_USERNAME=
export SQL_PASSWORD=
```

---

## 🔒 Security

### Best Practices

| Practice | Priority | Description |
|----------|----------|-------------|
| Use read-only mode | 🔴 High | Set `READONLY=true` for exploration |
| Least privilege | 🔴 High | Grant minimum permissions |
| Environment variables | 🔴 High | Never hardcode credentials |
| Audit logging | 🟡 Medium | Monitor tool usage |
| Network isolation | 🟡 Medium | Restrict database access |

### Read-Only Mode

Enable for safe exploration:

```json
{
  "env": {
    "READONLY": "true"
  }
}
```

**Operations in read-only mode:**

| Operation | Status |
|-----------|--------|
| `list_tables` | ✅ Allowed |
| `describe_table` | ✅ Allowed |
| `read_data` | ✅ Allowed |
| `insert_data` | ❌ Blocked |
| `update_data` | ❌ Blocked |
| `drop_table` | ❌ Blocked |

### SQL Permissions

Grant appropriate permissions to the MCP user:

```sql
-- Read-only access
GRANT SELECT ON SCHEMA::dbo TO [mcp_user];

-- Read-write access (if needed)
GRANT INSERT, UPDATE, DELETE ON SCHEMA::dbo TO [mcp_user];

-- Schema management (use carefully!)
GRANT CREATE TABLE, ALTER, DROP ON SCHEMA::dbo TO [mcp_user];
```

---

## 🔧 Troubleshooting

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| Connection refused | Server not running | Start SQL Server |
| Login failed | Wrong credentials | Verify username/password |
| Certificate error | Self-signed cert | Set `TRUST_SERVER_CERTIFICATE=true` |
| Permission denied | Insufficient grants | Check SQL permissions |
| Timeout | Slow query or network | Increase timeout setting |

### Connection Test

```bash
# Test with sqlcmd
sqlcmd -S localhost -d ResearchAnalytics -Q "SELECT 1"

# Test Entra authentication
az login
az account show
```

### Debug Mode

Enable verbose logging:

```bash
DEBUG=* node /path/to/dist/index.js
```

---

## 📚 Resources

### Official Documentation

- 📖 [MSSQL MCP Server Blog Post](https://devblogs.microsoft.com/azure-sql/introducing-mssql-mcp-server/)
- 💻 [GitHub Repository](https://github.com/Azure-Samples/SQL-AI-samples/tree/main/MssqlMcp)
- 📘 [Azure SQL Documentation](https://docs.microsoft.com/azure/azure-sql/)

### Related Guides

- [Getting Started](../guides/getting-started.md)
- [Configuration Reference](../guides/configuration.md)
- [Troubleshooting Guide](../guides/troubleshooting.md)

---

*Last Updated: December 2024*
