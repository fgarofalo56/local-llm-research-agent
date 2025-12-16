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
        if s.id == "mssql" and s.enabled:
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
