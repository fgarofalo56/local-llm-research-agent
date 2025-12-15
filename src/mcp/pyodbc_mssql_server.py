"""
Custom MSSQL MCP Server using pyodbc.

This is a simple MCP server that provides SQL Server database access
using pyodbc for reliable connectivity with ODBC Driver 18.
"""

import asyncio
import json
import os
import sys
from contextlib import contextmanager
from typing import Any

import pyodbc
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    TextContent,
    Tool,
)

# Server instance
server = Server("mssql-pyodbc")


def get_connection_string() -> str:
    """Build pyodbc connection string from environment variables."""
    server_name = os.environ.get("MSSQL_SERVER", "localhost")
    database = os.environ.get("MSSQL_DATABASE", "master")
    username = os.environ.get("MSSQL_USER", "sa")
    password = os.environ.get("MSSQL_PASSWORD", "")

    # Build connection string for ODBC Driver 18
    conn_str = (
        f"DRIVER={{ODBC Driver 18 for SQL Server}};"
        f"SERVER={server_name};"
        f"DATABASE={database};"
        f"UID={username};"
        f"PWD={password};"
        f"TrustServerCertificate=yes"
    )
    return conn_str


@contextmanager
def get_connection():
    """Context manager for database connections."""
    conn = pyodbc.connect(get_connection_string())
    try:
        yield conn
    finally:
        conn.close()


def execute_query(query: str, params: tuple = None) -> list[dict]:
    """Execute a SQL query and return results as list of dicts."""
    with get_connection() as conn:
        cursor = conn.cursor()
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)

        # For SELECT queries, return results
        if cursor.description:
            columns = [column[0] for column in cursor.description]
            rows = cursor.fetchall()
            return [dict(zip(columns, row, strict=False)) for row in rows]

        # For INSERT/UPDATE/DELETE, commit and return affected rows
        conn.commit()
        return [{"affected_rows": cursor.rowcount}]


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available database tools."""
    return [
        Tool(
            name="list_tables",
            description="List all tables in the database",
            inputSchema={"type": "object", "properties": {}, "required": []},
        ),
        Tool(
            name="describe_table",
            description="Get the schema/columns of a specific table",
            inputSchema={
                "type": "object",
                "properties": {
                    "table_name": {"type": "string", "description": "Name of the table to describe"}
                },
                "required": ["table_name"],
            },
        ),
        Tool(
            name="execute_sql",
            description="Execute a SQL query against the database",
            inputSchema={
                "type": "object",
                "properties": {"query": {"type": "string", "description": "SQL query to execute"}},
                "required": ["query"],
            },
        ),
        Tool(
            name="read_data",
            description="Read data from a table with optional filtering",
            inputSchema={
                "type": "object",
                "properties": {
                    "table_name": {"type": "string", "description": "Name of the table to read"},
                    "columns": {
                        "type": "string",
                        "description": "Comma-separated column names (default: *)",
                    },
                    "where": {
                        "type": "string",
                        "description": "WHERE clause conditions (without WHERE keyword)",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of rows to return (default: 100)",
                    },
                },
                "required": ["table_name"],
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """Handle tool calls."""
    try:
        if name == "list_tables":
            query = """
                SELECT TABLE_SCHEMA, TABLE_NAME, TABLE_TYPE
                FROM INFORMATION_SCHEMA.TABLES
                WHERE TABLE_TYPE = 'BASE TABLE'
                ORDER BY TABLE_SCHEMA, TABLE_NAME
            """
            results = execute_query(query)
            return [TextContent(type="text", text=json.dumps(results, indent=2, default=str))]

        elif name == "describe_table":
            table_name = arguments.get("table_name", "")
            query = """
                SELECT
                    COLUMN_NAME,
                    DATA_TYPE,
                    CHARACTER_MAXIMUM_LENGTH,
                    IS_NULLABLE,
                    COLUMN_DEFAULT
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_NAME = ?
                ORDER BY ORDINAL_POSITION
            """
            results = execute_query(query, (table_name,))
            return [TextContent(type="text", text=json.dumps(results, indent=2, default=str))]

        elif name == "execute_sql":
            query = arguments.get("query", "")
            results = execute_query(query)
            # Limit output to prevent huge responses
            if len(results) > 100:
                results = results[:100]
                results.append({"_note": "Results truncated to 100 rows"})
            return [TextContent(type="text", text=json.dumps(results, indent=2, default=str))]

        elif name == "read_data":
            table_name = arguments.get("table_name", "")
            columns = arguments.get("columns", "*")
            where = arguments.get("where", "")
            limit = arguments.get("limit", 100)

            # Build query safely
            query = f"SELECT TOP {int(limit)} {columns} FROM [{table_name}]"
            if where:
                query += f" WHERE {where}"

            results = execute_query(query)
            return [TextContent(type="text", text=json.dumps(results, indent=2, default=str))]

        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]

    except Exception as e:
        return [TextContent(type="text", text=f"Error: {str(e)}")]


async def main():
    """Run the MCP server."""
    print("Starting MSSQL MCP Server (pyodbc)...", file=sys.stderr)
    print(f"Server: {os.environ.get('MSSQL_SERVER', 'localhost')}", file=sys.stderr)
    print(f"Database: {os.environ.get('MSSQL_DATABASE', 'master')}", file=sys.stderr)

    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
