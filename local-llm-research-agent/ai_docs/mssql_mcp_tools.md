# MSSQL MCP Server Tools Reference

## Overview

The MSSQL MCP Server provides MCP tools for interacting with Microsoft SQL Server databases. It supports SQL Server, Azure SQL Database, and SQL Database in Microsoft Fabric.

## Available Implementations

- **Node.js** - Primary implementation
- **.NET** - Alternative implementation

## Configuration

### Environment Variables

```bash
SERVER_NAME=your-server.database.windows.net
DATABASE_NAME=your_database
TRUST_SERVER_CERTIFICATE=true
READONLY=false
```

### MCP Config (mcp_config.json)

```json
{
  "mcpServers": {
    "mssql": {
      "command": "node",
      "args": ["/path/to/MssqlMcp/Node/dist/index.js"],
      "env": {
        "SERVER_NAME": "localhost",
        "DATABASE_NAME": "mydb",
        "TRUST_SERVER_CERTIFICATE": "true",
        "READONLY": "false"
      }
    }
  }
}
```

## Tools

### list_tables

Lists all tables in the connected database.

**Use Case**: Schema discovery, understanding database structure

**Example Prompts**:
- "What tables are in the database?"
- "Show me all available tables"
- "List the database schema"

**Response**: Array of table names

---

### describe_table

Get detailed schema information for a specific table.

**Parameters**:
- `table_name` (string): Name of the table to describe

**Use Case**: Understanding table structure, column types, constraints

**Example Prompts**:
- "What columns does the Users table have?"
- "Describe the Orders table schema"
- "What's the structure of the Products table?"

**Response**: Column names, data types, nullable status, keys

---

### read_data

Query and retrieve data from a table.

**Parameters**:
- `table_name` (string): Table to query
- `conditions` (object, optional): WHERE clause conditions
- `limit` (number, optional): Maximum rows to return
- `order_by` (string, optional): Column to sort by

**Use Case**: Data retrieval, analysis, exploration

**Example Prompts**:
- "Show me the top 10 orders"
- "Get all customers from New York"
- "What are the most expensive products?"
- "Find orders placed this month"

**Response**: Array of row objects

---

### insert_data

Insert new rows into a table. Supports batch operations.

**Parameters**:
- `table_name` (string): Target table
- `data` (object|array): Row(s) to insert

**Use Case**: Data population, adding records

**Example Prompts**:
- "Add a new customer named John Smith"
- "Insert a product: Widget, $29.99"
- "Create a new order for customer 5"

**Response**: Number of rows inserted, generated IDs

---

### update_data

Modify existing data in a table.

**Parameters**:
- `table_name` (string): Table to update
- `conditions` (object): WHERE clause conditions
- `updates` (object): Column values to set

**Use Case**: Data maintenance, corrections

**Example Prompts**:
- "Update the status to 'shipped' for order 123"
- "Change the price of product 5 to $39.99"
- "Mark all pending orders as processing"

**Response**: Number of rows updated

---

### create_table

Create a new table in the database.

**Parameters**:
- `table_name` (string): Name for new table
- `columns` (array): Column definitions with types

**Use Case**: Schema management, new feature setup

**Example Prompts**:
- "Create a logs table with timestamp and message columns"
- "Make a new audit_trail table"

**Response**: Success confirmation

---

### drop_table

Delete a table from the database.

**Parameters**:
- `table_name` (string): Table to delete

**Use Case**: Schema cleanup, test data removal

**Example Prompts**:
- "Remove the temp_data table"
- "Delete the old_orders table"

**Response**: Success confirmation

---

### create_index

Create an index on a table for query optimization.

**Parameters**:
- `table_name` (string): Target table
- `index_name` (string): Name for the index
- `columns` (array): Columns to index

**Use Case**: Performance optimization

**Example Prompts**:
- "Create an index on the email column"
- "Add an index for faster customer lookups"

**Response**: Success confirmation

## Authentication

The MSSQL MCP Server supports:

1. **Microsoft Entra (Azure AD)** - Recommended for Azure SQL
2. **SQL Server Authentication** - Username/password
3. **Windows Authentication** - Integrated security

### Entra Authentication (Default for Node.js)

Opens browser for interactive authentication. Ensure your Entra user has database access.

### SQL Server Authentication (.NET version)

Set username and password in environment:
```bash
SQL_USERNAME=your_user
SQL_PASSWORD=your_password
```

## Security Considerations

1. **Use READONLY=true** for safe exploration
2. **Principle of least privilege** - Grant minimum necessary permissions
3. **Never commit credentials** - Use environment variables
4. **Audit tool usage** - Monitor for unexpected operations

## Setup Instructions

```bash
# Clone the repository
git clone https://github.com/Azure-Samples/SQL-AI-samples.git

# Navigate to Node.js implementation
cd SQL-AI-samples/MssqlMcp/Node

# Install dependencies
npm install

# The server is now at: ./dist/index.js
```

## Troubleshooting

### Connection Issues

```bash
# Test SQL Server connectivity
sqlcmd -S localhost -d your_db -Q "SELECT 1"

# Check Entra authentication
az login
```

### Certificate Issues

Set `TRUST_SERVER_CERTIFICATE=true` for self-signed certificates.

### Permission Issues

Ensure the authenticated user has appropriate database permissions:

```sql
-- Grant read access
GRANT SELECT ON SCHEMA::dbo TO [your_user];

-- Grant write access (if needed)
GRANT INSERT, UPDATE, DELETE ON SCHEMA::dbo TO [your_user];
```

## References

- [MSSQL MCP Server Blog Post](https://devblogs.microsoft.com/azure-sql/introducing-mssql-mcp-server/)
- [GitHub Repository](https://github.com/Azure-Samples/SQL-AI-samples/tree/main/MssqlMcp)
- [Azure SQL Documentation](https://docs.microsoft.com/azure/azure-sql/)
