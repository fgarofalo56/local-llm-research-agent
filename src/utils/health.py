"""
Health Check Utilities

Provides health check functionality to verify connectivity and status
of LLM providers, MCP servers, and database connections.
"""

import asyncio
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

import httpx

from src.utils.config import settings
from src.utils.logger import get_logger

logger = get_logger(__name__)


class HealthStatus(str, Enum):
    """Health check status values."""

    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    DEGRADED = "degraded"
    UNKNOWN = "unknown"


@dataclass
class ComponentHealth:
    """Health status of a single component."""

    name: str
    status: HealthStatus
    message: str = ""
    latency_ms: float | None = None
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        result = {
            "name": self.name,
            "status": self.status.value,
            "message": self.message,
        }
        if self.latency_ms is not None:
            result["latency_ms"] = round(self.latency_ms, 2)
        if self.details:
            result["details"] = self.details
        return result


@dataclass
class SystemHealth:
    """Overall system health status."""

    status: HealthStatus
    components: list[ComponentHealth] = field(default_factory=list)
    timestamp: str = ""

    def __post_init__(self) -> None:
        from datetime import datetime

        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "status": self.status.value,
            "timestamp": self.timestamp,
            "components": [c.to_dict() for c in self.components],
        }

    @property
    def is_healthy(self) -> bool:
        """Check if system is healthy."""
        return self.status == HealthStatus.HEALTHY


async def check_ollama_health() -> ComponentHealth:
    """
    Check Ollama server health.

    Returns:
        ComponentHealth with Ollama status
    """
    start_time = time.monotonic()
    name = "ollama"

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            # Check Ollama API endpoint
            response = await client.get(f"{settings.ollama_host}/api/tags")
            latency_ms = (time.monotonic() - start_time) * 1000

            if response.status_code == 200:
                data = response.json()
                models = data.get("models", [])
                model_names = [m.get("name", "") for m in models]

                # Check if configured model is available
                target_model = settings.ollama_model
                model_available = any(
                    target_model in m or m.startswith(target_model.split(":")[0])
                    for m in model_names
                )

                if model_available:
                    return ComponentHealth(
                        name=name,
                        status=HealthStatus.HEALTHY,
                        message=f"Connected, model '{target_model}' available",
                        latency_ms=latency_ms,
                        details={
                            "host": settings.ollama_host,
                            "model": target_model,
                            "available_models": model_names[:5],  # Limit for display
                        },
                    )
                else:
                    return ComponentHealth(
                        name=name,
                        status=HealthStatus.DEGRADED,
                        message=f"Connected, but model '{target_model}' not found",
                        latency_ms=latency_ms,
                        details={
                            "host": settings.ollama_host,
                            "model": target_model,
                            "available_models": model_names[:5],
                        },
                    )
            else:
                return ComponentHealth(
                    name=name,
                    status=HealthStatus.UNHEALTHY,
                    message=f"HTTP {response.status_code}",
                    latency_ms=latency_ms,
                )

    except httpx.ConnectError:
        return ComponentHealth(
            name=name,
            status=HealthStatus.UNHEALTHY,
            message=f"Cannot connect to {settings.ollama_host}",
        )
    except httpx.TimeoutException:
        return ComponentHealth(
            name=name,
            status=HealthStatus.UNHEALTHY,
            message="Connection timeout",
        )
    except Exception as e:
        return ComponentHealth(
            name=name,
            status=HealthStatus.UNHEALTHY,
            message=f"Error: {str(e)}",
        )


async def check_foundry_local_health() -> ComponentHealth:
    """
    Check Foundry Local server health.

    Returns:
        ComponentHealth with Foundry Local status
    """
    start_time = time.monotonic()
    name = "foundry_local"

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            # Check Foundry Local API endpoint
            response = await client.get(f"{settings.foundry_endpoint}/v1/models")
            latency_ms = (time.monotonic() - start_time) * 1000

            if response.status_code == 200:
                data = response.json()
                models = data.get("data", [])
                model_ids = [m.get("id", "") for m in models]

                return ComponentHealth(
                    name=name,
                    status=HealthStatus.HEALTHY,
                    message=f"Connected, {len(model_ids)} models available",
                    latency_ms=latency_ms,
                    details={
                        "endpoint": settings.foundry_endpoint,
                        "models": model_ids[:5],
                    },
                )
            else:
                return ComponentHealth(
                    name=name,
                    status=HealthStatus.UNHEALTHY,
                    message=f"HTTP {response.status_code}",
                    latency_ms=latency_ms,
                )

    except httpx.ConnectError:
        return ComponentHealth(
            name=name,
            status=HealthStatus.UNKNOWN,
            message=f"Not running at {settings.foundry_endpoint}",
        )
    except httpx.TimeoutException:
        return ComponentHealth(
            name=name,
            status=HealthStatus.UNHEALTHY,
            message="Connection timeout",
        )
    except Exception as e:
        return ComponentHealth(
            name=name,
            status=HealthStatus.UNHEALTHY,
            message=f"Error: {str(e)}",
        )


async def check_mcp_server_health() -> ComponentHealth:
    """
    Check MCP server availability.

    Returns:
        ComponentHealth with MCP server status
    """
    name = "mcp_server"

    try:
        from pathlib import Path

        mcp_path = settings.mcp_mssql_path

        if not mcp_path:
            return ComponentHealth(
                name=name,
                status=HealthStatus.UNKNOWN,
                message="MCP_MSSQL_PATH not configured",
            )

        path = Path(mcp_path)
        if not path.exists():
            return ComponentHealth(
                name=name,
                status=HealthStatus.UNHEALTHY,
                message=f"Server not found at {mcp_path}",
            )

        return ComponentHealth(
            name=name,
            status=HealthStatus.HEALTHY,
            message="Server executable found",
            details={
                "path": str(path),
                "readonly": settings.mcp_mssql_readonly,
            },
        )

    except Exception as e:
        return ComponentHealth(
            name=name,
            status=HealthStatus.UNHEALTHY,
            message=f"Error: {str(e)}",
        )


async def check_database_health() -> ComponentHealth:
    """
    Check database connectivity via MCP server.

    This performs a lightweight check by attempting to list tables.

    Returns:
        ComponentHealth with database status
    """
    start_time = time.monotonic()
    name = "database"

    try:
        from src.mcp.client import MCPClientManager

        mcp_manager = MCPClientManager()
        mssql_server = mcp_manager.get_mssql_server()

        # Try to connect and list tools (lightweight check)
        async with mssql_server:
            tools = await mssql_server.list_tools()
            latency_ms = (time.monotonic() - start_time) * 1000

            tool_names = [t.name for t in tools]

            return ComponentHealth(
                name=name,
                status=HealthStatus.HEALTHY,
                message=f"Connected, {len(tools)} tools available",
                latency_ms=latency_ms,
                details={
                    "server": settings.mcp_mssql_server,
                    "database": settings.mcp_mssql_database,
                    "tools": tool_names,
                },
            )

    except Exception as e:
        latency_ms = (time.monotonic() - start_time) * 1000
        return ComponentHealth(
            name=name,
            status=HealthStatus.UNHEALTHY,
            message=f"Connection failed: {str(e)[:100]}",
            latency_ms=latency_ms,
            details={
                "server": settings.mcp_mssql_server,
                "database": settings.mcp_mssql_database,
            },
        )


async def run_health_checks(
    include_database: bool = False,
) -> SystemHealth:
    """
    Run all health checks and return system health.

    Args:
        include_database: Include database connectivity check (slower)

    Returns:
        SystemHealth with all component statuses
    """
    logger.info("health_check_started")

    # Run LLM provider checks in parallel
    tasks = [
        check_ollama_health(),
        check_foundry_local_health(),
        check_mcp_server_health(),
    ]

    if include_database:
        tasks.append(check_database_health())

    results = await asyncio.gather(*tasks)
    components = list(results)

    # Determine overall status
    statuses = [c.status for c in components]

    if all(s == HealthStatus.HEALTHY for s in statuses):
        overall = HealthStatus.HEALTHY
    elif all(s == HealthStatus.UNHEALTHY for s in statuses):
        overall = HealthStatus.UNHEALTHY
    elif any(s == HealthStatus.UNHEALTHY for s in statuses) or any(
        s == HealthStatus.DEGRADED for s in statuses
    ):
        overall = HealthStatus.DEGRADED
    else:
        overall = HealthStatus.UNKNOWN

    health = SystemHealth(status=overall, components=components)

    logger.info(
        "health_check_completed",
        status=overall.value,
        components=len(components),
    )

    return health


async def quick_health_check() -> bool:
    """
    Perform a quick health check (Ollama only).

    Returns:
        True if essential services are healthy
    """
    ollama = await check_ollama_health()
    return ollama.status == HealthStatus.HEALTHY


def format_health_report(health: SystemHealth, verbose: bool = False) -> str:
    """
    Format health check results as a string report.

    Args:
        health: SystemHealth results
        verbose: Include detailed information

    Returns:
        Formatted report string
    """
    lines = [
        "System Health Report",
        "=" * 40,
        f"Overall Status: {health.status.value.upper()}",
        f"Timestamp: {health.timestamp}",
        "",
        "Components:",
        "-" * 40,
    ]

    status_icons = {
        HealthStatus.HEALTHY: "[OK]",
        HealthStatus.UNHEALTHY: "[FAIL]",
        HealthStatus.DEGRADED: "[WARN]",
        HealthStatus.UNKNOWN: "[?]",
    }

    for component in health.components:
        icon = status_icons.get(component.status, "[?]")
        latency = f" ({component.latency_ms:.0f}ms)" if component.latency_ms else ""
        lines.append(f"  {icon} {component.name}: {component.message}{latency}")

        if verbose and component.details:
            for key, value in component.details.items():
                if isinstance(value, list):
                    value = ", ".join(str(v) for v in value[:3])
                    if len(component.details[key]) > 3:
                        value += "..."
                lines.append(f"      {key}: {value}")

    lines.append("")
    lines.append("=" * 40)

    return "\n".join(lines)
