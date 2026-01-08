"""
Query Profiler
Phase 2.1: Backend Infrastructure & RAG Pipeline

SQLAlchemy query performance profiler using event listeners.
Logs slow queries and provides aggregate statistics.
"""

import logging
import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any

from sqlalchemy import event
from sqlalchemy.engine import Engine

logger = logging.getLogger(__name__)


@dataclass
class QueryStats:
    """Query execution statistics."""

    total_queries: int = 0
    total_time_ms: float = 0.0
    slow_queries: int = 0
    avg_time_ms: float = 0.0
    min_time_ms: float = float("inf")
    max_time_ms: float = 0.0
    queries_by_table: dict[str, int] = field(default_factory=lambda: defaultdict(int))
    slow_query_log: list[dict[str, Any]] = field(default_factory=list)


class QueryProfiler:
    """SQLAlchemy query profiler with slow query detection."""

    def __init__(self, slow_query_threshold_ms: int = 100, max_slow_queries: int = 100):
        """
        Initialize query profiler.

        Args:
            slow_query_threshold_ms: Queries slower than this are logged (default: 100ms)
            max_slow_queries: Maximum number of slow queries to retain (default: 100)
        """
        self.slow_query_threshold_ms = slow_query_threshold_ms
        self.max_slow_queries = max_slow_queries
        self.stats = QueryStats()
        self._query_start_times: dict[Any, float] = {}

    def enable(self, engine: Engine) -> None:
        """
        Enable query profiling on a SQLAlchemy engine.

        Args:
            engine: SQLAlchemy engine to profile
        """
        event.listen(engine, "before_cursor_execute", self._before_cursor_execute)
        event.listen(engine, "after_cursor_execute", self._after_cursor_execute)
        logger.info(
            f"Query profiler enabled (slow query threshold: {self.slow_query_threshold_ms}ms)"
        )

    def disable(self, engine: Engine) -> None:
        """
        Disable query profiling on a SQLAlchemy engine.

        Args:
            engine: SQLAlchemy engine to stop profiling
        """
        event.remove(engine, "before_cursor_execute", self._before_cursor_execute)
        event.remove(engine, "after_cursor_execute", self._after_cursor_execute)
        logger.info("Query profiler disabled")

    def _before_cursor_execute(
        self,
        conn: Any,
        cursor: Any,
        statement: str,
        parameters: Any,
        context: Any,
        executemany: bool,
    ) -> None:
        """Event listener: Called before query execution."""
        conn_id = id(conn)
        self._query_start_times[conn_id] = time.perf_counter()

    def _after_cursor_execute(
        self,
        conn: Any,
        cursor: Any,
        statement: str,
        parameters: Any,
        context: Any,
        executemany: bool,
    ) -> None:
        """Event listener: Called after query execution."""
        conn_id = id(conn)
        start_time = self._query_start_times.pop(conn_id, None)

        if start_time is None:
            return

        # Calculate execution time
        execution_time = time.perf_counter() - start_time
        execution_time_ms = execution_time * 1000

        # Update statistics
        self.stats.total_queries += 1
        self.stats.total_time_ms += execution_time_ms
        self.stats.avg_time_ms = self.stats.total_time_ms / self.stats.total_queries
        self.stats.min_time_ms = min(self.stats.min_time_ms, execution_time_ms)
        self.stats.max_time_ms = max(self.stats.max_time_ms, execution_time_ms)

        # Track queries by table (simple heuristic)
        self._track_table_usage(statement)

        # Log slow queries
        if execution_time_ms >= self.slow_query_threshold_ms:
            self._log_slow_query(statement, parameters, execution_time_ms)

    def _track_table_usage(self, statement: str) -> None:
        """Track which tables are being queried (simple heuristic)."""
        statement_upper = statement.upper()

        # Look for common table patterns
        for keyword in ["FROM", "JOIN", "INTO", "UPDATE"]:
            if keyword in statement_upper:
                parts = statement_upper.split(keyword)
                if len(parts) > 1:
                    # Extract table name (first word after keyword)
                    table_part = parts[1].strip().split()[0]
                    # Clean up table name
                    table_name = table_part.strip("(),[]").lower()
                    if table_name and not table_name.startswith("("):
                        self.stats.queries_by_table[table_name] += 1

    def _log_slow_query(self, statement: str, parameters: Any, execution_time_ms: float) -> None:
        """Log a slow query."""
        self.stats.slow_queries += 1

        # Create slow query record
        slow_query = {
            "statement": statement,
            "parameters": str(parameters) if parameters else None,
            "execution_time_ms": round(execution_time_ms, 2),
            "timestamp": time.time(),
        }

        # Add to slow query log (keep only most recent)
        self.stats.slow_query_log.append(slow_query)
        if len(self.stats.slow_query_log) > self.max_slow_queries:
            self.stats.slow_query_log.pop(0)

        # Log warning
        logger.warning(f"Slow query detected ({execution_time_ms:.2f}ms): {statement[:200]}")

    def get_stats(self) -> dict[str, Any]:
        """
        Get current profiling statistics.

        Returns:
            Dictionary with profiling statistics
        """
        return {
            "total_queries": self.stats.total_queries,
            "total_time_ms": round(self.stats.total_time_ms, 2),
            "avg_time_ms": round(self.stats.avg_time_ms, 2),
            "min_time_ms": round(self.stats.min_time_ms, 2)
            if self.stats.min_time_ms != float("inf")
            else 0.0,
            "max_time_ms": round(self.stats.max_time_ms, 2),
            "slow_queries": self.stats.slow_queries,
            "slow_query_threshold_ms": self.slow_query_threshold_ms,
            "queries_by_table": dict(self.stats.queries_by_table),
            "top_tables": sorted(
                self.stats.queries_by_table.items(), key=lambda x: x[1], reverse=True
            )[:10],
        }

    def get_slow_queries(self, limit: int = 20) -> list[dict[str, Any]]:
        """
        Get recent slow queries.

        Args:
            limit: Maximum number of slow queries to return

        Returns:
            List of slow query records
        """
        return self.stats.slow_query_log[-limit:]

    def reset(self) -> None:
        """Reset all profiling statistics."""
        self.stats = QueryStats()
        self._query_start_times.clear()
        logger.info("Query profiler statistics reset")


# Global profiler instance
_profiler: QueryProfiler | None = None


def get_profiler(slow_query_threshold_ms: int = 100, max_slow_queries: int = 100) -> QueryProfiler:
    """
    Get or create the global query profiler instance.

    Args:
        slow_query_threshold_ms: Threshold for slow query logging
        max_slow_queries: Maximum number of slow queries to retain

    Returns:
        QueryProfiler instance
    """
    global _profiler
    if _profiler is None:
        _profiler = QueryProfiler(
            slow_query_threshold_ms=slow_query_threshold_ms,
            max_slow_queries=max_slow_queries,
        )
    return _profiler


def enable_profiling(engine: Engine, slow_query_threshold_ms: int = 100) -> None:
    """
    Enable query profiling on an engine.

    Args:
        engine: SQLAlchemy engine
        slow_query_threshold_ms: Threshold for slow query logging
    """
    profiler = get_profiler(slow_query_threshold_ms=slow_query_threshold_ms)
    profiler.enable(engine)


def disable_profiling(engine: Engine) -> None:
    """
    Disable query profiling on an engine.

    Args:
        engine: SQLAlchemy engine
    """
    profiler = get_profiler()
    profiler.disable(engine)


def get_stats() -> dict[str, Any]:
    """Get current profiling statistics."""
    profiler = get_profiler()
    return profiler.get_stats()


def get_slow_queries(limit: int = 20) -> list[dict[str, Any]]:
    """Get recent slow queries."""
    profiler = get_profiler()
    return profiler.get_slow_queries(limit=limit)


def reset_stats() -> None:
    """Reset profiling statistics."""
    profiler = get_profiler()
    profiler.reset()
