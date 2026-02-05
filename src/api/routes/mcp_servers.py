"""
MCP Servers Routes
Phase 2.1: Backend Infrastructure & RAG Pipeline

Endpoints for MCP server configuration and management.
"""

import structlog
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from src.api.deps import get_mcp_manager_optional
from src.mcp.dynamic_manager import MCPServerConfig

router = APIRouter()
logger = structlog.get_logger()


class MCPServerResponse(BaseModel):
    """Response model for MCP server."""

    id: str
    name: str
    description: str | None
    type: str
    command: str | None
    args: list[str]
    url: str | None
    enabled: bool
    built_in: bool
    # Additional fields for frontend compatibility
    status: str = "connected"  # 'connected', 'disconnected', 'error'
    tools: list[str] = []  # List of available tool names


class MCPServerCreate(BaseModel):
    """Request model for creating an MCP server."""

    id: str
    name: str
    description: str = ""
    type: str  # 'stdio' or 'http'
    command: str | None = None
    args: list[str] = []
    url: str | None = None
    env: dict[str, str] = {}
    enabled: bool = True


class MCPServerUpdate(BaseModel):
    """Request model for updating an MCP server."""

    name: str | None = None
    description: str | None = None
    enabled: bool | None = None
    command: str | None = None
    args: list[str] | None = None
    url: str | None = None
    env: dict[str, str] | None = None


class MCPServerListResponse(BaseModel):
    """Response model for MCP server list."""

    servers: list[MCPServerResponse]
    total: int


@router.get("", response_model=MCPServerListResponse)
async def list_mcp_servers(
    mcp_manager=Depends(get_mcp_manager_optional),
):
    """List all configured MCP servers."""
    if not mcp_manager:
        return MCPServerListResponse(servers=[], total=0)

    servers = mcp_manager.list_servers()

    # Build response with status and tools info
    server_responses = []
    for s in servers:
        # Determine status based on enabled flag
        status = "connected" if s.enabled else "disconnected"

        # Get tools if available (placeholder - would need to query MCP server)
        tools: list[str] = []
        if s.enabled:
            if s.id == "mssql":
                # Default MSSQL tools
                tools = [
                    "list_tables",
                    "describe_table",
                    "read_data",
                    "insert_data",
                    "update_data",
                    "create_table",
                    "drop_table",
                    "create_index",
                ]
            elif s.id == "analytics-management":
                # Analytics Management MCP tools
                tools = [
                    "list_dashboards",
                    "get_dashboard",
                    "create_dashboard",
                    "update_dashboard",
                    "delete_dashboard",
                    "list_widgets",
                    "add_widget",
                    "update_widget",
                    "delete_widget",
                    "list_saved_queries",
                    "save_query",
                    "get_query_history",
                    "get_dashboard_metrics",
                    "get_usage_analytics",
                    "export_dashboard",
                    "import_dashboard",
                ]
            elif s.id == "data-analytics":
                # Data Analytics MCP tools
                tools = [
                    "descriptive_statistics",
                    "correlation_analysis",
                    "percentile_analysis",
                    "group_aggregation",
                    "pivot_analysis",
                    "time_series_analysis",
                    "trend_detection",
                    "profile_table",
                    "column_distribution",
                    "data_quality_check",
                    "detect_outliers",
                    "detect_anomalies_timeseries",
                    "segment_analysis",
                    "cohort_analysis",
                    "run_analytics_query",
                ]
            elif s.id == "archon":
                # Archon MCP tools (project management + RAG)
                tools = [
                    "find_projects",
                    "manage_project",
                    "find_tasks",
                    "manage_task",
                    "find_documents",
                    "manage_document",
                    "find_versions",
                    "manage_version",
                    "get_project_features",
                    "rag_search_knowledge_base",
                    "rag_search_code_examples",
                    "rag_get_available_sources",
                    "rag_list_pages_for_source",
                    "rag_read_full_page",
                    "health_check",
                    "session_info",
                ]
            elif s.id == "microsoft.docs.mcp":
                # Microsoft Docs MCP tools
                tools = [
                    "search",
                    "get_page",
                    "list_products",
                    "get_toc",
                ]

        server_responses.append(
            MCPServerResponse(
                id=s.id,
                name=s.name,
                description=s.description,
                type=s.type,
                command=s.command,
                args=s.args,
                url=s.url,
                enabled=s.enabled,
                built_in=s.built_in,
                status=status,
                tools=tools,
            )
        )

    return MCPServerListResponse(
        servers=server_responses,
        total=len(servers),
    )


@router.get("/{server_id}", response_model=MCPServerResponse)
async def get_mcp_server(
    server_id: str,
    mcp_manager=Depends(get_mcp_manager_optional),
):
    """Get a specific MCP server configuration."""
    if not mcp_manager:
        raise HTTPException(status_code=503, detail="MCP manager not available")

    servers = {s.id: s for s in mcp_manager.list_servers()}
    if server_id not in servers:
        raise HTTPException(status_code=404, detail="Server not found")

    s = servers[server_id]
    return MCPServerResponse(
        id=s.id,
        name=s.name,
        description=s.description,
        type=s.type,
        command=s.command,
        args=s.args,
        url=s.url,
        enabled=s.enabled,
        built_in=s.built_in,
    )


@router.post("", response_model=MCPServerResponse)
async def create_mcp_server(
    data: MCPServerCreate,
    mcp_manager=Depends(get_mcp_manager_optional),
):
    """Add a new MCP server."""
    if not mcp_manager:
        raise HTTPException(status_code=503, detail="MCP manager not available")

    # Check if ID already exists
    existing = {s.id for s in mcp_manager.list_servers()}
    if data.id in existing:
        raise HTTPException(status_code=400, detail="Server ID already exists")

    config = MCPServerConfig(
        id=data.id,
        name=data.name,
        description=data.description,
        type=data.type,
        command=data.command,
        args=data.args,
        url=data.url,
        env=data.env,
        enabled=data.enabled,
        built_in=False,
    )

    await mcp_manager.add_server(config)

    return MCPServerResponse(
        id=config.id,
        name=config.name,
        description=config.description,
        type=config.type,
        command=config.command,
        args=config.args,
        url=config.url,
        enabled=config.enabled,
        built_in=config.built_in,
    )


@router.patch("/{server_id}", response_model=MCPServerResponse)
async def update_mcp_server(
    server_id: str,
    data: MCPServerUpdate,
    mcp_manager=Depends(get_mcp_manager_optional),
):
    """Update an MCP server configuration."""
    if not mcp_manager:
        raise HTTPException(status_code=503, detail="MCP manager not available")

    # Build update dict
    updates = {}
    if data.name is not None:
        updates["name"] = data.name
    if data.description is not None:
        updates["description"] = data.description
    if data.enabled is not None:
        updates["enabled"] = data.enabled
    if data.command is not None:
        updates["command"] = data.command
    if data.args is not None:
        updates["args"] = data.args
    if data.url is not None:
        updates["url"] = data.url
    if data.env is not None:
        updates["env"] = data.env

    try:
        await mcp_manager.update_server(server_id, updates)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    # Get updated server
    servers = {s.id: s for s in mcp_manager.list_servers()}
    s = servers[server_id]

    return MCPServerResponse(
        id=s.id,
        name=s.name,
        description=s.description,
        type=s.type,
        command=s.command,
        args=s.args,
        url=s.url,
        enabled=s.enabled,
        built_in=s.built_in,
    )


@router.delete("/{server_id}")
async def delete_mcp_server(
    server_id: str,
    mcp_manager=Depends(get_mcp_manager_optional),
):
    """Delete an MCP server."""
    if not mcp_manager:
        raise HTTPException(status_code=503, detail="MCP manager not available")

    try:
        await mcp_manager.remove_server(server_id)
    except ValueError as e:
        if "built-in" in str(e).lower():
            raise HTTPException(status_code=403, detail=str(e))
        raise HTTPException(status_code=404, detail=str(e))

    return {"status": "deleted", "server_id": server_id}


@router.post("/{server_id}/enable")
async def enable_mcp_server(
    server_id: str,
    mcp_manager=Depends(get_mcp_manager_optional),
):
    """Enable an MCP server."""
    if not mcp_manager:
        raise HTTPException(status_code=503, detail="MCP manager not available")

    try:
        await mcp_manager.update_server(server_id, {"enabled": True})
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    return {"status": "enabled", "server_id": server_id}


@router.post("/{server_id}/disable")
async def disable_mcp_server(
    server_id: str,
    mcp_manager=Depends(get_mcp_manager_optional),
):
    """Disable an MCP server."""
    if not mcp_manager:
        raise HTTPException(status_code=503, detail="MCP manager not available")

    try:
        await mcp_manager.update_server(server_id, {"enabled": False})
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    return {"status": "disabled", "server_id": server_id}


# Tool definitions for each MCP server
MCP_TOOL_DEFINITIONS = {
    "mssql": {
        "list_tables": {"description": "Lists all tables in the connected database"},
        "describe_table": {"description": "Get schema information for a specific table"},
        "read_data": {"description": "Query and retrieve data from tables"},
        "insert_data": {"description": "Insert new rows into tables"},
        "update_data": {"description": "Modify existing data in tables"},
        "create_table": {"description": "Create new database tables"},
        "drop_table": {"description": "Delete tables from the database"},
        "create_index": {"description": "Create indexes for query optimization"},
    },
    "archon": {
        "find_projects": {"description": "List and search projects (list + search + get combined)"},
        "manage_project": {"description": "Create, update, delete, or move projects"},
        "find_tasks": {"description": "Find and search tasks with filtering options"},
        "manage_task": {"description": "Create, update, or delete tasks"},
        "find_documents": {"description": "Find and search documents within projects"},
        "manage_document": {"description": "Create, update, or delete documents"},
        "find_versions": {"description": "Find version history for project fields"},
        "manage_version": {"description": "Create or restore version snapshots"},
        "get_project_features": {"description": "Get features from a project's features field"},
        "rag_search_knowledge_base": {"description": "Search knowledge base using RAG"},
        "rag_search_code_examples": {"description": "Search for code examples in knowledge base"},
        "rag_get_available_sources": {"description": "List available sources in knowledge base"},
        "rag_list_pages_for_source": {"description": "List all pages for a knowledge source"},
        "rag_read_full_page": {"description": "Retrieve full page content from knowledge base"},
        "health_check": {"description": "Check Archon MCP server health status"},
        "session_info": {"description": "Get current session information"},
    },
    "microsoft.docs.mcp": {
        "search": {"description": "Search Microsoft Learn documentation"},
        "get_page": {"description": "Get content of a specific documentation page"},
        "list_products": {"description": "List available Microsoft products/services"},
        "get_toc": {"description": "Get table of contents for a documentation section"},
    },
    "analytics-management": {
        "list_dashboards": {
            "description": "List all dashboards with optional filtering by user or status"
        },
        "get_dashboard": {
            "description": "Get detailed information about a specific dashboard including its widgets"
        },
        "create_dashboard": {"description": "Create a new dashboard"},
        "update_dashboard": {"description": "Update an existing dashboard's properties"},
        "delete_dashboard": {"description": "Delete a dashboard and all its widgets"},
        "list_widgets": {"description": "List widgets for a dashboard"},
        "add_widget": {
            "description": "Add a new widget to a dashboard (bar, line, pie, kpi, table, etc.)"
        },
        "update_widget": {"description": "Update an existing widget"},
        "delete_widget": {"description": "Remove a widget from a dashboard"},
        "list_saved_queries": {"description": "List saved queries with optional filtering"},
        "save_query": {"description": "Save a query for later reuse"},
        "get_query_history": {"description": "Get recent query execution history"},
        "get_dashboard_metrics": {"description": "Get usage metrics for dashboards"},
        "get_usage_analytics": {"description": "Get overall system usage analytics"},
        "export_dashboard": {
            "description": "Export dashboard configuration as JSON for backup or sharing"
        },
        "import_dashboard": {"description": "Import a dashboard from JSON configuration"},
    },
    "data-analytics": {
        "descriptive_statistics": {
            "description": "Calculate descriptive statistics (mean, median, std dev, quartiles) for numeric columns"
        },
        "correlation_analysis": {
            "description": "Calculate correlation matrix between numeric columns using Pearson or Spearman method"
        },
        "percentile_analysis": {"description": "Calculate percentile values for a numeric column"},
        "group_aggregation": {
            "description": "Perform GROUP BY aggregations with multiple aggregate functions"
        },
        "pivot_analysis": {"description": "Create a pivot table summarization"},
        "time_series_analysis": {
            "description": "Analyze time series data for trends, patterns, and seasonality with moving averages"
        },
        "trend_detection": {
            "description": "Detect trends and calculate growth rates in time series data"
        },
        "profile_table": {
            "description": "Generate a comprehensive data profile (column types, nulls, cardinality, sample values)"
        },
        "column_distribution": {
            "description": "Analyze value distribution for a column (histograms for numeric, frequencies for categorical)"
        },
        "data_quality_check": {
            "description": "Check data quality issues: nulls, duplicates, outliers"
        },
        "detect_outliers": {
            "description": "Detect outliers in numeric columns using IQR or Z-score method"
        },
        "detect_anomalies_timeseries": {
            "description": "Detect anomalies in time series data using rolling statistics"
        },
        "segment_analysis": {"description": "Analyze data by segments with comparison metrics"},
        "cohort_analysis": {"description": "Perform cohort analysis based on date columns"},
        "run_analytics_query": {
            "description": "Execute a custom analytics SQL query (SELECT only)"
        },
    },
}


class MCPToolResponse(BaseModel):
    """Response model for MCP tool information."""

    name: str
    description: str


class MCPToolsListResponse(BaseModel):
    """Response model for MCP tools list."""

    server_id: str
    server_name: str
    tools: list[MCPToolResponse]
    total: int


@router.get("/{server_id}/tools", response_model=MCPToolsListResponse)
async def get_mcp_server_tools(
    server_id: str,
    mcp_manager=Depends(get_mcp_manager_optional),
):
    """Get list of tools available for a specific MCP server."""
    if not mcp_manager:
        raise HTTPException(status_code=503, detail="MCP manager not available")

    servers = {s.id: s for s in mcp_manager.list_servers()}
    if server_id not in servers:
        raise HTTPException(status_code=404, detail="Server not found")

    server = servers[server_id]
    tool_defs = MCP_TOOL_DEFINITIONS.get(server_id, {})

    tools = [
        MCPToolResponse(name=name, description=info.get("description", ""))
        for name, info in tool_defs.items()
    ]

    return MCPToolsListResponse(
        server_id=server_id,
        server_name=server.name,
        tools=tools,
        total=len(tools),
    )
