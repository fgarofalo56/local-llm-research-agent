"""
Analytics Management MCP Server
Provides tools for dashboard, widget, metrics, and report management.

This MCP server integrates with the backend database to manage analytics
artifacts like dashboards, widgets, and generate reports.
"""

# Configure logging to stderr BEFORE any other imports
# JSON-RPC only on stdout - logging MUST go to stderr
import logging
import sys

logging.basicConfig(
    level=logging.WARNING,
    format="%(name)s - %(levelname)s - %(message)s",
    stream=sys.stderr,
    force=True,
)

import asyncio
import json
import os
from contextlib import contextmanager
from datetime import datetime, timedelta
from typing import Any

import pyodbc
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

# Suppress noisy loggers
logging.getLogger("mcp").setLevel(logging.WARNING)
logging.getLogger("asyncio").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

# Create the MCP server
server = Server("analytics-management")


def get_connection_string() -> str:
    """Build pyodbc connection string from environment variables."""
    server_name = os.environ.get("BACKEND_DB_HOST", "localhost")
    port = os.environ.get("BACKEND_DB_PORT", "1434")
    database = os.environ.get("BACKEND_DB_NAME", "LLM_BackEnd")
    username = os.environ.get("BACKEND_DB_USERNAME", os.environ.get("SQL_USERNAME", "sa"))
    password = os.environ.get("BACKEND_DB_PASSWORD", os.environ.get("SQL_PASSWORD", ""))
    trust_cert = os.environ.get("BACKEND_DB_TRUST_CERT", "true").lower() == "true"

    server_with_port = f"{server_name},{port}" if port else server_name

    conn_str = (
        f"DRIVER={{ODBC Driver 18 for SQL Server}};"
        f"SERVER={server_with_port};"
        f"DATABASE={database};"
        f"UID={username};"
        f"PWD={password};"
    )

    if trust_cert:
        conn_str += "TrustServerCertificate=yes;"

    return conn_str


@contextmanager
def get_connection():
    """Context manager for database connections."""
    conn = pyodbc.connect(get_connection_string())
    try:
        yield conn
    finally:
        conn.close()


def row_to_dict(cursor, row) -> dict:
    """Convert a pyodbc row to a dictionary."""
    columns = [column[0] for column in cursor.description]
    return dict(zip(columns, row, strict=False))


# =============================================================================
# Tool Definitions
# =============================================================================

TOOLS = [
    # Dashboard Management
    Tool(
        name="list_dashboards",
        description="List all dashboards with optional filtering by user or status",
        inputSchema={
            "type": "object",
            "properties": {
                "user_id": {"type": "integer", "description": "Filter by user ID (optional)"},
                "is_public": {"type": "boolean", "description": "Filter by public status (optional)"},
                "limit": {"type": "integer", "description": "Max results (default: 50)", "default": 50},
            },
        },
    ),
    Tool(
        name="get_dashboard",
        description="Get detailed information about a specific dashboard including its widgets",
        inputSchema={
            "type": "object",
            "properties": {
                "dashboard_id": {"type": "integer", "description": "Dashboard ID"},
            },
            "required": ["dashboard_id"],
        },
    ),
    Tool(
        name="create_dashboard",
        description="Create a new dashboard",
        inputSchema={
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Dashboard name"},
                "description": {"type": "string", "description": "Dashboard description"},
                "user_id": {"type": "integer", "description": "Owner user ID"},
                "is_public": {"type": "boolean", "description": "Make dashboard public", "default": False},
                "layout": {"type": "object", "description": "Dashboard layout configuration"},
            },
            "required": ["name"],
        },
    ),
    Tool(
        name="update_dashboard",
        description="Update an existing dashboard's properties",
        inputSchema={
            "type": "object",
            "properties": {
                "dashboard_id": {"type": "integer", "description": "Dashboard ID"},
                "name": {"type": "string", "description": "New name"},
                "description": {"type": "string", "description": "New description"},
                "is_public": {"type": "boolean", "description": "Public status"},
                "layout": {"type": "object", "description": "Layout configuration"},
            },
            "required": ["dashboard_id"],
        },
    ),
    Tool(
        name="delete_dashboard",
        description="Delete a dashboard and all its widgets",
        inputSchema={
            "type": "object",
            "properties": {
                "dashboard_id": {"type": "integer", "description": "Dashboard ID to delete"},
            },
            "required": ["dashboard_id"],
        },
    ),
    # Widget Management
    Tool(
        name="list_widgets",
        description="List widgets for a dashboard",
        inputSchema={
            "type": "object",
            "properties": {
                "dashboard_id": {"type": "integer", "description": "Dashboard ID"},
            },
            "required": ["dashboard_id"],
        },
    ),
    Tool(
        name="add_widget",
        description="Add a new widget to a dashboard",
        inputSchema={
            "type": "object",
            "properties": {
                "dashboard_id": {"type": "integer", "description": "Dashboard ID"},
                "widget_type": {
                    "type": "string",
                    "description": "Widget type",
                    "enum": ["bar", "line", "area", "pie", "scatter", "kpi", "table", "text"],
                },
                "title": {"type": "string", "description": "Widget title"},
                "query": {"type": "string", "description": "SQL query for data"},
                "config": {"type": "object", "description": "Widget configuration (colors, axes, etc.)"},
                "position": {
                    "type": "object",
                    "description": "Position and size",
                    "properties": {
                        "x": {"type": "integer"},
                        "y": {"type": "integer"},
                        "w": {"type": "integer"},
                        "h": {"type": "integer"},
                    },
                },
                "refresh_interval": {"type": "integer", "description": "Auto-refresh interval in seconds"},
            },
            "required": ["dashboard_id", "widget_type", "title"],
        },
    ),
    Tool(
        name="update_widget",
        description="Update an existing widget",
        inputSchema={
            "type": "object",
            "properties": {
                "widget_id": {"type": "integer", "description": "Widget ID"},
                "title": {"type": "string", "description": "New title"},
                "query": {"type": "string", "description": "New SQL query"},
                "config": {"type": "object", "description": "New configuration"},
                "position": {"type": "object", "description": "New position"},
                "refresh_interval": {"type": "integer", "description": "New refresh interval"},
            },
            "required": ["widget_id"],
        },
    ),
    Tool(
        name="delete_widget",
        description="Remove a widget from a dashboard",
        inputSchema={
            "type": "object",
            "properties": {
                "widget_id": {"type": "integer", "description": "Widget ID to delete"},
            },
            "required": ["widget_id"],
        },
    ),
    # Query Management
    Tool(
        name="list_saved_queries",
        description="List saved queries with optional filtering",
        inputSchema={
            "type": "object",
            "properties": {
                "user_id": {"type": "integer", "description": "Filter by user ID"},
                "is_favorite": {"type": "boolean", "description": "Filter favorites only"},
                "search": {"type": "string", "description": "Search in name/description"},
                "limit": {"type": "integer", "description": "Max results", "default": 50},
            },
        },
    ),
    Tool(
        name="save_query",
        description="Save a query for later reuse",
        inputSchema={
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Query name"},
                "description": {"type": "string", "description": "Query description"},
                "query_text": {"type": "string", "description": "SQL query text"},
                "user_id": {"type": "integer", "description": "Owner user ID"},
                "is_favorite": {"type": "boolean", "description": "Mark as favorite", "default": False},
            },
            "required": ["name", "query_text"],
        },
    ),
    Tool(
        name="get_query_history",
        description="Get recent query execution history",
        inputSchema={
            "type": "object",
            "properties": {
                "user_id": {"type": "integer", "description": "Filter by user ID"},
                "conversation_id": {"type": "integer", "description": "Filter by conversation"},
                "limit": {"type": "integer", "description": "Max results", "default": 100},
                "since": {"type": "string", "description": "ISO datetime to filter from"},
            },
        },
    ),
    # Metrics & Analytics
    Tool(
        name="get_dashboard_metrics",
        description="Get usage metrics for dashboards (views, shares, widget counts)",
        inputSchema={
            "type": "object",
            "properties": {
                "dashboard_id": {"type": "integer", "description": "Specific dashboard ID (optional)"},
                "period_days": {"type": "integer", "description": "Analysis period in days", "default": 30},
            },
        },
    ),
    Tool(
        name="get_usage_analytics",
        description="Get overall system usage analytics (queries, conversations, documents)",
        inputSchema={
            "type": "object",
            "properties": {
                "period_days": {"type": "integer", "description": "Analysis period in days", "default": 30},
                "group_by": {
                    "type": "string",
                    "description": "Grouping",
                    "enum": ["day", "week", "month"],
                    "default": "day",
                },
            },
        },
    ),
    # Export Operations
    Tool(
        name="export_dashboard",
        description="Export dashboard configuration as JSON for backup or sharing",
        inputSchema={
            "type": "object",
            "properties": {
                "dashboard_id": {"type": "integer", "description": "Dashboard ID to export"},
                "include_queries": {"type": "boolean", "description": "Include widget queries", "default": True},
            },
            "required": ["dashboard_id"],
        },
    ),
    Tool(
        name="import_dashboard",
        description="Import a dashboard from JSON configuration",
        inputSchema={
            "type": "object",
            "properties": {
                "config": {"type": "object", "description": "Dashboard configuration JSON"},
                "user_id": {"type": "integer", "description": "Owner user ID"},
                "rename_to": {"type": "string", "description": "Optional new name"},
            },
            "required": ["config"],
        },
    ),
]


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available analytics management tools."""
    return TOOLS


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """Execute an analytics management tool."""
    try:
        result = await execute_tool(name, arguments)
        return [TextContent(type="text", text=json.dumps(result, indent=2, default=str))]
    except Exception as e:
        logger.error(f"Tool execution error: {e}")
        return [TextContent(type="text", text=json.dumps({"error": str(e)}))]


async def execute_tool(name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    """Execute the specified tool with arguments."""

    # Dashboard Management
    if name == "list_dashboards":
        return await list_dashboards(
            user_id=arguments.get("user_id"),
            is_public=arguments.get("is_public"),
            limit=arguments.get("limit", 50),
        )

    elif name == "get_dashboard":
        return await get_dashboard(arguments["dashboard_id"])

    elif name == "create_dashboard":
        return await create_dashboard(
            name=arguments["name"],
            description=arguments.get("description"),
            user_id=arguments.get("user_id"),
            is_public=arguments.get("is_public", False),
            layout=arguments.get("layout"),
        )

    elif name == "update_dashboard":
        return await update_dashboard(
            dashboard_id=arguments["dashboard_id"],
            name=arguments.get("name"),
            description=arguments.get("description"),
            is_public=arguments.get("is_public"),
            layout=arguments.get("layout"),
        )

    elif name == "delete_dashboard":
        return await delete_dashboard(arguments["dashboard_id"])

    # Widget Management
    elif name == "list_widgets":
        return await list_widgets(arguments["dashboard_id"])

    elif name == "add_widget":
        return await add_widget(
            dashboard_id=arguments["dashboard_id"],
            widget_type=arguments["widget_type"],
            title=arguments["title"],
            query=arguments.get("query"),
            config=arguments.get("config"),
            position=arguments.get("position"),
            refresh_interval=arguments.get("refresh_interval"),
        )

    elif name == "update_widget":
        return await update_widget(
            widget_id=arguments["widget_id"],
            title=arguments.get("title"),
            query=arguments.get("query"),
            config=arguments.get("config"),
            position=arguments.get("position"),
            refresh_interval=arguments.get("refresh_interval"),
        )

    elif name == "delete_widget":
        return await delete_widget(arguments["widget_id"])

    # Query Management
    elif name == "list_saved_queries":
        return await list_saved_queries(
            user_id=arguments.get("user_id"),
            is_favorite=arguments.get("is_favorite"),
            search=arguments.get("search"),
            limit=arguments.get("limit", 50),
        )

    elif name == "save_query":
        return await save_query(
            name=arguments["name"],
            description=arguments.get("description"),
            query_text=arguments["query_text"],
            user_id=arguments.get("user_id"),
            is_favorite=arguments.get("is_favorite", False),
        )

    elif name == "get_query_history":
        return await get_query_history(
            user_id=arguments.get("user_id"),
            conversation_id=arguments.get("conversation_id"),
            limit=arguments.get("limit", 100),
            since=arguments.get("since"),
        )

    # Metrics & Analytics
    elif name == "get_dashboard_metrics":
        return await get_dashboard_metrics(
            dashboard_id=arguments.get("dashboard_id"),
            period_days=arguments.get("period_days", 30),
        )

    elif name == "get_usage_analytics":
        return await get_usage_analytics(
            period_days=arguments.get("period_days", 30),
            group_by=arguments.get("group_by", "day"),
        )

    # Export/Import
    elif name == "export_dashboard":
        return await export_dashboard(
            dashboard_id=arguments["dashboard_id"],
            include_queries=arguments.get("include_queries", True),
        )

    elif name == "import_dashboard":
        return await import_dashboard(
            config=arguments["config"],
            user_id=arguments.get("user_id"),
            rename_to=arguments.get("rename_to"),
        )

    else:
        return {"error": f"Unknown tool: {name}"}


# =============================================================================
# Tool Implementations
# =============================================================================

async def list_dashboards(
    user_id: int | None = None,
    is_public: bool | None = None,
    limit: int = 50,
) -> dict[str, Any]:
    """List dashboards with optional filtering."""
    with get_connection() as conn:
        cursor = conn.cursor()

        query = """
            SELECT
                d.id, d.name, d.description, d.user_id, d.is_public,
                d.layout, d.created_at, d.updated_at,
                (SELECT COUNT(*) FROM app.widgets w WHERE w.dashboard_id = d.id) as widget_count
            FROM app.dashboards d
            WHERE 1=1
        """
        params = []

        if user_id is not None:
            query += " AND d.user_id = ?"
            params.append(user_id)

        if is_public is not None:
            query += " AND d.is_public = ?"
            params.append(is_public)

        query += " ORDER BY d.updated_at DESC"
        query += f" OFFSET 0 ROWS FETCH NEXT {limit} ROWS ONLY"

        cursor.execute(query, params)
        rows = cursor.fetchall()

        dashboards = [row_to_dict(cursor, row) for row in rows]

        return {
            "dashboards": dashboards,
            "count": len(dashboards),
        }


async def get_dashboard(dashboard_id: int) -> dict[str, Any]:
    """Get dashboard with its widgets."""
    with get_connection() as conn:
        cursor = conn.cursor()

        # Get dashboard
        cursor.execute(
            """
            SELECT id, name, description, user_id, is_public, layout, created_at, updated_at
            FROM app.dashboards WHERE id = ?
            """,
            (dashboard_id,),
        )
        row = cursor.fetchone()

        if not row:
            return {"error": f"Dashboard {dashboard_id} not found"}

        dashboard = row_to_dict(cursor, row)

        # Get widgets
        cursor.execute(
            """
            SELECT id, widget_type, title, query, config, position_x, position_y,
                   width, height, refresh_interval, created_at, updated_at
            FROM app.widgets WHERE dashboard_id = ?
            ORDER BY position_y, position_x
            """,
            (dashboard_id,),
        )
        widgets = [row_to_dict(cursor, row) for row in cursor.fetchall()]

        dashboard["widgets"] = widgets

        return dashboard


async def create_dashboard(
    name: str,
    description: str | None = None,
    user_id: int | None = None,
    is_public: bool = False,
    layout: dict | None = None,
) -> dict[str, Any]:
    """Create a new dashboard."""
    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO app.dashboards (name, description, user_id, is_public, layout)
            OUTPUT INSERTED.id, INSERTED.created_at
            VALUES (?, ?, ?, ?, ?)
            """,
            (name, description, user_id, is_public, json.dumps(layout) if layout else None),
        )

        row = cursor.fetchone()
        conn.commit()

        return {
            "success": True,
            "dashboard_id": row[0],
            "created_at": row[1],
            "message": f"Dashboard '{name}' created successfully",
        }


async def update_dashboard(
    dashboard_id: int,
    name: str | None = None,
    description: str | None = None,
    is_public: bool | None = None,
    layout: dict | None = None,
) -> dict[str, Any]:
    """Update an existing dashboard."""
    with get_connection() as conn:
        cursor = conn.cursor()

        updates = []
        params = []

        if name is not None:
            updates.append("name = ?")
            params.append(name)
        if description is not None:
            updates.append("description = ?")
            params.append(description)
        if is_public is not None:
            updates.append("is_public = ?")
            params.append(is_public)
        if layout is not None:
            updates.append("layout = ?")
            params.append(json.dumps(layout))

        if not updates:
            return {"error": "No updates provided"}

        updates.append("updated_at = GETUTCDATE()")
        params.append(dashboard_id)

        query = f"UPDATE app.dashboards SET {', '.join(updates)} WHERE id = ?"
        cursor.execute(query, params)
        conn.commit()

        return {
            "success": True,
            "dashboard_id": dashboard_id,
            "message": "Dashboard updated successfully",
        }


async def delete_dashboard(dashboard_id: int) -> dict[str, Any]:
    """Delete a dashboard and all its widgets."""
    with get_connection() as conn:
        cursor = conn.cursor()

        # Delete widgets first
        cursor.execute("DELETE FROM app.widgets WHERE dashboard_id = ?", (dashboard_id,))
        widgets_deleted = cursor.rowcount

        # Delete dashboard
        cursor.execute("DELETE FROM app.dashboards WHERE id = ?", (dashboard_id,))

        if cursor.rowcount == 0:
            return {"error": f"Dashboard {dashboard_id} not found"}

        conn.commit()

        return {
            "success": True,
            "dashboard_id": dashboard_id,
            "widgets_deleted": widgets_deleted,
            "message": "Dashboard deleted successfully",
        }


async def list_widgets(dashboard_id: int) -> dict[str, Any]:
    """List widgets for a dashboard."""
    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT id, widget_type, title, query, config, position_x, position_y,
                   width, height, refresh_interval, created_at, updated_at
            FROM app.widgets WHERE dashboard_id = ?
            ORDER BY position_y, position_x
            """,
            (dashboard_id,),
        )

        widgets = [row_to_dict(cursor, row) for row in cursor.fetchall()]

        return {
            "dashboard_id": dashboard_id,
            "widgets": widgets,
            "count": len(widgets),
        }


async def add_widget(
    dashboard_id: int,
    widget_type: str,
    title: str,
    query: str | None = None,
    config: dict | None = None,
    position: dict | None = None,
    refresh_interval: int | None = None,
) -> dict[str, Any]:
    """Add a new widget to a dashboard."""
    with get_connection() as conn:
        cursor = conn.cursor()

        pos = position or {}

        cursor.execute(
            """
            INSERT INTO app.widgets (dashboard_id, widget_type, title, query, config,
                                     position_x, position_y, width, height, refresh_interval)
            OUTPUT INSERTED.id, INSERTED.created_at
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                dashboard_id,
                widget_type,
                title,
                query,
                json.dumps(config) if config else None,
                pos.get("x", 0),
                pos.get("y", 0),
                pos.get("w", 6),
                pos.get("h", 4),
                refresh_interval,
            ),
        )

        row = cursor.fetchone()
        conn.commit()

        return {
            "success": True,
            "widget_id": row[0],
            "created_at": row[1],
            "message": f"Widget '{title}' added successfully",
        }


async def update_widget(
    widget_id: int,
    title: str | None = None,
    query: str | None = None,
    config: dict | None = None,
    position: dict | None = None,
    refresh_interval: int | None = None,
) -> dict[str, Any]:
    """Update an existing widget."""
    with get_connection() as conn:
        cursor = conn.cursor()

        updates = []
        params = []

        if title is not None:
            updates.append("title = ?")
            params.append(title)
        if query is not None:
            updates.append("query = ?")
            params.append(query)
        if config is not None:
            updates.append("config = ?")
            params.append(json.dumps(config))
        if position is not None:
            if "x" in position:
                updates.append("position_x = ?")
                params.append(position["x"])
            if "y" in position:
                updates.append("position_y = ?")
                params.append(position["y"])
            if "w" in position:
                updates.append("width = ?")
                params.append(position["w"])
            if "h" in position:
                updates.append("height = ?")
                params.append(position["h"])
        if refresh_interval is not None:
            updates.append("refresh_interval = ?")
            params.append(refresh_interval)

        if not updates:
            return {"error": "No updates provided"}

        updates.append("updated_at = GETUTCDATE()")
        params.append(widget_id)

        query_str = f"UPDATE app.widgets SET {', '.join(updates)} WHERE id = ?"
        cursor.execute(query_str, params)
        conn.commit()

        return {
            "success": True,
            "widget_id": widget_id,
            "message": "Widget updated successfully",
        }


async def delete_widget(widget_id: int) -> dict[str, Any]:
    """Delete a widget."""
    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("DELETE FROM app.widgets WHERE id = ?", (widget_id,))

        if cursor.rowcount == 0:
            return {"error": f"Widget {widget_id} not found"}

        conn.commit()

        return {
            "success": True,
            "widget_id": widget_id,
            "message": "Widget deleted successfully",
        }


async def list_saved_queries(
    user_id: int | None = None,
    is_favorite: bool | None = None,
    search: str | None = None,
    limit: int = 50,
) -> dict[str, Any]:
    """List saved queries."""
    with get_connection() as conn:
        cursor = conn.cursor()

        query = """
            SELECT id, name, description, query_text, user_id, is_favorite,
                   created_at, updated_at
            FROM app.saved_queries
            WHERE 1=1
        """
        params = []

        if user_id is not None:
            query += " AND user_id = ?"
            params.append(user_id)

        if is_favorite is not None:
            query += " AND is_favorite = ?"
            params.append(is_favorite)

        if search:
            query += " AND (name LIKE ? OR description LIKE ?)"
            params.extend([f"%{search}%", f"%{search}%"])

        query += " ORDER BY updated_at DESC"
        query += f" OFFSET 0 ROWS FETCH NEXT {limit} ROWS ONLY"

        cursor.execute(query, params)
        queries = [row_to_dict(cursor, row) for row in cursor.fetchall()]

        return {
            "queries": queries,
            "count": len(queries),
        }


async def save_query(
    name: str,
    query_text: str,
    description: str | None = None,
    user_id: int | None = None,
    is_favorite: bool = False,
) -> dict[str, Any]:
    """Save a query for later reuse."""
    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO app.saved_queries (name, description, query_text, user_id, is_favorite)
            OUTPUT INSERTED.id, INSERTED.created_at
            VALUES (?, ?, ?, ?, ?)
            """,
            (name, description, query_text, user_id, is_favorite),
        )

        row = cursor.fetchone()
        conn.commit()

        return {
            "success": True,
            "query_id": row[0],
            "created_at": row[1],
            "message": f"Query '{name}' saved successfully",
        }


async def get_query_history(
    user_id: int | None = None,
    conversation_id: int | None = None,
    limit: int = 100,
    since: str | None = None,
) -> dict[str, Any]:
    """Get query execution history."""
    with get_connection() as conn:
        cursor = conn.cursor()

        query = """
            SELECT id, conversation_id, query_text, execution_time_ms,
                   row_count, status, error_message, created_at
            FROM app.query_history
            WHERE 1=1
        """
        params = []

        if user_id is not None:
            query += " AND user_id = ?"
            params.append(user_id)

        if conversation_id is not None:
            query += " AND conversation_id = ?"
            params.append(conversation_id)

        if since:
            query += " AND created_at >= ?"
            params.append(since)

        query += " ORDER BY created_at DESC"
        query += f" OFFSET 0 ROWS FETCH NEXT {limit} ROWS ONLY"

        cursor.execute(query, params)
        history = [row_to_dict(cursor, row) for row in cursor.fetchall()]

        return {
            "history": history,
            "count": len(history),
        }


async def get_dashboard_metrics(
    dashboard_id: int | None = None,
    period_days: int = 30,
) -> dict[str, Any]:
    """Get dashboard usage metrics."""
    with get_connection() as conn:
        cursor = conn.cursor()

        # Note: cutoff could be used for time-based filtering if needed
        # cutoff = datetime.utcnow() - timedelta(days=period_days)

        if dashboard_id:
            # Specific dashboard metrics
            cursor.execute(
                """
                SELECT
                    d.id, d.name,
                    (SELECT COUNT(*) FROM app.widgets w WHERE w.dashboard_id = d.id) as widget_count,
                    d.created_at, d.updated_at
                FROM app.dashboards d
                WHERE d.id = ?
                """,
                (dashboard_id,),
            )
            row = cursor.fetchone()

            if not row:
                return {"error": f"Dashboard {dashboard_id} not found"}

            return {
                "dashboard": row_to_dict(cursor, row),
                "period_days": period_days,
            }
        else:
            # Overall dashboard metrics
            cursor.execute(
                """
                SELECT
                    COUNT(*) as total_dashboards,
                    SUM(CASE WHEN is_public = 1 THEN 1 ELSE 0 END) as public_dashboards,
                    (SELECT COUNT(*) FROM app.widgets) as total_widgets
                FROM app.dashboards
                """
            )
            row = cursor.fetchone()

            return {
                "total_dashboards": row[0],
                "public_dashboards": row[1],
                "total_widgets": row[2],
                "period_days": period_days,
            }


async def get_usage_analytics(
    period_days: int = 30,
    group_by: str = "day",
) -> dict[str, Any]:
    """Get system usage analytics."""
    with get_connection() as conn:
        cursor = conn.cursor()

        cutoff = datetime.utcnow() - timedelta(days=period_days)

        # Get counts
        cursor.execute("SELECT COUNT(*) FROM app.conversations WHERE created_at >= ?", (cutoff,))
        conversations = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM app.messages WHERE created_at >= ?", (cutoff,))
        messages = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM vectors.documents WHERE created_at >= ?", (cutoff,))
        documents = cursor.fetchone()[0]

        return {
            "period_days": period_days,
            "group_by": group_by,
            "metrics": {
                "conversations": conversations,
                "messages": messages,
                "documents": documents,
            },
        }


async def export_dashboard(
    dashboard_id: int,
    include_queries: bool = True,
) -> dict[str, Any]:
    """Export dashboard configuration as JSON."""
    dashboard = await get_dashboard(dashboard_id)

    if "error" in dashboard:
        return dashboard

    export_config = {
        "version": "1.0",
        "exported_at": datetime.utcnow().isoformat(),
        "dashboard": {
            "name": dashboard["name"],
            "description": dashboard.get("description"),
            "is_public": dashboard.get("is_public", False),
            "layout": dashboard.get("layout"),
        },
        "widgets": [],
    }

    for widget in dashboard.get("widgets", []):
        widget_config = {
            "widget_type": widget["widget_type"],
            "title": widget["title"],
            "config": widget.get("config"),
            "position": {
                "x": widget.get("position_x", 0),
                "y": widget.get("position_y", 0),
                "w": widget.get("width", 6),
                "h": widget.get("height", 4),
            },
            "refresh_interval": widget.get("refresh_interval"),
        }

        if include_queries:
            widget_config["query"] = widget.get("query")

        export_config["widgets"].append(widget_config)

    return {
        "success": True,
        "config": export_config,
    }


async def import_dashboard(
    config: dict,
    user_id: int | None = None,
    rename_to: str | None = None,
) -> dict[str, Any]:
    """Import a dashboard from JSON configuration."""
    dashboard_config = config.get("dashboard", {})
    widgets_config = config.get("widgets", [])

    name = rename_to or dashboard_config.get("name", "Imported Dashboard")

    # Create dashboard
    result = await create_dashboard(
        name=name,
        description=dashboard_config.get("description"),
        user_id=user_id,
        is_public=dashboard_config.get("is_public", False),
        layout=dashboard_config.get("layout"),
    )

    if not result.get("success"):
        return result

    dashboard_id = result["dashboard_id"]

    # Add widgets
    widgets_created = 0
    for widget_config in widgets_config:
        await add_widget(
            dashboard_id=dashboard_id,
            widget_type=widget_config.get("widget_type", "bar"),
            title=widget_config.get("title", "Untitled"),
            query=widget_config.get("query"),
            config=widget_config.get("config"),
            position=widget_config.get("position"),
            refresh_interval=widget_config.get("refresh_interval"),
        )
        widgets_created += 1

    return {
        "success": True,
        "dashboard_id": dashboard_id,
        "widgets_created": widgets_created,
        "message": f"Dashboard '{name}' imported successfully with {widgets_created} widgets",
    }


# =============================================================================
# Main Entry Point
# =============================================================================

async def main():
    """Run the MCP server."""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options(),
        )


if __name__ == "__main__":
    asyncio.run(main())
