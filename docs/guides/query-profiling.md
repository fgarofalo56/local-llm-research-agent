# Query Profiling Guide

This guide explains how to use the query profiler to monitor and optimize database performance in the local-llm-research-agent application.

## Overview

The query profiler is a SQLAlchemy-based tool that:

- Tracks all database queries in real-time
- Measures execution time for each query
- Detects and logs slow queries (default: >100ms)
- Provides aggregate statistics (total queries, avg/min/max times)
- Tracks which tables are queried most frequently
- Maintains a rolling log of recent slow queries

## Quick Start

### Enable Profiling

```python
from sqlalchemy import create_engine
from src.utils.query_profiler import enable_profiling

# Create your engine
engine = create_engine("your_connection_string")

# Enable profiling with 100ms slow query threshold
enable_profiling(engine, slow_query_threshold_ms=100)
```

### Get Statistics

```python
from src.utils.query_profiler import get_stats

# Get current profiling statistics
stats = get_stats()

print(f"Total queries: {stats['total_queries']}")
print(f"Average query time: {stats['avg_time_ms']:.2f}ms")
print(f"Slow queries: {stats['slow_queries']}")
```

### View Slow Queries

```python
from src.utils.query_profiler import get_slow_queries

# Get last 20 slow queries
slow_queries = get_slow_queries(limit=20)

for query in slow_queries:
    print(f"Time: {query['execution_time_ms']:.2f}ms")
    print(f"SQL: {query['statement']}")
```

## Integration with FastAPI

### In Application Startup

Add profiling to your FastAPI lifespan handler:

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI
from src.api.deps import get_engine
from src.utils.query_profiler import enable_profiling, disable_profiling


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    engine = get_engine()
    enable_profiling(engine, slow_query_threshold_ms=100)
    yield
    # Shutdown
    disable_profiling(engine)
    await engine.dispose()


app = FastAPI(lifespan=lifespan)
```

### Add Metrics Endpoint

Create an endpoint to expose profiling metrics:

```python
from fastapi import APIRouter
from src.utils.query_profiler import get_stats, get_slow_queries

router = APIRouter(prefix="/api/metrics", tags=["metrics"])


@router.get("/database/stats")
async def get_database_stats():
    """Get database query statistics."""
    return get_stats()


@router.get("/database/slow-queries")
async def get_database_slow_queries(limit: int = 20):
    """Get recent slow queries."""
    return {
        "slow_queries": get_slow_queries(limit=limit)
    }
```

## Configuration

### Slow Query Threshold

Adjust the threshold based on your performance requirements:

```python
# Development: Catch queries over 50ms
enable_profiling(engine, slow_query_threshold_ms=50)

# Production: Only log very slow queries
enable_profiling(engine, slow_query_threshold_ms=500)
```

### Maximum Slow Queries

Control how many slow queries are kept in memory:

```python
from src.utils.query_profiler import QueryProfiler

profiler = QueryProfiler(
    slow_query_threshold_ms=100,
    max_slow_queries=50  # Keep last 50 slow queries
)
profiler.enable(engine)
```

## Statistics Reference

### Available Metrics

The `get_stats()` function returns:

```python
{
    "total_queries": 1234,           # Total queries executed
    "total_time_ms": 45678.90,       # Total execution time
    "avg_time_ms": 37.05,            # Average query time
    "min_time_ms": 0.12,             # Fastest query
    "max_time_ms": 1234.56,          # Slowest query
    "slow_queries": 42,              # Number of slow queries
    "slow_query_threshold_ms": 100,  # Current threshold
    "queries_by_table": {            # Queries per table
        "conversations": 234,
        "messages": 567,
        "documents": 123
    },
    "top_tables": [                  # Top 10 tables by query count
        ("messages", 567),
        ("conversations", 234),
        ("documents", 123)
    ]
}
```

### Slow Query Log

Each slow query entry contains:

```python
{
    "statement": "SELECT * FROM messages...",
    "parameters": "{'id': 123}",
    "execution_time_ms": 123.45,
    "timestamp": 1702933200.123
}
```

## Performance Optimization Workflow

### 1. Identify Slow Queries

```python
slow_queries = get_slow_queries(limit=10)
for query in slow_queries:
    if query['execution_time_ms'] > 200:
        print(f"CRITICAL: {query['statement']}")
```

### 2. Check Table Usage

```python
stats = get_stats()
for table, count in stats['top_tables']:
    avg_time = stats['total_time_ms'] / stats['total_queries']
    print(f"{table}: {count} queries, avg {avg_time:.2f}ms")
```

### 3. Add Indexes

If you identify slow queries on specific columns, add indexes:

```python
# Create an Alembic migration
# alembic revision -m "add_index_to_messages"

def upgrade():
    op.create_index(
        'ix_messages_conversation_id',
        'messages',
        ['conversation_id']
    )
```

### 4. Monitor Impact

After adding indexes, reset statistics and monitor:

```python
from src.utils.query_profiler import reset_stats

# Reset statistics
reset_stats()

# Run your workload
# ...

# Check if performance improved
stats = get_stats()
print(f"Average query time: {stats['avg_time_ms']:.2f}ms")
```

## Best Practices

### Development

- Use a low threshold (50-100ms) to catch all potentially slow queries
- Monitor slow query log regularly
- Run profiler during integration tests

### Production

- Use a higher threshold (200-500ms) to avoid noise
- Enable profiling only on specific endpoints if needed
- Integrate with monitoring tools (Prometheus, Grafana)
- Consider async profiling to avoid overhead

### Testing

- Profile test runs to catch N+1 query problems
- Set up CI checks for query count regressions
- Use profiler to validate index effectiveness

## Example: Adding Database Metrics to Health Endpoint

```python
from fastapi import APIRouter
from src.utils.query_profiler import get_stats

router = APIRouter()


@router.get("/health")
async def health_check():
    """Health check with database metrics."""
    db_stats = get_stats()

    return {
        "status": "healthy",
        "database": {
            "total_queries": db_stats["total_queries"],
            "avg_query_time_ms": db_stats["avg_time_ms"],
            "slow_queries": db_stats["slow_queries"]
        }
    }
```

## Troubleshooting

### High Average Query Time

**Problem**: `avg_time_ms` is consistently high (>100ms)

**Solutions**:
1. Check `slow_queries` log for problematic queries
2. Add indexes to frequently filtered columns
3. Optimize complex joins
4. Consider query result caching

### Many Slow Queries

**Problem**: `slow_queries` count keeps increasing

**Solutions**:
1. Review `top_tables` to find hotspot tables
2. Check for missing foreign key indexes
3. Look for N+1 query patterns (use eager loading)
4. Consider database connection pooling

### No Queries Tracked

**Problem**: `total_queries` is 0

**Solutions**:
1. Ensure profiler is enabled: `enable_profiling(engine)`
2. Check that queries are using the profiled engine
3. Verify async vs sync engine usage matches

## Database Migration

The performance indexes migration adds indexes to commonly queried columns:

```bash
# Apply migration
uv run alembic upgrade head

# Check migration status
uv run alembic current

# Rollback if needed
uv run alembic downgrade -1
```

### Added Indexes

The migration adds indexes for:

- **conversations**: `created_at`, `is_archived`
- **messages**: `conversation_id`, `created_at`
- **documents**: `processing_status`, `created_at`
- **query_history**: `is_favorite`, `created_at`, `conversation_id`
- **dashboards**: `created_at`, `is_default`
- **dashboard_widgets**: `dashboard_id`, `widget_type`
- **data_alerts**: `is_active`, `last_checked_at`
- **mcp_server_configs**: `is_enabled`
- **scheduled_queries**: `is_active`, `next_run_at`
- **theme_configs**: `is_active`

## See Also

- [Database Schema](../reference/database-schema.md)
- [API Performance Guide](../guides/api-performance.md)
- [Alembic Migrations](../reference/migrations.md)
