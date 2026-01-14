"""
Analytics Routes
Phase 4.5: Observability - Query Performance Metrics Dashboard

Endpoints for query performance metrics, system analytics, and monitoring.
"""

from datetime import datetime, timedelta
from typing import Literal

import structlog
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from redis.asyncio import Redis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_db, get_redis_optional

router = APIRouter()
logger = structlog.get_logger()


# ============================================================================
# Response Models
# ============================================================================


class QueryPerformanceStats(BaseModel):
    """Query performance statistics."""

    total_queries: int
    avg_execution_time_ms: float | None
    min_execution_time_ms: int | None
    max_execution_time_ms: int | None
    median_execution_time_ms: float | None
    total_rows_returned: int
    queries_today: int
    queries_this_week: int
    queries_this_month: int


class TimeSeriesPoint(BaseModel):
    """Single point in a time series."""

    timestamp: str
    value: float


class QueryTimeSeriesResponse(BaseModel):
    """Time series data for query performance."""

    period: str
    data: list[TimeSeriesPoint]
    avg_execution_time: float | None


class SlowQuery(BaseModel):
    """A slow query entry."""

    id: int
    natural_language: str
    generated_sql: str | None
    execution_time_ms: int
    row_count: int | None
    created_at: datetime


class TopSlowQueriesResponse(BaseModel):
    """Top slowest queries response."""

    queries: list[SlowQuery]
    threshold_ms: int


class CommonQuery(BaseModel):
    """Frequently executed query pattern."""

    pattern: str
    count: int
    avg_execution_time_ms: float | None


class ToolUsageStats(BaseModel):
    """MCP tool usage statistics."""

    tool_name: str
    usage_count: int
    percentage: float


class ToolUsageResponse(BaseModel):
    """Tool usage statistics response."""

    total_tool_calls: int
    tools: list[ToolUsageStats]


class CacheStats(BaseModel):
    """Cache statistics."""

    hits: int
    misses: int
    hit_rate: str
    evictions: int
    size: int
    max_size: int
    ttl_seconds: int


class SystemMetrics(BaseModel):
    """Overall system metrics."""

    total_conversations: int
    total_messages: int
    total_documents: int
    total_queries: int
    avg_messages_per_conversation: float
    active_mcp_servers: int
    database_status: str
    cache_status: str


class DashboardOverview(BaseModel):
    """Complete analytics dashboard overview."""

    query_stats: QueryPerformanceStats
    system_metrics: SystemMetrics
    cache_stats: CacheStats | None


# ============================================================================
# Endpoints
# ============================================================================


@router.get("/overview", response_model=DashboardOverview)
async def get_analytics_overview(
    db: AsyncSession = Depends(get_db),
    redis: Redis | None = Depends(get_redis_optional),
):
    """
    Get a complete analytics overview for the dashboard.

    Returns aggregated metrics for queries, system health, and cache performance.
    """

    now = datetime.utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_ago = now - timedelta(days=7)
    month_ago = now - timedelta(days=30)

    # Query performance stats
    query_stats_result = await db.execute(
        text("""
            SELECT
                COUNT(*) as total_queries,
                AVG(execution_time_ms) as avg_time,
                MIN(execution_time_ms) as min_time,
                MAX(execution_time_ms) as max_time,
                SUM(COALESCE(result_row_count, 0)) as total_rows
            FROM app.query_history
        """)
    )
    row = query_stats_result.fetchone()

    # Get queries by time period
    queries_today = await db.execute(
        text("SELECT COUNT(*) FROM app.query_history WHERE created_at >= :today"),
        {"today": today_start},
    )
    queries_week = await db.execute(
        text("SELECT COUNT(*) FROM app.query_history WHERE created_at >= :week_ago"),
        {"week_ago": week_ago},
    )
    queries_month = await db.execute(
        text("SELECT COUNT(*) FROM app.query_history WHERE created_at >= :month_ago"),
        {"month_ago": month_ago},
    )

    query_stats = QueryPerformanceStats(
        total_queries=row.total_queries if row else 0,
        avg_execution_time_ms=float(row.avg_time) if row and row.avg_time else None,
        min_execution_time_ms=row.min_time if row else None,
        max_execution_time_ms=row.max_time if row else None,
        median_execution_time_ms=None,  # Would require more complex query
        total_rows_returned=row.total_rows if row and row.total_rows else 0,
        queries_today=queries_today.scalar() or 0,
        queries_this_week=queries_week.scalar() or 0,
        queries_this_month=queries_month.scalar() or 0,
    )

    # System metrics
    conversations_count = await db.execute(text("SELECT COUNT(*) FROM app.conversations"))
    messages_count = await db.execute(text("SELECT COUNT(*) FROM app.messages"))
    documents_count = await db.execute(text("SELECT COUNT(*) FROM app.documents"))
    active_mcp = await db.execute(
        text("SELECT COUNT(*) FROM app.mcp_server_configs WHERE is_enabled = 1")
    )

    total_convs = conversations_count.scalar() or 0
    total_msgs = messages_count.scalar() or 0

    system_metrics = SystemMetrics(
        total_conversations=total_convs,
        total_messages=total_msgs,
        total_documents=documents_count.scalar() or 0,
        total_queries=row.total_queries if row else 0,
        avg_messages_per_conversation=(total_msgs / total_convs) if total_convs > 0 else 0,
        active_mcp_servers=active_mcp.scalar() or 0,
        database_status="connected",
        cache_status="connected" if redis else "disconnected",
    )

    # Cache stats (if Redis available)
    cache_stats = None
    if redis:
        try:
            info = await redis.info("stats")
            cache_stats = CacheStats(
                hits=info.get("keyspace_hits", 0),
                misses=info.get("keyspace_misses", 0),
                hit_rate=f"{(info.get('keyspace_hits', 0) / max(1, info.get('keyspace_hits', 0) + info.get('keyspace_misses', 0)) * 100):.1f}%",
                evictions=info.get("evicted_keys", 0),
                size=await redis.dbsize(),
                max_size=0,  # Redis doesn't have a fixed max size like our LRU cache
                ttl_seconds=0,
            )
        except Exception as e:
            logger.warning("failed_to_get_redis_stats", error=str(e))

    return DashboardOverview(
        query_stats=query_stats,
        system_metrics=system_metrics,
        cache_stats=cache_stats,
    )


@router.get("/queries/performance", response_model=QueryTimeSeriesResponse)
async def get_query_performance_timeline(
    period: Literal["hour", "day", "week", "month"] = Query(default="day"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get query execution time trends over time.

    Args:
        period: Time period for aggregation (hour, day, week, month)
    """
    now = datetime.utcnow()

    # Determine date range and grouping based on period
    if period == "hour":
        start_date = now - timedelta(hours=24)
        group_format = "DATEPART(HOUR, created_at)"
        interval = "hour"
    elif period == "day":
        start_date = now - timedelta(days=7)
        group_format = "CAST(created_at AS DATE)"
        interval = "day"
    elif period == "week":
        start_date = now - timedelta(weeks=4)
        group_format = "DATEPART(WEEK, created_at)"
        interval = "week"
    else:  # month
        start_date = now - timedelta(days=365)
        group_format = "FORMAT(created_at, 'yyyy-MM')"
        interval = "month"

    result = await db.execute(
        text(f"""
            SELECT
                {group_format} as time_bucket,
                AVG(execution_time_ms) as avg_time,
                COUNT(*) as query_count
            FROM app.query_history
            WHERE created_at >= :start_date
            GROUP BY {group_format}
            ORDER BY time_bucket
        """),
        {"start_date": start_date},
    )

    rows = result.fetchall()
    data = [
        TimeSeriesPoint(timestamp=str(row.time_bucket), value=float(row.avg_time or 0))
        for row in rows
    ]

    # Calculate overall average
    avg_result = await db.execute(
        text("""
            SELECT AVG(execution_time_ms) as avg_time
            FROM app.query_history
            WHERE created_at >= :start_date
        """),
        {"start_date": start_date},
    )
    avg_row = avg_result.fetchone()

    return QueryTimeSeriesResponse(
        period=period,
        data=data,
        avg_execution_time=float(avg_row.avg_time) if avg_row and avg_row.avg_time else None,
    )


@router.get("/queries/slow", response_model=TopSlowQueriesResponse)
async def get_slow_queries(
    limit: int = Query(default=10, ge=1, le=50),
    threshold_ms: int = Query(default=1000, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """
    Get the slowest queries above a threshold.

    Args:
        limit: Maximum number of queries to return
        threshold_ms: Minimum execution time to include (milliseconds)
    """
    result = await db.execute(
        text("""
            SELECT TOP (:limit)
                id, natural_language, generated_sql,
                execution_time_ms, result_row_count, created_at
            FROM app.query_history
            WHERE execution_time_ms >= :threshold
            ORDER BY execution_time_ms DESC
        """),
        {"limit": limit, "threshold": threshold_ms},
    )

    rows = result.fetchall()
    queries = [
        SlowQuery(
            id=row.id,
            natural_language=row.natural_language or "",
            generated_sql=row.generated_sql,
            execution_time_ms=row.execution_time_ms or 0,
            row_count=row.result_row_count,
            created_at=row.created_at,
        )
        for row in rows
    ]

    return TopSlowQueriesResponse(queries=queries, threshold_ms=threshold_ms)


@router.get("/queries/common", response_model=list[CommonQuery])
async def get_common_queries(
    limit: int = Query(default=10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    """
    Get most frequently executed query patterns.

    Identifies similar queries by natural language patterns.
    """
    # Get most common query patterns (simplified - uses first 100 chars)
    result = await db.execute(
        text("""
            SELECT TOP (:limit)
                LEFT(natural_language, 100) as pattern,
                COUNT(*) as count,
                AVG(execution_time_ms) as avg_time
            FROM app.query_history
            WHERE natural_language IS NOT NULL
            GROUP BY LEFT(natural_language, 100)
            ORDER BY COUNT(*) DESC
        """),
        {"limit": limit},
    )

    rows = result.fetchall()
    return [
        CommonQuery(
            pattern=row.pattern,
            count=row.count,
            avg_execution_time_ms=float(row.avg_time) if row.avg_time else None,
        )
        for row in rows
    ]


@router.get("/tools/usage", response_model=ToolUsageResponse)
async def get_tool_usage_stats(
    days: int = Query(default=30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
):
    """
    Get MCP tool usage statistics.

    Analyzes tool_calls from messages to determine tool usage patterns.
    """
    import json

    start_date = datetime.utcnow() - timedelta(days=days)

    # Get all messages with tool calls
    result = await db.execute(
        text("""
            SELECT tool_calls
            FROM app.messages
            WHERE tool_calls IS NOT NULL
            AND tool_calls != ''
            AND created_at >= :start_date
        """),
        {"start_date": start_date},
    )

    rows = result.fetchall()

    # Parse tool calls and count usage
    tool_counts: dict[str, int] = {}
    total_calls = 0

    for row in rows:
        try:
            if row.tool_calls:
                tool_calls = json.loads(row.tool_calls)
                if isinstance(tool_calls, list):
                    for call in tool_calls:
                        tool_name = call.get("name", call.get("tool_name", "unknown"))
                        tool_counts[tool_name] = tool_counts.get(tool_name, 0) + 1
                        total_calls += 1
        except json.JSONDecodeError:
            continue

    # Calculate percentages and create response
    tools = []
    for name, count in sorted(tool_counts.items(), key=lambda x: x[1], reverse=True):
        tools.append(
            ToolUsageStats(
                tool_name=name,
                usage_count=count,
                percentage=round((count / total_calls * 100) if total_calls > 0 else 0, 1),
            )
        )

    return ToolUsageResponse(total_tool_calls=total_calls, tools=tools)


@router.get("/cache/stats", response_model=CacheStats | None)
async def get_cache_stats(
    redis: Redis | None = Depends(get_redis_optional),
):
    """
    Get detailed cache statistics.

    Returns Redis cache metrics including hit rate and memory usage.
    """
    if not redis:
        return None

    try:
        info = await redis.info("stats")
        memory_info = await redis.info("memory")

        hits = info.get("keyspace_hits", 0)
        misses = info.get("keyspace_misses", 0)
        total = hits + misses

        return CacheStats(
            hits=hits,
            misses=misses,
            hit_rate=f"{(hits / max(1, total) * 100):.1f}%",
            evictions=info.get("evicted_keys", 0),
            size=await redis.dbsize(),
            max_size=0,
            ttl_seconds=0,
        )
    except Exception as e:
        logger.error("failed_to_get_cache_stats", error=str(e))
        return None


@router.get("/conversations/activity", response_model=list[TimeSeriesPoint])
async def get_conversation_activity(
    period: Literal["day", "week", "month"] = Query(default="week"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get conversation activity over time.

    Shows number of messages per time period.
    """
    now = datetime.utcnow()

    if period == "day":
        start_date = now - timedelta(days=1)
        group_format = "DATEPART(HOUR, created_at)"
    elif period == "week":
        start_date = now - timedelta(days=7)
        group_format = "CAST(created_at AS DATE)"
    else:  # month
        start_date = now - timedelta(days=30)
        group_format = "CAST(created_at AS DATE)"

    result = await db.execute(
        text(f"""
            SELECT
                {group_format} as time_bucket,
                COUNT(*) as message_count
            FROM app.messages
            WHERE created_at >= :start_date
            GROUP BY {group_format}
            ORDER BY time_bucket
        """),
        {"start_date": start_date},
    )

    rows = result.fetchall()
    return [
        TimeSeriesPoint(timestamp=str(row.time_bucket), value=float(row.message_count))
        for row in rows
    ]


@router.get("/documents/stats")
async def get_document_stats(
    db: AsyncSession = Depends(get_db),
):
    """
    Get document processing statistics.

    Returns counts by processing status and file type.
    """
    # Get counts by status
    status_result = await db.execute(
        text("""
            SELECT processing_status, COUNT(*) as count
            FROM app.documents
            GROUP BY processing_status
        """)
    )

    # Get counts by file type
    type_result = await db.execute(
        text("""
            SELECT
                CASE
                    WHEN mime_type LIKE '%pdf%' THEN 'PDF'
                    WHEN mime_type LIKE '%word%' OR mime_type LIKE '%docx%' THEN 'Word'
                    WHEN mime_type LIKE '%text%' THEN 'Text'
                    ELSE 'Other'
                END as file_type,
                COUNT(*) as count
            FROM app.documents
            GROUP BY CASE
                    WHEN mime_type LIKE '%pdf%' THEN 'PDF'
                    WHEN mime_type LIKE '%word%' OR mime_type LIKE '%docx%' THEN 'Word'
                    WHEN mime_type LIKE '%text%' THEN 'Text'
                    ELSE 'Other'
                END
        """)
    )

    # Get total chunks
    chunks_result = await db.execute(
        text("SELECT SUM(COALESCE(chunk_count, 0)) as total_chunks FROM app.documents")
    )

    status_rows = status_result.fetchall()
    type_rows = type_result.fetchall()
    total_chunks = chunks_result.scalar() or 0

    return {
        "by_status": {row.processing_status: row.count for row in status_rows},
        "by_type": {row.file_type: row.count for row in type_rows},
        "total_chunks": total_chunks,
    }
