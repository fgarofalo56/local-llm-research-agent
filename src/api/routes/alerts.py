"""
Alerts Routes
Phase 2.5: Advanced Features & Polish

Endpoints for managing data alerts.
"""

from datetime import datetime

import structlog
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_db
from src.api.models.database import DataAlert

router = APIRouter()
logger = structlog.get_logger()


class AlertCreate(BaseModel):
    """Request model for creating an alert."""

    name: str
    query: str
    condition: str  # 'greater_than', 'less_than', 'equals', 'changes'
    threshold: float | None = None


class AlertUpdate(BaseModel):
    """Request model for updating an alert."""

    name: str | None = None
    query: str | None = None
    condition: str | None = None
    threshold: float | None = None
    is_active: bool | None = None


class AlertResponse(BaseModel):
    """Response model for an alert."""

    id: int
    name: str
    query: str
    condition: str
    threshold: float | None
    is_active: bool
    last_checked_at: datetime | None
    last_triggered_at: datetime | None
    last_value: str | None
    created_at: datetime

    class Config:
        from_attributes = True


class AlertListResponse(BaseModel):
    """Response model for alert list."""

    alerts: list[AlertResponse]
    total: int


class AlertCheckResponse(BaseModel):
    """Response model for manual alert check."""

    alert_id: int
    name: str | None = None
    current_value: float | None = None
    threshold: float | None = None
    condition: str | None = None
    triggered: bool | None = None
    status: str
    error: str | None = None


@router.get("", response_model=AlertListResponse)
async def list_alerts(
    skip: int = 0,
    limit: int = 50,
    active_only: bool = False,
    db: AsyncSession = Depends(get_db),
):
    """List all data alerts."""
    query = select(DataAlert)
    if active_only:
        query = query.where(DataAlert.is_active == True)  # noqa: E712

    # Get total
    count_result = await db.execute(query)
    total = len(count_result.scalars().all())

    # Get paginated results
    query = query.offset(skip).limit(limit).order_by(DataAlert.created_at.desc())
    result = await db.execute(query)
    alerts = result.scalars().all()

    return AlertListResponse(
        alerts=[
            AlertResponse(
                id=a.id,
                name=a.name,
                query=a.query,
                condition=a.condition,
                threshold=float(a.threshold) if a.threshold else None,
                is_active=a.is_active,
                last_checked_at=a.last_checked_at,
                last_triggered_at=a.last_triggered_at,
                last_value=a.last_value,
                created_at=a.created_at,
            )
            for a in alerts
        ],
        total=total,
    )


@router.post("", response_model=AlertResponse)
async def create_alert(
    data: AlertCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new data alert."""
    # Validate condition
    valid_conditions = ["greater_than", "less_than", "equals", "changes"]
    if data.condition not in valid_conditions:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid condition. Must be one of: {valid_conditions}",
        )

    alert = DataAlert(
        name=data.name,
        query=data.query,
        condition=data.condition,
        threshold=data.threshold,
    )
    db.add(alert)
    await db.commit()
    await db.refresh(alert)

    logger.info("alert_created", alert_id=alert.id, name=alert.name)

    return AlertResponse(
        id=alert.id,
        name=alert.name,
        query=alert.query,
        condition=alert.condition,
        threshold=float(alert.threshold) if alert.threshold else None,
        is_active=alert.is_active,
        last_checked_at=alert.last_checked_at,
        last_triggered_at=alert.last_triggered_at,
        last_value=alert.last_value,
        created_at=alert.created_at,
    )


@router.get("/{alert_id}", response_model=AlertResponse)
async def get_alert(
    alert_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get a specific data alert."""
    alert = await db.get(DataAlert, alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    return AlertResponse(
        id=alert.id,
        name=alert.name,
        query=alert.query,
        condition=alert.condition,
        threshold=float(alert.threshold) if alert.threshold else None,
        is_active=alert.is_active,
        last_checked_at=alert.last_checked_at,
        last_triggered_at=alert.last_triggered_at,
        last_value=alert.last_value,
        created_at=alert.created_at,
    )


@router.put("/{alert_id}", response_model=AlertResponse)
async def update_alert(
    alert_id: int,
    data: AlertUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update a data alert."""
    alert = await db.get(DataAlert, alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    # Validate condition if provided
    if data.condition:
        valid_conditions = ["greater_than", "less_than", "equals", "changes"]
        if data.condition not in valid_conditions:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid condition. Must be one of: {valid_conditions}",
            )

    # Update fields
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(alert, field, value)

    await db.commit()
    await db.refresh(alert)

    logger.info("alert_updated", alert_id=alert.id)

    return AlertResponse(
        id=alert.id,
        name=alert.name,
        query=alert.query,
        condition=alert.condition,
        threshold=float(alert.threshold) if alert.threshold else None,
        is_active=alert.is_active,
        last_checked_at=alert.last_checked_at,
        last_triggered_at=alert.last_triggered_at,
        last_value=alert.last_value,
        created_at=alert.created_at,
    )


@router.delete("/{alert_id}")
async def delete_alert(
    alert_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Delete a data alert."""
    alert = await db.get(DataAlert, alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    await db.delete(alert)
    await db.commit()

    logger.info("alert_deleted", alert_id=alert_id)

    return {"status": "deleted", "alert_id": alert_id}


@router.post("/{alert_id}/check", response_model=AlertCheckResponse)
async def check_alert(
    alert_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Manually trigger a check for a specific alert."""
    from src.api.deps import get_alert_scheduler

    scheduler = get_alert_scheduler()
    if scheduler is None:
        raise HTTPException(status_code=503, detail="Alert scheduler not available")

    result = await scheduler.check_alert_now(alert_id)

    if "error" in result and result.get("status") != "error":
        raise HTTPException(status_code=404, detail=result["error"])

    return AlertCheckResponse(**result)


@router.post("/{alert_id}/toggle")
async def toggle_alert(
    alert_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Toggle the active status of an alert."""
    alert = await db.get(DataAlert, alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    alert.is_active = not alert.is_active
    await db.commit()

    logger.info("alert_toggled", alert_id=alert_id, is_active=alert.is_active)

    return {"status": "toggled", "alert_id": alert_id, "is_active": alert.is_active}
