"""
Superset Integration Routes
Phase 3: Enterprise BI Platform Integration

Endpoints for interacting with Apache Superset:
- List dashboards
- Get embed URLs with guest tokens
- Health check
"""

import os
from typing import Any

import httpx
import structlog
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()
logger = structlog.get_logger()

# Superset configuration from environment
SUPERSET_URL = os.getenv("SUPERSET_URL", "http://localhost:8088")
SUPERSET_USER = os.getenv("SUPERSET_ADMIN_USER", "admin")
SUPERSET_PASS = os.getenv("SUPERSET_ADMIN_PASSWORD", "LocalLLM@2024!")


class EmbedResponse(BaseModel):
    """Response with embedded dashboard URL."""

    embed_url: str
    dashboard_id: str


class SupersetDashboard(BaseModel):
    """Superset dashboard metadata."""

    id: int
    dashboard_title: str
    slug: str | None = None
    description: str | None = None
    published: bool = False
    charts: list[dict[str, Any]] | None = None
    created_on: str | None = None
    changed_on: str | None = None


class DashboardListResponse(BaseModel):
    """List of Superset dashboards."""

    dashboards: list[SupersetDashboard]
    count: int


class SupersetHealthResponse(BaseModel):
    """Superset health status."""

    status: str
    url: str
    error: str | None = None


async def get_superset_token() -> str:
    """
    Login to Superset and get access token.

    Returns:
        JWT access token for Superset API

    Raises:
        HTTPException: If authentication fails
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{SUPERSET_URL}/api/v1/security/login",
                json={
                    "username": SUPERSET_USER,
                    "password": SUPERSET_PASS,
                    "provider": "db",
                    "refresh": True,
                },
            )
            if response.status_code != 200:
                logger.error(
                    "superset_auth_failed",
                    status=response.status_code,
                    body=response.text[:200],
                )
                raise HTTPException(status_code=500, detail="Failed to authenticate with Superset")
            return response.json()["access_token"]
    except httpx.RequestError as e:
        logger.error("superset_connection_error", error=str(e))
        raise HTTPException(status_code=503, detail=f"Cannot connect to Superset: {str(e)}")


@router.get("/health", response_model=SupersetHealthResponse)
async def superset_health() -> SupersetHealthResponse:
    """
    Check Superset health status.

    Returns health status of the Superset service.
    """
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{SUPERSET_URL}/health")
            if response.status_code == 200:
                return SupersetHealthResponse(status="healthy", url=SUPERSET_URL)
            return SupersetHealthResponse(
                status="unhealthy",
                url=SUPERSET_URL,
                error=f"HTTP {response.status_code}",
            )
    except httpx.RequestError as e:
        return SupersetHealthResponse(status="unhealthy", url=SUPERSET_URL, error=str(e))


@router.get("/dashboards", response_model=DashboardListResponse)
async def list_dashboards() -> DashboardListResponse:
    """
    List all available Superset dashboards.

    Returns a list of dashboards with their metadata.
    """
    token = await get_superset_token()

    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(
            f"{SUPERSET_URL}/api/v1/dashboard/",
            headers={"Authorization": f"Bearer {token}"},
        )

        if response.status_code != 200:
            logger.error(
                "superset_dashboards_failed",
                status=response.status_code,
                body=response.text[:200],
            )
            raise HTTPException(
                status_code=response.status_code,
                detail="Failed to fetch dashboards from Superset",
            )

        data = response.json()
        dashboards = [
            SupersetDashboard(
                id=d.get("id"),
                dashboard_title=d.get("dashboard_title", "Untitled"),
                slug=d.get("slug"),
                description=d.get("description"),
                published=d.get("published", False),
                charts=d.get("charts"),
                created_on=d.get("created_on"),
                changed_on=d.get("changed_on"),
            )
            for d in data.get("result", [])
        ]

        return DashboardListResponse(dashboards=dashboards, count=len(dashboards))


@router.get("/embed/{dashboard_id}", response_model=EmbedResponse)
async def get_embed_url(dashboard_id: int) -> EmbedResponse:
    """
    Get embeddable URL for a dashboard with guest token.

    Args:
        dashboard_id: The ID of the dashboard to embed

    Returns:
        EmbedResponse with the embed URL and dashboard ID
    """
    token = await get_superset_token()

    async with httpx.AsyncClient(timeout=10.0) as client:
        # First verify the dashboard exists
        dash_response = await client.get(
            f"{SUPERSET_URL}/api/v1/dashboard/{dashboard_id}",
            headers={"Authorization": f"Bearer {token}"},
        )

        if dash_response.status_code != 200:
            raise HTTPException(status_code=404, detail=f"Dashboard {dashboard_id} not found")

        # Create guest token for embedding
        guest_response = await client.post(
            f"{SUPERSET_URL}/api/v1/security/guest_token/",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "user": {
                    "username": "embed_user",
                    "first_name": "Embed",
                    "last_name": "User",
                },
                "resources": [{"type": "dashboard", "id": str(dashboard_id)}],
                "rls": [],
            },
        )

        if guest_response.status_code != 200:
            logger.error(
                "superset_guest_token_failed",
                status=guest_response.status_code,
                body=guest_response.text[:200],
            )
            raise HTTPException(
                status_code=500, detail="Failed to create guest token for embedding"
            )

        guest_token = guest_response.json()["token"]

    embed_url = f"{SUPERSET_URL}/embedded/{dashboard_id}?guest_token={guest_token}"

    return EmbedResponse(embed_url=embed_url, dashboard_id=str(dashboard_id))


@router.get("/charts")
async def list_charts() -> dict[str, Any]:
    """
    List all available Superset charts.

    Returns a list of charts that can be used in dashboards.
    """
    token = await get_superset_token()

    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(
            f"{SUPERSET_URL}/api/v1/chart/",
            headers={"Authorization": f"Bearer {token}"},
        )

        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code,
                detail="Failed to fetch charts from Superset",
            )

        return response.json()


@router.get("/databases")
async def list_databases() -> dict[str, Any]:
    """
    List configured database connections in Superset.

    Returns databases that can be used for SQL Lab queries.
    """
    token = await get_superset_token()

    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(
            f"{SUPERSET_URL}/api/v1/database/",
            headers={"Authorization": f"Bearer {token}"},
        )

        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code,
                detail="Failed to fetch databases from Superset",
            )

        return response.json()
