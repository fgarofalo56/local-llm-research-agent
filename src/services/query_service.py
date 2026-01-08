"""
Query Service
Phase 2.1 & 2.3: Backend Infrastructure & Visualization

Business logic for query history, saved queries, and query execution operations.
Extracted from src/api/routes/queries.py to separate concerns.
"""

import time
from typing import Any

import structlog
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.models.database import QueryHistory, SavedQuery

logger = structlog.get_logger()


class QueryService:
    """Service for query history, saved queries, and execution operations."""

    # SQL injection prevention - dangerous keywords to block
    DANGEROUS_KEYWORDS = [
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

    def __init__(self):
        """Initialize query service."""
        pass

    # Query History operations

    async def list_query_history(
        self,
        db: AsyncSession,
        skip: int = 0,
        limit: int = 50,
        favorites_only: bool = False,
    ) -> tuple[list[QueryHistory], int]:
        """List query history with optional filtering.

        Args:
            db: Database session.
            skip: Number of queries to skip (pagination).
            limit: Maximum number of queries to return.
            favorites_only: If True, only return favorited queries.

        Returns:
            Tuple of (list of query history items, total count).
        """
        query = select(QueryHistory)
        if favorites_only:
            query = query.where(QueryHistory.is_favorite == True)  # noqa: E712

        # Get total count
        count_result = await db.execute(query)
        total = len(count_result.scalars().all())

        # Get paginated results
        query = query.offset(skip).limit(limit).order_by(QueryHistory.created_at.desc())
        result = await db.execute(query)
        queries = result.scalars().all()

        return queries, total

    async def toggle_favorite(
        self,
        db: AsyncSession,
        query_id: int,
    ) -> tuple[bool, bool]:
        """Toggle favorite status for a query.

        Args:
            db: Database session.
            query_id: ID of the query to toggle.

        Returns:
            Tuple of (new favorite status, query_exists flag).
        """
        query_history = await db.get(QueryHistory, query_id)
        if not query_history:
            return False, False

        query_history.is_favorite = not query_history.is_favorite
        await db.commit()

        return query_history.is_favorite, True

    async def delete_query_history(
        self,
        db: AsyncSession,
        query_id: int,
    ) -> bool:
        """Delete a query from history.

        Args:
            db: Database session.
            query_id: ID of the query to delete.

        Returns:
            True if deleted successfully, False if not found.
        """
        query_history = await db.get(QueryHistory, query_id)
        if not query_history:
            return False

        await db.delete(query_history)
        await db.commit()

        return True

    async def create_query_history(
        self,
        db: AsyncSession,
        conversation_id: int | None,
        natural_language: str | None,
        generated_sql: str | None,
        result_row_count: int | None,
        execution_time_ms: int | None,
    ) -> QueryHistory:
        """Create a new query history record.

        Args:
            db: Database session.
            conversation_id: Optional conversation ID.
            natural_language: Original natural language query.
            generated_sql: Generated SQL query.
            result_row_count: Number of rows returned.
            execution_time_ms: Execution time in milliseconds.

        Returns:
            Created QueryHistory instance.
        """
        query_history = QueryHistory(
            conversation_id=conversation_id,
            natural_language=natural_language,
            generated_sql=generated_sql,
            result_row_count=result_row_count,
            execution_time_ms=execution_time_ms,
        )
        db.add(query_history)
        await db.commit()
        await db.refresh(query_history)

        return query_history

    # Saved Query operations

    async def list_saved_queries(
        self,
        db: AsyncSession,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[SavedQuery], int]:
        """List saved queries with pagination.

        Args:
            db: Database session.
            skip: Number of queries to skip (pagination).
            limit: Maximum number of queries to return.

        Returns:
            Tuple of (list of saved queries, total count).
        """
        query = select(SavedQuery)

        # Get total count
        count_result = await db.execute(query)
        total = len(count_result.scalars().all())

        # Get paginated results
        query = query.offset(skip).limit(limit).order_by(SavedQuery.created_at.desc())
        result = await db.execute(query)
        queries = result.scalars().all()

        return queries, total

    async def get_saved_query(
        self,
        db: AsyncSession,
        query_id: int,
    ) -> SavedQuery | None:
        """Get a specific saved query.

        Args:
            db: Database session.
            query_id: ID of the saved query.

        Returns:
            SavedQuery instance or None if not found.
        """
        return await db.get(SavedQuery, query_id)

    async def create_saved_query(
        self,
        db: AsyncSession,
        name: str,
        query: str,
        description: str | None = None,
        tags: str | None = None,
    ) -> SavedQuery:
        """Save a query for reuse.

        Args:
            db: Database session.
            name: Query name.
            query: SQL query text.
            description: Optional description.
            tags: Optional JSON array of tags.

        Returns:
            Created SavedQuery instance.
        """
        saved_query = SavedQuery(
            name=name,
            description=description,
            query=query,
            tags=tags,
        )
        db.add(saved_query)
        await db.commit()
        await db.refresh(saved_query)

        return saved_query

    async def update_saved_query(
        self,
        db: AsyncSession,
        query_id: int,
        name: str,
        query: str,
        description: str | None = None,
        tags: str | None = None,
    ) -> SavedQuery | None:
        """Update a saved query.

        Args:
            db: Database session.
            query_id: ID of the query to update.
            name: New query name.
            query: New SQL query text.
            description: New description.
            tags: New JSON array of tags.

        Returns:
            Updated SavedQuery instance or None if not found.
        """
        saved_query = await db.get(SavedQuery, query_id)
        if not saved_query:
            return None

        saved_query.name = name
        saved_query.description = description
        saved_query.query = query
        saved_query.tags = tags

        await db.commit()
        await db.refresh(saved_query)

        return saved_query

    async def delete_saved_query(
        self,
        db: AsyncSession,
        query_id: int,
    ) -> bool:
        """Delete a saved query.

        Args:
            db: Database session.
            query_id: ID of the query to delete.

        Returns:
            True if deleted successfully, False if not found.
        """
        saved_query = await db.get(SavedQuery, query_id)
        if not saved_query:
            return False

        await db.delete(saved_query)
        await db.commit()

        return True

    # Query Execution operations

    @staticmethod
    def validate_query(query: str) -> tuple[bool, str | None]:
        """Validate a SQL query for safe execution.

        Only SELECT statements are allowed, and queries are checked for
        dangerous keywords that could modify data.

        Args:
            query: SQL query to validate.

        Returns:
            Tuple of (is_valid, error_message).
        """
        # Basic SQL injection prevention - only allow SELECT statements
        query_upper = query.strip().upper()
        if not query_upper.startswith("SELECT"):
            return False, "Only SELECT statements are allowed for direct execution"

        # Check for dangerous keywords
        for keyword in QueryService.DANGEROUS_KEYWORDS:
            if keyword in query_upper:
                return False, f"Query contains forbidden keyword: {keyword}"

        return True, None

    async def execute_query(
        self,
        db: AsyncSession,
        query: str,
    ) -> tuple[list[dict[str, Any]], list[str], int, int] | tuple[None, None, None, str]:
        """Execute a SQL query and return results.

        This method validates the query for safety before execution.
        Only SELECT statements are allowed.

        Args:
            db: Database session.
            query: SQL query to execute.

        Returns:
            Tuple of (data list, columns list, row_count, execution_time_ms) on success,
            or (None, None, None, error_message) on failure.
        """
        # Validate query
        is_valid, error_msg = self.validate_query(query)
        if not is_valid:
            return None, None, None, error_msg

        start_time = time.time()
        try:
            result = await db.execute(text(query))
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

            return data_list, columns, len(data_list), execution_time

        except Exception as e:
            error_message = str(e)
            await logger.aerror("query_execution_failed", error=error_message)
            return None, None, None, error_message
