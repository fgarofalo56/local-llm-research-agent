"""
Dashboards Routes
Phase 2.1: Backend Infrastructure & RAG Pipeline

Endpoints for dashboard and widget management.
"""

import secrets
from datetime import datetime, timedelta

import structlog
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.api.deps import get_db
from src.api.models.database import Dashboard, DashboardWidget

router = APIRouter()
logger = structlog.get_logger()


# Widget Models
class WidgetCreate(BaseModel):
    """Request model for creating a widget."""

    widget_type: str
    title: str
    query: str | None = None
    chart_config: str | None = None  # JSON
    position: str | None = None  # JSON {x, y, w, h}
    refresh_interval: int | None = None


class WidgetResponse(BaseModel):
    """Response model for a widget."""

    id: int
    dashboard_id: int
    widget_type: str
    title: str
    query: str | None
    chart_config: str | None
    position: str | None
    refresh_interval: int | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Dashboard Models
class DashboardCreate(BaseModel):
    """Request model for creating a dashboard."""

    name: str
    description: str | None = None
    layout: str | None = None  # JSON


class DashboardResponse(BaseModel):
    """Response model for a dashboard."""

    id: int
    name: str
    description: str | None
    layout: str | None
    is_default: bool
    share_token: str | None
    share_expires_at: datetime | None
    created_at: datetime
    updated_at: datetime
    widget_count: int = 0

    class Config:
        from_attributes = True


class DashboardDetailResponse(DashboardResponse):
    """Response model for dashboard with widgets."""

    widgets: list[WidgetResponse] = []


class DashboardListResponse(BaseModel):
    """Response model for dashboard list."""

    dashboards: list[DashboardResponse]
    total: int


# Dashboard Endpoints
@router.get("", response_model=DashboardListResponse)
async def list_dashboards(
    skip: int = 0,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
):
    """List all dashboards."""
    query = select(Dashboard).options(selectinload(Dashboard.widgets))

    # Get total
    count_result = await db.execute(query)
    total = len(count_result.scalars().all())

    # Get paginated results
    query = query.offset(skip).limit(limit).order_by(Dashboard.updated_at.desc())
    result = await db.execute(query)
    dashboards = result.scalars().all()

    return DashboardListResponse(
        dashboards=[
            DashboardResponse(
                id=d.id,
                name=d.name,
                description=d.description,
                layout=d.layout,
                is_default=d.is_default,
                share_token=d.share_token,
                share_expires_at=d.share_expires_at,
                created_at=d.created_at,
                updated_at=d.updated_at,
                widget_count=len(d.widgets),
            )
            for d in dashboards
        ],
        total=total,
    )


@router.post("", response_model=DashboardResponse)
async def create_dashboard(
    data: DashboardCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new dashboard."""
    dashboard = Dashboard(
        name=data.name,
        description=data.description,
        layout=data.layout,
    )
    db.add(dashboard)
    await db.commit()
    await db.refresh(dashboard)

    return DashboardResponse(
        id=dashboard.id,
        name=dashboard.name,
        description=dashboard.description,
        layout=dashboard.layout,
        is_default=dashboard.is_default,
        share_token=dashboard.share_token,
        share_expires_at=dashboard.share_expires_at,
        created_at=dashboard.created_at,
        updated_at=dashboard.updated_at,
        widget_count=0,
    )


@router.get("/{dashboard_id}", response_model=DashboardDetailResponse)
async def get_dashboard(
    dashboard_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get a dashboard with all widgets."""
    query = (
        select(Dashboard)
        .options(selectinload(Dashboard.widgets))
        .where(Dashboard.id == dashboard_id)
    )
    result = await db.execute(query)
    dashboard = result.scalar_one_or_none()

    if not dashboard:
        raise HTTPException(status_code=404, detail="Dashboard not found")

    return DashboardDetailResponse(
        id=dashboard.id,
        name=dashboard.name,
        description=dashboard.description,
        layout=dashboard.layout,
        is_default=dashboard.is_default,
        share_token=dashboard.share_token,
        share_expires_at=dashboard.share_expires_at,
        created_at=dashboard.created_at,
        updated_at=dashboard.updated_at,
        widget_count=len(dashboard.widgets),
        widgets=[WidgetResponse.model_validate(w) for w in dashboard.widgets],
    )


@router.put("/{dashboard_id}", response_model=DashboardResponse)
async def update_dashboard(
    dashboard_id: int,
    data: DashboardCreate,
    db: AsyncSession = Depends(get_db),
):
    """Update a dashboard."""
    dashboard = await db.get(Dashboard, dashboard_id)
    if not dashboard:
        raise HTTPException(status_code=404, detail="Dashboard not found")

    dashboard.name = data.name
    dashboard.description = data.description
    dashboard.layout = data.layout
    dashboard.updated_at = datetime.utcnow()

    await db.commit()
    await db.refresh(dashboard)

    return DashboardResponse.model_validate(dashboard)


@router.delete("/{dashboard_id}")
async def delete_dashboard(
    dashboard_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Delete a dashboard and all its widgets."""
    dashboard = await db.get(Dashboard, dashboard_id)
    if not dashboard:
        raise HTTPException(status_code=404, detail="Dashboard not found")

    await db.delete(dashboard)
    await db.commit()

    return {"status": "deleted", "dashboard_id": dashboard_id}


@router.post("/{dashboard_id}/share")
async def create_share_link(
    dashboard_id: int,
    expires_hours: int = 24,
    db: AsyncSession = Depends(get_db),
):
    """Create a share link for a dashboard."""
    dashboard = await db.get(Dashboard, dashboard_id)
    if not dashboard:
        raise HTTPException(status_code=404, detail="Dashboard not found")

    # Generate token
    dashboard.share_token = secrets.token_urlsafe(32)
    dashboard.share_expires_at = datetime.utcnow() + timedelta(hours=expires_hours)

    await db.commit()

    return {
        "share_token": dashboard.share_token,
        "expires_at": dashboard.share_expires_at,
    }


# Widget Endpoints
@router.post("/{dashboard_id}/widgets", response_model=WidgetResponse)
async def create_widget(
    dashboard_id: int,
    data: WidgetCreate,
    db: AsyncSession = Depends(get_db),
):
    """Add a widget to a dashboard."""
    dashboard = await db.get(Dashboard, dashboard_id)
    if not dashboard:
        raise HTTPException(status_code=404, detail="Dashboard not found")

    widget = DashboardWidget(
        dashboard_id=dashboard_id,
        widget_type=data.widget_type,
        title=data.title,
        query=data.query,
        chart_config=data.chart_config,
        position=data.position,
        refresh_interval=data.refresh_interval,
    )
    db.add(widget)

    dashboard.updated_at = datetime.utcnow()

    await db.commit()
    await db.refresh(widget)

    return WidgetResponse.model_validate(widget)


@router.put("/{dashboard_id}/widgets/{widget_id}", response_model=WidgetResponse)
async def update_widget(
    dashboard_id: int,
    widget_id: int,
    data: WidgetCreate,
    db: AsyncSession = Depends(get_db),
):
    """Update a widget."""
    widget = await db.get(DashboardWidget, widget_id)
    if not widget or widget.dashboard_id != dashboard_id:
        raise HTTPException(status_code=404, detail="Widget not found")

    widget.widget_type = data.widget_type
    widget.title = data.title
    widget.query = data.query
    widget.chart_config = data.chart_config
    widget.position = data.position
    widget.refresh_interval = data.refresh_interval
    widget.updated_at = datetime.utcnow()

    await db.commit()
    await db.refresh(widget)

    return WidgetResponse.model_validate(widget)


@router.delete("/{dashboard_id}/widgets/{widget_id}")
async def delete_widget(
    dashboard_id: int,
    widget_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Delete a widget from a dashboard."""
    widget = await db.get(DashboardWidget, widget_id)
    if not widget or widget.dashboard_id != dashboard_id:
        raise HTTPException(status_code=404, detail="Widget not found")

    await db.delete(widget)
    await db.commit()

    return {"status": "deleted", "widget_id": widget_id}
