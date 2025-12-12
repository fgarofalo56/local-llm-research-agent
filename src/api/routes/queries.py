"""
Queries Routes
Phase 2.1 & 2.3: Backend Infrastructure & Visualization

Endpoints for query history, saved queries, and query execution.
"""

import time
from datetime import datetime
from typing import Any

import structlog
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_db
from src.api.models.database import QueryHistory, SavedQuery

router = APIRouter()
logger = structlog.get_logger()


# Query Execution Models (Phase 2.3)
class QueryExecuteRequest(BaseModel):
    """Request model for executing a SQL query."""

    query: str


class QueryExecuteResponse(BaseModel):
    """Response model for query execution result."""

    data: list[dict[str, Any]]
    columns: list[str]
    row_count: int
    execution_time_ms: int


# Query History Models
class QueryHistoryResponse(BaseModel):
    """Response model for query history."""

    id: int
    conversation_id: int | None
    natural_language: str | None
    generated_sql: str | None
    result_row_count: int | None
    execution_time_ms: int | None
    is_favorite: bool
    created_at: datetime

    class Config:
        from_attributes = True


class QueryHistoryListResponse(BaseModel):
    """Response model for query history list."""

    queries: list[QueryHistoryResponse]
    total: int


# Saved Query Models
class SavedQueryCreate(BaseModel):
    """Request model for creating a saved query."""

    name: str
    description: str | None = None
    query: str
    tags: str | None = None  # JSON array


class SavedQueryResponse(BaseModel):
    """Response model for saved query."""

    id: int
    name: str
    description: str | None
    query: str
    tags: str | None
    created_at: datetime

    class Config:
        from_attributes = True


class SavedQueryListResponse(BaseModel):
    """Response model for saved query list."""

    queries: list[SavedQueryResponse]
    total: int


# Query Endpoints - "/" redirects to history for frontend compatibility
@router.get("", response_model=QueryHistoryListResponse)
async def list_queries(
    skip: int = 0,
    limit: int = 50,
    is_favorite: bool = False,
    db: AsyncSession = Depends(get_db),
):
    """List queries (alias for /history for frontend compatibility)."""
    return await list_query_history(skip, limit, is_favorite, db)


# Query History Endpoints
@router.get("/history", response_model=QueryHistoryListResponse)
async def list_query_history(
    skip: int = 0,
    limit: int = 50,
    favorites_only: bool = False,
    db: AsyncSession = Depends(get_db),
):
    """List query history."""
    query = select(QueryHistory)
    if favorites_only:
        query = query.where(QueryHistory.is_favorite == True)  # noqa: E712

    # Get total
    count_result = await db.execute(query)
    total = len(count_result.scalars().all())

    # Get paginated results
    query = query.offset(skip).limit(limit).order_by(QueryHistory.created_at.desc())
    result = await db.execute(query)
    queries = result.scalars().all()

    return QueryHistoryListResponse(
        queries=[QueryHistoryResponse.model_validate(q) for q in queries],
        total=total,
    )


@router.post("/history/{query_id}/favorite")
async def toggle_favorite(
    query_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Toggle favorite status for a query."""
    query_history = await db.get(QueryHistory, query_id)
    if not query_history:
        raise HTTPException(status_code=404, detail="Query not found")

    query_history.is_favorite = not query_history.is_favorite
    await db.commit()

    return {
        "status": "updated",
        "query_id": query_id,
        "is_favorite": query_history.is_favorite,
    }


@router.delete("/history/{query_id}")
async def delete_query_history(
    query_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Delete a query from history."""
    query_history = await db.get(QueryHistory, query_id)
    if not query_history:
        raise HTTPException(status_code=404, detail="Query not found")

    await db.delete(query_history)
    await db.commit()

    return {"status": "deleted", "query_id": query_id}


# Saved Query Endpoints
@router.get("/saved", response_model=SavedQueryListResponse)
async def list_saved_queries(
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
):
    """List saved queries."""
    query = select(SavedQuery)

    # Get total
    count_result = await db.execute(query)
    total = len(count_result.scalars().all())

    # Get paginated results
    query = query.offset(skip).limit(limit).order_by(SavedQuery.created_at.desc())
    result = await db.execute(query)
    queries = result.scalars().all()

    return SavedQueryListResponse(
        queries=[SavedQueryResponse.model_validate(q) for q in queries],
        total=total,
    )


@router.post("/saved", response_model=SavedQueryResponse)
async def create_saved_query(
    data: SavedQueryCreate,
    db: AsyncSession = Depends(get_db),
):
    """Save a query for reuse."""
    saved_query = SavedQuery(
        name=data.name,
        description=data.description,
        query=data.query,
        tags=data.tags,
    )
    db.add(saved_query)
    await db.commit()
    await db.refresh(saved_query)

    return SavedQueryResponse.model_validate(saved_query)


@router.get("/saved/{query_id}", response_model=SavedQueryResponse)
async def get_saved_query(
    query_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get a saved query."""
    saved_query = await db.get(SavedQuery, query_id)
    if not saved_query:
        raise HTTPException(status_code=404, detail="Query not found")

    return SavedQueryResponse.model_validate(saved_query)


@router.put("/saved/{query_id}", response_model=SavedQueryResponse)
async def update_saved_query(
    query_id: int,
    data: SavedQueryCreate,
    db: AsyncSession = Depends(get_db),
):
    """Update a saved query."""
    saved_query = await db.get(SavedQuery, query_id)
    if not saved_query:
        raise HTTPException(status_code=404, detail="Query not found")

    saved_query.name = data.name
    saved_query.description = data.description
    saved_query.query = data.query
    saved_query.tags = data.tags

    await db.commit()
    await db.refresh(saved_query)

    return SavedQueryResponse.model_validate(saved_query)


@router.delete("/saved/{query_id}")
async def delete_saved_query(
    query_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Delete a saved query."""
    saved_query = await db.get(SavedQuery, query_id)
    if not saved_query:
        raise HTTPException(status_code=404, detail="Query not found")

    await db.delete(saved_query)
    await db.commit()

    return {"status": "deleted", "query_id": query_id}


# Query Execution Endpoint (Phase 2.3)
@router.post("/execute", response_model=QueryExecuteResponse)
async def execute_query(
    data: QueryExecuteRequest,
    db: AsyncSession = Depends(get_db),
):
    """Execute a SQL query and return results.

    This endpoint allows executing arbitrary SELECT queries against the database.
    For security, only SELECT statements are allowed.
    """
    # Basic SQL injection prevention - only allow SELECT statements
    query_upper = data.query.strip().upper()
    if not query_upper.startswith("SELECT"):
        raise HTTPException(
            status_code=400,
            detail="Only SELECT statements are allowed for direct execution",
        )

    # Check for dangerous keywords
    dangerous_keywords = [
        "DROP",
        "DELETE",
        "TRUNCATE",
        "INSERT",
        "UPDATE",
        "ALTER",
        "CREATE",
        "EXEC",
        "EXECUTE",
    ]
    for keyword in dangerous_keywords:
        if keyword in query_upper:
            raise HTTPException(
                status_code=400,
                detail=f"Query contains forbidden keyword: {keyword}",
            )

    start_time = time.time()
    try:
        result = await db.execute(text(data.query))
        rows = result.fetchall()
        columns = list(result.keys())

        # Convert rows to list of dicts
        data_list = [dict(zip(columns, row, strict=False)) for row in rows]

        execution_time = int((time.time() - start_time) * 1000)

        await logger.ainfo(
            "query_executed",
            row_count=len(data_list),
            execution_time_ms=execution_time,
        )

        return QueryExecuteResponse(
            data=data_list,
            columns=columns,
            row_count=len(data_list),
            execution_time_ms=execution_time,
        )
    except Exception as e:
        await logger.aerror("query_execution_failed", error=str(e))
        raise HTTPException(status_code=400, detail=str(e))
