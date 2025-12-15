"""
Dashboards Routes
Phase 2.1 & 2.3: Backend Infrastructure & Visualization

Endpoints for dashboard and widget management.
"""

import contextlib
import json
import secrets
from datetime import datetime, timedelta
from typing import Any

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
class WidgetPosition(BaseModel):
    """Position and size for a widget."""

    x: int
    y: int
    w: int
    h: int


class WidgetChartConfig(BaseModel):
    """Chart configuration for a widget."""

    xKey: str | None = None
    yKeys: list[str] | None = None
    colors: list[str] | None = None


class WidgetCreate(BaseModel):
    """Request model for creating a widget."""

    widget_type: str
    title: str
    query: str | None = None
    chart_config: WidgetChartConfig | dict[str, Any] | None = None
    position: WidgetPosition | dict[str, Any] | None = None
    refresh_interval: int | None = None


class WidgetResponse(BaseModel):
    """Response model for a widget (raw JSON strings)."""

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


class WidgetListItem(BaseModel):
    """Response model for widget list item with parsed JSON."""

    id: int
    dashboard_id: int
    widget_type: str
    title: str
    query: str | None
    chart_config: dict[str, Any] | None
    position: dict[str, Any]
    refresh_interval: int | None

    class Config:
        from_attributes = True


class WidgetListResponse(BaseModel):
    """Response model for widget list."""

    widgets: list[WidgetListItem]


class LayoutUpdateItem(BaseModel):
    """Single widget layout update."""

    id: int
    position: WidgetPosition


class LayoutUpdateRequest(BaseModel):
    """Request model for batch layout update."""

    widgets: list[LayoutUpdateItem]


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


class ShareLinkRequest(BaseModel):
    """Request model for creating a share link."""

    expires_hours: int = 24
    is_public: bool = True


class ShareLinkResponse(BaseModel):
    """Response model for share link."""

    share_token: str
    share_url: str
    expires_at: datetime | None
    is_public: bool


@router.post("/{dashboard_id}/share", response_model=ShareLinkResponse)
async def create_share_link(
    dashboard_id: int,
    data: ShareLinkRequest | None = None,
    db: AsyncSession = Depends(get_db),
):
    """Create a share link for a dashboard."""
    dashboard = await db.get(Dashboard, dashboard_id)
    if not dashboard:
        raise HTTPException(status_code=404, detail="Dashboard not found")

    expires_hours = data.expires_hours if data else 24

    # Generate token
    dashboard.share_token = secrets.token_urlsafe(32)
    if expires_hours > 0:
        dashboard.share_expires_at = datetime.utcnow() + timedelta(hours=expires_hours)
    else:
        # Never expires
        dashboard.share_expires_at = None

    await db.commit()

    # Build share URL (frontend will construct actual URL)
    share_url = f"/shared/{dashboard.share_token}"

    return ShareLinkResponse(
        share_token=dashboard.share_token,
        share_url=share_url,
        expires_at=dashboard.share_expires_at,
        is_public=data.is_public if data else True,
    )


@router.delete("/{dashboard_id}/share")
async def revoke_share_link(
    dashboard_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Revoke the share link for a dashboard."""
    dashboard = await db.get(Dashboard, dashboard_id)
    if not dashboard:
        raise HTTPException(status_code=404, detail="Dashboard not found")

    dashboard.share_token = None
    dashboard.share_expires_at = None

    await db.commit()

    return {"status": "revoked", "dashboard_id": dashboard_id}


@router.get("/shared/{share_token}", response_model=DashboardDetailResponse)
async def get_shared_dashboard(
    share_token: str,
    db: AsyncSession = Depends(get_db),
):
    """Get a shared dashboard by its share token (public access)."""
    query = (
        select(Dashboard)
        .options(selectinload(Dashboard.widgets))
        .where(Dashboard.share_token == share_token)
    )
    result = await db.execute(query)
    dashboard = result.scalar_one_or_none()

    if not dashboard:
        raise HTTPException(status_code=404, detail="Shared dashboard not found")

    # Check if share has expired
    if dashboard.share_expires_at and dashboard.share_expires_at < datetime.utcnow():
        raise HTTPException(status_code=410, detail="Share link has expired")

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


# Widget Endpoints
@router.post("/{dashboard_id}/widgets", response_model=WidgetListItem)
async def create_widget(
    dashboard_id: int,
    data: WidgetCreate,
    db: AsyncSession = Depends(get_db),
):
    """Add a widget to a dashboard."""
    dashboard = await db.get(Dashboard, dashboard_id)
    if not dashboard:
        raise HTTPException(status_code=404, detail="Dashboard not found")

    # Convert chart_config to JSON string
    chart_config_str = None
    if data.chart_config:
        if isinstance(data.chart_config, dict):
            chart_config_str = json.dumps(data.chart_config)
        else:
            chart_config_str = json.dumps(data.chart_config.model_dump())

    # Convert position to JSON string
    position_str = json.dumps({"x": 0, "y": 0, "w": 4, "h": 3})  # Default
    if data.position:
        if isinstance(data.position, dict):
            position_str = json.dumps(data.position)
        else:
            position_str = json.dumps(data.position.model_dump())

    widget = DashboardWidget(
        dashboard_id=dashboard_id,
        widget_type=data.widget_type,
        title=data.title,
        query=data.query,
        chart_config=chart_config_str,
        position=position_str,
        refresh_interval=data.refresh_interval,
    )
    db.add(widget)

    dashboard.updated_at = datetime.utcnow()

    await db.commit()
    await db.refresh(widget)

    # Return with parsed JSON
    return WidgetListItem(
        id=widget.id,
        dashboard_id=widget.dashboard_id,
        widget_type=widget.widget_type,
        title=widget.title,
        query=widget.query,
        chart_config=json.loads(widget.chart_config) if widget.chart_config else None,
        position=json.loads(widget.position)
        if widget.position
        else {"x": 0, "y": 0, "w": 4, "h": 3},
        refresh_interval=widget.refresh_interval,
    )


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


# Additional Endpoints for Phase 2.3
@router.get("/{dashboard_id}/widgets", response_model=WidgetListResponse)
async def list_dashboard_widgets(
    dashboard_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get all widgets for a specific dashboard with parsed JSON fields."""
    # Verify dashboard exists
    dashboard = await db.get(Dashboard, dashboard_id)
    if not dashboard:
        raise HTTPException(status_code=404, detail="Dashboard not found")

    query = select(DashboardWidget).where(DashboardWidget.dashboard_id == dashboard_id)
    result = await db.execute(query)
    widgets = result.scalars().all()

    widget_list = []
    for w in widgets:
        # Parse JSON fields
        chart_config = None
        if w.chart_config:
            try:
                chart_config = json.loads(w.chart_config)
            except json.JSONDecodeError:
                chart_config = {}

        position = {"x": 0, "y": 0, "w": 4, "h": 3}  # Default position
        if w.position:
            with contextlib.suppress(json.JSONDecodeError):
                position = json.loads(w.position)

        widget_list.append(
            WidgetListItem(
                id=w.id,
                dashboard_id=w.dashboard_id,
                widget_type=w.widget_type,
                title=w.title,
                query=w.query,
                chart_config=chart_config,
                position=position,
                refresh_interval=w.refresh_interval,
            )
        )

    return WidgetListResponse(widgets=widget_list)


@router.put("/{dashboard_id}/layout")
async def update_dashboard_layout(
    dashboard_id: int,
    data: LayoutUpdateRequest,
    db: AsyncSession = Depends(get_db),
):
    """Batch update widget positions for a dashboard."""
    # Verify dashboard exists
    dashboard = await db.get(Dashboard, dashboard_id)
    if not dashboard:
        raise HTTPException(status_code=404, detail="Dashboard not found")

    updated_count = 0
    for widget_update in data.widgets:
        widget = await db.get(DashboardWidget, widget_update.id)
        if widget and widget.dashboard_id == dashboard_id:
            widget.position = json.dumps(widget_update.position.model_dump())
            widget.updated_at = datetime.utcnow()
            updated_count += 1

    dashboard.updated_at = datetime.utcnow()
    await db.commit()

    return {"status": "updated", "widgets_updated": updated_count}
