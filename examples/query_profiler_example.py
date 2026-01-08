"""
Query Profiler Example
Phase 2.1: Backend Infrastructure & RAG Pipeline

Example of using the query profiler to monitor database performance.
"""

import asyncio

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.api.models.database import Base, Conversation, Message
from src.utils.query_profiler import enable_profiling, get_slow_queries, get_stats


async def main():
    """Example usage of query profiler."""

    # Create async engine (in-memory SQLite for demo)
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
    )

    # Enable query profiling with 50ms slow query threshold
    enable_profiling(engine, slow_query_threshold_ms=50)

    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Create session factory
    async_session_maker = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    print("=== Running Database Queries ===\n")

    # Execute some queries
    async with async_session_maker() as session:
        # Create test data
        conv1 = Conversation(title="Test Conversation 1")
        conv2 = Conversation(title="Test Conversation 2")
        session.add_all([conv1, conv2])
        await session.commit()

        # Query conversations
        result = await session.execute(select(Conversation))
        conversations = result.scalars().all()
        print(f"Found {len(conversations)} conversations")

        # Create messages
        for conv in conversations:
            for i in range(5):
                msg = Message(
                    conversation_id=conv.id,
                    role="user" if i % 2 == 0 else "assistant",
                    content=f"Message {i}",
                    tokens_used=10,
                )
                session.add(msg)

        await session.commit()

        # Query messages
        result = await session.execute(select(Message))
        messages = result.scalars().all()
        print(f"Found {len(messages)} messages")

    # Get profiling statistics
    print("\n=== Query Profiler Statistics ===\n")
    stats = get_stats()

    print(f"Total queries executed: {stats['total_queries']}")
    print(f"Total execution time: {stats['total_time_ms']:.2f}ms")
    print(f"Average query time: {stats['avg_time_ms']:.2f}ms")
    print(f"Min query time: {stats['min_time_ms']:.2f}ms")
    print(f"Max query time: {stats['max_time_ms']:.2f}ms")
    print(f"Slow queries detected: {stats['slow_queries']}")

    # Show queries by table
    if stats["queries_by_table"]:
        print("\n=== Queries by Table ===\n")
        for table, count in stats["top_tables"]:
            print(f"  {table}: {count} queries")

    # Show slow queries if any
    slow_queries = get_slow_queries(limit=5)
    if slow_queries:
        print("\n=== Slow Queries ===\n")
        for i, query in enumerate(slow_queries, 1):
            print(f"{i}. Execution time: {query['execution_time_ms']:.2f}ms")
            print(f"   Statement: {query['statement'][:100]}...")
            print()

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
