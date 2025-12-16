"""
Health Check Routes
Phase 2.1: Backend Infrastructure & RAG Pipeline

Endpoints for checking the health of all services.
"""

import time

import httpx
import structlog
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from redis.asyncio import Redis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_db, get_mcp_manager_optional, get_redis_optional
from src.utils.config import get_settings

router = APIRouter()
logger = structlog.get_logger()


class ServiceHealth(BaseModel):
    """Health status for a single service."""

    name: str
    status: str  # 'healthy', 'unhealthy', 'unknown'
    message: str | None = None
    latency_ms: float | None = None


class HealthResponse(BaseModel):
    """Overall health response."""

    status: str  # 'healthy', 'degraded', 'unhealthy'
    services: list[ServiceHealth]


@router.get("", response_model=HealthResponse)
async def health_check(
    db: AsyncSession = Depends(get_db),
    redis: Redis | None = Depends(get_redis_optional),
):
    """
    Check health of all services.

    Returns overall status and individual service health.
    """
    import os

    services = []
    unhealthy_count = 0
    settings = get_settings()
    superset_url = os.getenv("SUPERSET_URL", "http://localhost:8088")

    # Check SQL Server
    try:
        start = time.time()
        await db.execute(text("SELECT 1"))
        latency = (time.time() - start) * 1000
        services.append(
            ServiceHealth(
                name="sql_server",
                status="healthy",
                latency_ms=round(latency, 2),
            )
        )
    except Exception as e:
        unhealthy_count += 1
        services.append(
            ServiceHealth(
                name="sql_server",
                status="unhealthy",
                message=str(e)[:200],
            )
        )

    # Check Redis
    if redis:
        try:
            start = time.time()
            await redis.ping()
            latency = (time.time() - start) * 1000
            services.append(
                ServiceHealth(
                    name="redis",
                    status="healthy",
                    latency_ms=round(latency, 2),
                )
            )
        except Exception as e:
            unhealthy_count += 1
            services.append(
                ServiceHealth(
                    name="redis",
                    status="unhealthy",
                    message=str(e)[:200],
                )
            )
    else:
        services.append(
            ServiceHealth(
                name="redis",
                status="unknown",
                message="Redis client not initialized",
            )
        )

    # Check Ollama
    try:
        start = time.time()
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{settings.ollama_host}/api/tags",
                timeout=5.0,
            )
            response.raise_for_status()
        latency = (time.time() - start) * 1000
        services.append(
            ServiceHealth(
                name="ollama",
                status="healthy",
                latency_ms=round(latency, 2),
            )
        )
    except Exception as e:
        unhealthy_count += 1
        services.append(
            ServiceHealth(
                name="ollama",
                status="unhealthy",
                message=str(e)[:200],
            )
        )

    # Check Superset (optional service - doesn't count as unhealthy if not running)
    try:
        start = time.time()
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{superset_url}/health",
                timeout=5.0,
            )
            response.raise_for_status()
        latency = (time.time() - start) * 1000
        services.append(
            ServiceHealth(
                name="superset",
                status="healthy",
                latency_ms=round(latency, 2),
            )
        )
    except Exception as e:
        # Superset is optional, so we mark it as unknown rather than unhealthy
        services.append(
            ServiceHealth(
                name="superset",
                status="unknown",
                message=f"Not available: {str(e)[:100]}",
            )
        )

    # Determine overall status
    if unhealthy_count == 0:
        overall_status = "healthy"
    elif unhealthy_count < len(services):
        overall_status = "degraded"
    else:
        overall_status = "unhealthy"

    return HealthResponse(status=overall_status, services=services)


@router.get("/ready")
async def readiness_check():
    """
    Simple readiness check.

    Returns 200 when the API is ready to accept requests.
    Used by Kubernetes readiness probes.
    """
    return {"status": "ready"}


@router.get("/live")
async def liveness_check():
    """
    Simple liveness check.

    Returns 200 when the API is alive.
    Used by Kubernetes liveness probes.
    """
    return {"status": "alive"}


@router.get("/services")
async def services_status(
    redis: Redis | None = Depends(get_redis_optional),
    mcp_manager=Depends(get_mcp_manager_optional),
):
    """
    Get detailed status of all configured services.

    Includes MCP servers and their status.
    """
    services = {
        "api": {"status": "running", "version": "2.1.0"},
        "redis": {"status": "connected" if redis else "disconnected"},
        "mcp_servers": [],
    }

    # Add MCP server info if available
    if mcp_manager:
        try:
            for server in mcp_manager.list_servers():
                services["mcp_servers"].append(
                    {
                        "id": server.id,
                        "name": server.name,
                        "type": server.type,
                        "enabled": server.enabled,
                    }
                )
        except Exception as e:
            logger.warning("mcp_servers_status_error", error=str(e))

    return services
