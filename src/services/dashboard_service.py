"""
Dashboard Service
Phase 2.1 & 2.3: Backend Infrastructure & Visualization

Business logic for dashboard and widget management operations.
Extracted from src/api/routes/dashboards.py to separate concerns.
"""

import contextlib
import json
import secrets
from datetime import datetime, timedelta
from typing import Any

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.api.models.database import Dashboard, DashboardWidget

logger = structlog.get_logger()


class DashboardService:
    """Service for dashboard and widget management operations."""

    def __init__(self):
        """Initialize dashboard service."""
        pass

    async def list_dashboards(
        self,
        db: AsyncSession,
        skip: int = 0,
        limit: int = 20,
    ) -> tuple[list[Dashboard], int]:
        """List all dashboards with pagination.

        Args:
            db: Database session.
            skip: Number of dashboards to skip (pagination).
            limit: Maximum number of dashboards to return.

        Returns:
            Tuple of (list of dashboards with widgets loaded, total count).
        """
        query = select(Dashboard).options(selectinload(Dashboard.widgets))

        # Get total count
        count_result = await db.execute(query)
        total = len(count_result.scalars().all())

        # Get paginated results
        query = query.offset(skip).limit(limit).order_by(Dashboard.updated_at.desc())
        result = await db.execute(query)
        dashboards = result.scalars().all()

        return dashboards, total

    async def get_dashboard(
        self,
        db: AsyncSession,
        dashboard_id: int,
    ) -> Dashboard | None:
        """Get a specific dashboard with all widgets.

        Args:
            db: Database session.
            dashboard_id: ID of the dashboard to retrieve.

        Returns:
            Dashboard instance with widgets loaded, or None if not found.
        """
        query = (
            select(Dashboard)
            .options(selectinload(Dashboard.widgets))
            .where(Dashboard.id == dashboard_id)
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def create_dashboard(
        self,
        db: AsyncSession,
        name: str,
        description: str | None = None,
        layout: str | None = None,
    ) -> Dashboard:
        """Create a new dashboard.

        Args:
            db: Database session.
            name: Dashboard name.
            description: Optional dashboard description.
            layout: Optional JSON layout configuration.

        Returns:
            Created Dashboard instance.
        """
        dashboard = Dashboard(
            name=name,
            description=description,
            layout=layout,
        )
        db.add(dashboard)
        await db.commit()
        await db.refresh(dashboard)
        return dashboard

    async def update_dashboard(
        self,
        db: AsyncSession,
        dashboard_id: int,
        name: str,
        description: str | None = None,
        layout: str | None = None,
    ) -> Dashboard | None:
        """Update an existing dashboard.

        Args:
            db: Database session.
            dashboard_id: ID of the dashboard to update.
            name: New dashboard name.
            description: New dashboard description.
            layout: New JSON layout configuration.

        Returns:
            Updated Dashboard instance or None if not found.
        """
        dashboard = await db.get(Dashboard, dashboard_id)
        if not dashboard:
            return None

        dashboard.name = name
        dashboard.description = description
        dashboard.layout = layout
        dashboard.updated_at = datetime.utcnow()

        await db.commit()
        await db.refresh(dashboard)

        return dashboard

    async def delete_dashboard(
        self,
        db: AsyncSession,
        dashboard_id: int,
    ) -> bool:
        """Delete a dashboard and all its widgets.

        Args:
            db: Database session.
            dashboard_id: ID of the dashboard to delete.

        Returns:
            True if deleted successfully, False if not found.
        """
        dashboard = await db.get(Dashboard, dashboard_id)
        if not dashboard:
            return False

        await db.delete(dashboard)
        await db.commit()

        return True

    async def create_share_link(
        self,
        db: AsyncSession,
        dashboard_id: int,
        expires_hours: int = 24,
    ) -> tuple[str, str, datetime | None] | None:
        """Create a share link for a dashboard.

        Args:
            db: Database session.
            dashboard_id: ID of the dashboard to share.
            expires_hours: Number of hours until link expires (0 = never expires).

        Returns:
            Tuple of (share_token, share_url, expires_at) or None if dashboard not found.
        """
        dashboard = await db.get(Dashboard, dashboard_id)
        if not dashboard:
            return None

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

        return dashboard.share_token, share_url, dashboard.share_expires_at

    async def revoke_share_link(
        self,
        db: AsyncSession,
        dashboard_id: int,
    ) -> bool:
        """Revoke the share link for a dashboard.

        Args:
            db: Database session.
            dashboard_id: ID of the dashboard.

        Returns:
            True if revoked successfully, False if not found.
        """
        dashboard = await db.get(Dashboard, dashboard_id)
        if not dashboard:
            return False

        dashboard.share_token = None
        dashboard.share_expires_at = None

        await db.commit()

        return True

    async def get_shared_dashboard(
        self,
        db: AsyncSession,
        share_token: str,
    ) -> tuple[Dashboard | None, str | None]:
        """Get a shared dashboard by its share token.

        Args:
            db: Database session.
            share_token: Share token to look up.

        Returns:
            Tuple of (Dashboard instance or None, error message or None).
        """
        query = (
            select(Dashboard)
            .options(selectinload(Dashboard.widgets))
            .where(Dashboard.share_token == share_token)
        )
        result = await db.execute(query)
        dashboard = result.scalar_one_or_none()

        if not dashboard:
            return None, "Shared dashboard not found"

        # Check if share has expired
        if dashboard.share_expires_at and dashboard.share_expires_at < datetime.utcnow():
            return None, "Share link has expired"

        return dashboard, None

    # Widget operations

    async def list_dashboard_widgets(
        self,
        db: AsyncSession,
        dashboard_id: int,
    ) -> tuple[list[DashboardWidget], bool]:
        """Get all widgets for a specific dashboard.

        Args:
            db: Database session.
            dashboard_id: ID of the dashboard.

        Returns:
            Tuple of (list of widgets, dashboard_exists flag).
        """
        # Verify dashboard exists
        dashboard = await db.get(Dashboard, dashboard_id)
        if not dashboard:
            return [], False

        query = select(DashboardWidget).where(DashboardWidget.dashboard_id == dashboard_id)
        result = await db.execute(query)
        widgets = result.scalars().all()

        return widgets, True

    async def create_widget(
        self,
        db: AsyncSession,
        dashboard_id: int,
        widget_type: str,
        title: str,
        query: str | None = None,
        chart_config: dict[str, Any] | None = None,
        position: dict[str, Any] | None = None,
        refresh_interval: int | None = None,
    ) -> DashboardWidget | None:
        """Add a widget to a dashboard.

        Args:
            db: Database session.
            dashboard_id: ID of the dashboard.
            widget_type: Type of widget ('chart', 'kpi', 'table').
            title: Widget title.
            query: SQL query for the widget.
            chart_config: Chart configuration dict.
            position: Position dict {x, y, w, h}.
            refresh_interval: Refresh interval in seconds.

        Returns:
            Created DashboardWidget instance or None if dashboard not found.
        """
        dashboard = await db.get(Dashboard, dashboard_id)
        if not dashboard:
            return None

        # Convert chart_config to JSON string
        chart_config_str = None
        if chart_config:
            chart_config_str = json.dumps(chart_config)

        # Convert position to JSON string with default
        position_str = json.dumps(position or {"x": 0, "y": 0, "w": 4, "h": 3})

        widget = DashboardWidget(
            dashboard_id=dashboard_id,
            widget_type=widget_type,
            title=title,
            query=query,
            chart_config=chart_config_str,
            position=position_str,
            refresh_interval=refresh_interval,
        )
        db.add(widget)

        dashboard.updated_at = datetime.utcnow()

        await db.commit()
        await db.refresh(widget)

        return widget

    async def update_widget(
        self,
        db: AsyncSession,
        dashboard_id: int,
        widget_id: int,
        widget_type: str,
        title: str,
        query: str | None = None,
        chart_config: Any = None,
        position: Any = None,
        refresh_interval: int | None = None,
    ) -> DashboardWidget | None:
        """Update a widget.

        Args:
            db: Database session.
            dashboard_id: ID of the dashboard (for verification).
            widget_id: ID of the widget to update.
            widget_type: Type of widget.
            title: Widget title.
            query: SQL query for the widget.
            chart_config: Chart configuration (dict or JSON string).
            position: Position (dict or JSON string).
            refresh_interval: Refresh interval in seconds.

        Returns:
            Updated DashboardWidget instance or None if not found.
        """
        widget = await db.get(DashboardWidget, widget_id)
        if not widget or widget.dashboard_id != dashboard_id:
            return None

        widget.widget_type = widget_type
        widget.title = title
        widget.query = query
        widget.chart_config = chart_config
        widget.position = position
        widget.refresh_interval = refresh_interval
        widget.updated_at = datetime.utcnow()

        await db.commit()
        await db.refresh(widget)

        return widget

    async def delete_widget(
        self,
        db: AsyncSession,
        dashboard_id: int,
        widget_id: int,
    ) -> bool:
        """Delete a widget from a dashboard.

        Args:
            db: Database session.
            dashboard_id: ID of the dashboard (for verification).
            widget_id: ID of the widget to delete.

        Returns:
            True if deleted successfully, False if not found.
        """
        widget = await db.get(DashboardWidget, widget_id)
        if not widget or widget.dashboard_id != dashboard_id:
            return False

        await db.delete(widget)
        await db.commit()

        return True

    async def update_dashboard_layout(
        self,
        db: AsyncSession,
        dashboard_id: int,
        widget_updates: list[tuple[int, dict[str, Any]]],
    ) -> tuple[int, bool]:
        """Batch update widget positions for a dashboard.

        Args:
            db: Database session.
            dashboard_id: ID of the dashboard.
            widget_updates: List of (widget_id, position_dict) tuples.

        Returns:
            Tuple of (number of widgets updated, dashboard_exists flag).
        """
        # Verify dashboard exists
        dashboard = await db.get(Dashboard, dashboard_id)
        if not dashboard:
            return 0, False

        updated_count = 0
        for widget_id, position in widget_updates:
            widget = await db.get(DashboardWidget, widget_id)
            if widget and widget.dashboard_id == dashboard_id:
                widget.position = json.dumps(position)
                widget.updated_at = datetime.utcnow()
                updated_count += 1

        dashboard.updated_at = datetime.utcnow()
        await db.commit()

        return updated_count, True

    @staticmethod
    def parse_widget_json_fields(
        widget: DashboardWidget,
    ) -> tuple[dict[str, Any] | None, dict[str, Any]]:
        """Parse JSON fields from a widget for response serialization.

        Args:
            widget: DashboardWidget instance with JSON string fields.

        Returns:
            Tuple of (chart_config dict or None, position dict with defaults).
        """
        # Parse chart_config
        chart_config = None
        if widget.chart_config:
            try:
                chart_config = json.loads(widget.chart_config)
            except json.JSONDecodeError:
                chart_config = {}

        # Parse position with default
        position = {"x": 0, "y": 0, "w": 4, "h": 3}
        if widget.position:
            with contextlib.suppress(json.JSONDecodeError):
                position = json.loads(widget.position)

        return chart_config, position
