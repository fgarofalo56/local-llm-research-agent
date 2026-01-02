"""
Tests for Query Profiler
Phase 2.1: Backend Infrastructure & RAG Pipeline

Tests for SQLAlchemy query profiler functionality.
"""

import pytest
from sqlalchemy import Column, Integer, String, create_engine, select
from sqlalchemy.orm import DeclarativeBase, Session

from src.utils.query_profiler import (
    QueryProfiler,
    enable_profiling,
    disable_profiling,
    get_profiler,
    get_stats,
    reset_stats,
)


class Base(DeclarativeBase):
    """Test model base class."""

    pass


class TestModel(Base):
    """Test model for profiler testing."""

    __tablename__ = "test_table"
    id = Column(Integer, primary_key=True)
    name = Column(String(100))


@pytest.fixture
def test_engine():
    """Create in-memory SQLite engine for testing."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    return engine


@pytest.fixture
def profiler():
    """Create a fresh profiler instance."""
    return QueryProfiler(slow_query_threshold_ms=50, max_slow_queries=10)


@pytest.mark.unit
def test_profiler_initialization():
    """Test profiler initialization."""
    profiler = QueryProfiler(slow_query_threshold_ms=100, max_slow_queries=50)
    assert profiler.slow_query_threshold_ms == 100
    assert profiler.max_slow_queries == 50
    assert profiler.stats.total_queries == 0


@pytest.mark.unit
def test_profiler_enable_disable(test_engine, profiler):
    """Test enabling and disabling profiler."""
    # Enable profiling
    profiler.enable(test_engine)

    # Execute a query
    with Session(test_engine) as session:
        session.execute(select(TestModel))

    # Check that query was tracked
    assert profiler.stats.total_queries > 0

    # Disable profiling
    profiler.disable(test_engine)

    # Reset stats
    profiler.reset()

    # Execute another query
    with Session(test_engine) as session:
        session.execute(select(TestModel))

    # Query should not be tracked
    assert profiler.stats.total_queries == 0


@pytest.mark.unit
def test_query_stats_tracking(test_engine, profiler):
    """Test that query statistics are tracked correctly."""
    profiler.enable(test_engine)

    # Execute multiple queries
    with Session(test_engine) as session:
        for i in range(5):
            session.execute(select(TestModel))

    stats = profiler.get_stats()

    assert stats["total_queries"] >= 5
    assert stats["total_time_ms"] > 0
    assert stats["avg_time_ms"] > 0
    assert stats["min_time_ms"] >= 0
    assert stats["max_time_ms"] >= stats["min_time_ms"]

    profiler.disable(test_engine)


@pytest.mark.unit
def test_table_tracking(test_engine, profiler):
    """Test that queries are tracked by table."""
    profiler.enable(test_engine)

    # Execute queries
    with Session(test_engine) as session:
        session.execute(select(TestModel))
        session.execute(select(TestModel).where(TestModel.id == 1))

    stats = profiler.get_stats()

    # Check that test_table is tracked
    assert "test_table" in stats["queries_by_table"]
    assert stats["queries_by_table"]["test_table"] >= 2

    profiler.disable(test_engine)


@pytest.mark.unit
def test_slow_query_detection(test_engine, profiler):
    """Test slow query detection and logging."""
    # Use a very low threshold for testing
    profiler.slow_query_threshold_ms = 0  # All queries will be "slow"
    profiler.enable(test_engine)

    # Execute a query
    with Session(test_engine) as session:
        session.execute(select(TestModel))

    stats = profiler.get_stats()
    slow_queries = profiler.get_slow_queries()

    assert stats["slow_queries"] > 0
    assert len(slow_queries) > 0
    assert "statement" in slow_queries[0]
    assert "execution_time_ms" in slow_queries[0]

    profiler.disable(test_engine)


@pytest.mark.unit
def test_profiler_reset(test_engine, profiler):
    """Test profiler statistics reset."""
    profiler.enable(test_engine)

    # Execute queries
    with Session(test_engine) as session:
        session.execute(select(TestModel))

    assert profiler.stats.total_queries > 0

    # Reset stats
    profiler.reset()

    assert profiler.stats.total_queries == 0
    assert profiler.stats.total_time_ms == 0.0
    assert len(profiler.stats.slow_query_log) == 0

    profiler.disable(test_engine)


@pytest.mark.unit
def test_global_profiler_functions(test_engine):
    """Test global profiler utility functions."""
    # Enable profiling
    enable_profiling(test_engine, slow_query_threshold_ms=50)

    # Execute query
    with Session(test_engine) as session:
        session.execute(select(TestModel))

    # Get stats
    stats = get_stats()
    assert stats["total_queries"] > 0

    # Reset stats
    reset_stats()
    stats = get_stats()
    assert stats["total_queries"] == 0

    # Disable profiling
    disable_profiling(test_engine)


@pytest.mark.unit
def test_max_slow_queries_limit(test_engine):
    """Test that slow query log respects maximum size."""
    profiler = QueryProfiler(slow_query_threshold_ms=0, max_slow_queries=3)
    profiler.enable(test_engine)

    # Execute 5 queries (all will be "slow")
    with Session(test_engine) as session:
        for i in range(5):
            session.execute(select(TestModel))

    # Should only keep last 3
    slow_queries = profiler.get_slow_queries()
    assert len(slow_queries) <= 3

    profiler.disable(test_engine)


@pytest.mark.unit
def test_profiler_stats_aggregation(test_engine, profiler):
    """Test that profiler correctly aggregates statistics."""
    profiler.enable(test_engine)

    # Execute multiple queries
    with Session(test_engine) as session:
        for i in range(10):
            session.execute(select(TestModel))

    stats = profiler.get_stats()

    # Verify aggregation
    assert stats["total_queries"] >= 10
    # Use approximate equality due to floating point rounding
    expected_avg = stats["total_time_ms"] / stats["total_queries"]
    assert abs(stats["avg_time_ms"] - expected_avg) < 0.01
    assert stats["min_time_ms"] <= stats["avg_time_ms"] <= stats["max_time_ms"]

    profiler.disable(test_engine)
