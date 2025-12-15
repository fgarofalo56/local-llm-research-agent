"""
Scheduled Queries Routes
Phase 2.5: Advanced Features & Polish

Endpoints for managing scheduled queries.
"""

from datetime import datetime

import structlog
from apscheduler.triggers.cron import CronTrigger
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_db
from src.api.models.database import ScheduledQuery

router = APIRouter()
logger = structlog.get_logger()


class ScheduledQueryCreate(BaseModel):
    """Request model for creating a scheduled query."""

    name: str
    query: str
    cron_expression: str  # e.g., "0 8 * * *" for 8am daily


class ScheduledQueryUpdate(BaseModel):
    """Request model for updating a scheduled query."""

    name: str | None = None
    query: str | None = None
    cron_expression: str | None = None
    is_active: bool | None = None


class ScheduledQueryResponse(BaseModel):
    """Response model for a scheduled query."""

    id: int
    name: str
    query: str
    cron_expression: str
    is_active: bool
    last_run_at: datetime | None
    next_run_at: datetime | None
    created_at: datetime

    class Config:
        from_attributes = True


class ScheduledQueryListResponse(BaseModel):
    """Response model for scheduled query list."""

    queries: list[ScheduledQueryResponse]
    total: int


class RunQueryResponse(BaseModel):
    """Response model for manual query execution."""

    query_id: int
    name: str | None = None
    row_count: int | None = None
    status: str
    error: str | None = None


def validate_cron(cron_expression: str) -> bool:
    """Validate a cron expression."""
    try:
        CronTrigger.from_crontab(cron_expression)
        return True
    except Exception:
        return False


def get_next_run_time(cron_expression: str) -> datetime | None:
    """Get the next run time for a cron expression."""
    try:
        trigger = CronTrigger.from_crontab(cron_expression)
        return trigger.get_next_fire_time(None, datetime.utcnow())
    except Exception:
        return None


@router.get("", response_model=ScheduledQueryListResponse)
async def list_scheduled_queries(
    skip: int = 0,
    limit: int = 50,
    active_only: bool = False,
    db: AsyncSession = Depends(get_db),
):
    """List all scheduled queries."""
    query = select(ScheduledQuery)
    if active_only:
        query = query.where(ScheduledQuery.is_active == True)  # noqa: E712

    # Get total
    count_result = await db.execute(query)
    total = len(count_result.scalars().all())

    # Get paginated results
    query = query.offset(skip).limit(limit).order_by(ScheduledQuery.created_at.desc())
    result = await db.execute(query)
    queries = result.scalars().all()

    return ScheduledQueryListResponse(
        queries=[ScheduledQueryResponse.model_validate(q) for q in queries],
        total=total,
    )


@router.post("", response_model=ScheduledQueryResponse)
async def create_scheduled_query(
    data: ScheduledQueryCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new scheduled query."""
    # Validate cron expression
    if not validate_cron(data.cron_expression):
        raise HTTPException(
            status_code=400,
            detail="Invalid cron expression. Use format: 'minute hour day month weekday'",
        )

    # Calculate next run time
    next_run = get_next_run_time(data.cron_expression)

    sq = ScheduledQuery(
        name=data.name,
        query=data.query,
        cron_expression=data.cron_expression,
        next_run_at=next_run,
    )
    db.add(sq)
    await db.commit()
    await db.refresh(sq)

    logger.info("scheduled_query_created", query_id=sq.id, name=sq.name)

    # Add to scheduler if running
    try:
        from src.api.deps import get_query_scheduler

        scheduler = get_query_scheduler()
        if scheduler and scheduler.is_running:
            await scheduler.add_scheduled_query(sq)
    except Exception as e:
        logger.warning("failed_to_add_to_scheduler", error=str(e))

    return ScheduledQueryResponse.model_validate(sq)


@router.get("/{query_id}", response_model=ScheduledQueryResponse)
async def get_scheduled_query(
    query_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get a specific scheduled query."""
    sq = await db.get(ScheduledQuery, query_id)
    if not sq:
        raise HTTPException(status_code=404, detail="Scheduled query not found")

    return ScheduledQueryResponse.model_validate(sq)


@router.put("/{query_id}", response_model=ScheduledQueryResponse)
async def update_scheduled_query(
    query_id: int,
    data: ScheduledQueryUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update a scheduled query."""
    sq = await db.get(ScheduledQuery, query_id)
    if not sq:
        raise HTTPException(status_code=404, detail="Scheduled query not found")

    # Validate cron expression if provided
    if data.cron_expression and not validate_cron(data.cron_expression):
        raise HTTPException(
            status_code=400,
            detail="Invalid cron expression. Use format: 'minute hour day month weekday'",
        )

    # Update fields
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(sq, field, value)

    # Update next run time if cron changed
    if data.cron_expression:
        sq.next_run_at = get_next_run_time(data.cron_expression)

    await db.commit()
    await db.refresh(sq)

    logger.info("scheduled_query_updated", query_id=sq.id)

    # Update in scheduler
    try:
        from src.api.deps import get_query_scheduler

        scheduler = get_query_scheduler()
        if scheduler and scheduler.is_running:
            await scheduler.update_scheduled_query(sq)
    except Exception as e:
        logger.warning("failed_to_update_in_scheduler", error=str(e))

    return ScheduledQueryResponse.model_validate(sq)


@router.delete("/{query_id}")
async def delete_scheduled_query(
    query_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Delete a scheduled query."""
    sq = await db.get(ScheduledQuery, query_id)
    if not sq:
        raise HTTPException(status_code=404, detail="Scheduled query not found")

    # Remove from scheduler
    try:
        from src.api.deps import get_query_scheduler

        scheduler = get_query_scheduler()
        if scheduler and scheduler.is_running:
            await scheduler.remove_scheduled_query(query_id)
    except Exception as e:
        logger.warning("failed_to_remove_from_scheduler", error=str(e))

    await db.delete(sq)
    await db.commit()

    logger.info("scheduled_query_deleted", query_id=query_id)

    return {"status": "deleted", "query_id": query_id}


@router.post("/{query_id}/run", response_model=RunQueryResponse)
async def run_scheduled_query(
    query_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Manually trigger a scheduled query execution."""
    from src.api.deps import get_query_scheduler

    scheduler = get_query_scheduler()
    if scheduler is None:
        raise HTTPException(status_code=503, detail="Query scheduler not available")

    result = await scheduler.run_query_now(query_id)

    if "error" in result and result.get("status") != "error":
        raise HTTPException(status_code=404, detail=result["error"])

    return RunQueryResponse(**result)


@router.post("/{query_id}/toggle")
async def toggle_scheduled_query(
    query_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Toggle the active status of a scheduled query."""
    sq = await db.get(ScheduledQuery, query_id)
    if not sq:
        raise HTTPException(status_code=404, detail="Scheduled query not found")

    sq.is_active = not sq.is_active

    # Update next run time
    if sq.is_active:
        sq.next_run_at = get_next_run_time(sq.cron_expression)
    else:
        sq.next_run_at = None

    await db.commit()

    logger.info("scheduled_query_toggled", query_id=query_id, is_active=sq.is_active)

    # Update in scheduler
    try:
        from src.api.deps import get_query_scheduler

        scheduler = get_query_scheduler()
        if scheduler and scheduler.is_running:
            await scheduler.update_scheduled_query(sq)
    except Exception as e:
        logger.warning("failed_to_update_in_scheduler", error=str(e))

    return {"status": "toggled", "query_id": query_id, "is_active": sq.is_active}


@router.post("/validate-cron")
async def validate_cron_expression(cron_expression: str):
    """Validate a cron expression and return the next run time."""
    if not validate_cron(cron_expression):
        raise HTTPException(
            status_code=400,
            detail="Invalid cron expression. Use format: 'minute hour day month weekday'",
        )

    next_run = get_next_run_time(cron_expression)
    return {
        "valid": True,
        "cron_expression": cron_expression,
        "next_run_at": next_run.isoformat() if next_run else None,
    }
