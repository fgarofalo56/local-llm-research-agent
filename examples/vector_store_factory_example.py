"""
Vector Store Factory Example

Demonstrates the use of the VectorStoreFactory for creating vector stores
with different backends (MSSQL or Redis).

Usage:
    uv run python examples/vector_store_factory_example.py
"""

import asyncio

from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from src.rag import OllamaEmbedder, VectorStoreFactory
from src.utils.config import get_settings


async def example_create_mssql_store():
    """Example: Create MSSQL vector store using factory."""
    print("\n=== Creating MSSQL Vector Store ===")

    settings = get_settings()

    # Initialize embedder
    embedder = OllamaEmbedder(
        base_url=settings.ollama_host,
        model=settings.embedding_model,
    )

    # Create backend database engine
    backend_engine = create_async_engine(
        settings.backend_database_url_async,
        echo=False,
        pool_pre_ping=True,
    )
    session_factory = async_sessionmaker(backend_engine, expire_on_commit=False)

    try:
        # Create MSSQL vector store using factory
        vector_store = await VectorStoreFactory.create(
            store_type="mssql",
            embedder=embedder,
            dimensions=settings.vector_dimensions,
            session_factory=session_factory,
        )

        print(f"✓ Vector store created: {vector_store}")

        # Get stats
        stats = await vector_store.get_stats()
        print(f"✓ Stats: {stats}")

        return vector_store

    finally:
        await backend_engine.dispose()


async def example_create_redis_store():
    """Example: Create Redis vector store using factory."""
    print("\n=== Creating Redis Vector Store ===")

    settings = get_settings()

    # Initialize embedder
    embedder = OllamaEmbedder(
        base_url=settings.ollama_host,
        model=settings.embedding_model,
    )

    # Create Redis client
    redis_client = Redis.from_url(settings.redis_url, decode_responses=True)

    try:
        # Verify Redis connection
        await redis_client.ping()
        print("✓ Redis connection verified")

        # Create Redis vector store using factory
        vector_store = await VectorStoreFactory.create(
            store_type="redis",
            embedder=embedder,
            dimensions=settings.vector_dimensions,
            redis_client=redis_client,
        )

        print(f"✓ Vector store created: {vector_store}")

        # Get stats
        stats = await vector_store.get_stats()
        print(f"✓ Stats: {stats}")

        return vector_store

    finally:
        await redis_client.close()


async def example_create_with_fallback():
    """Example: Create vector store with automatic fallback."""
    print("\n=== Creating Vector Store with Fallback ===")

    settings = get_settings()

    # Initialize embedder
    embedder = OllamaEmbedder(
        base_url=settings.ollama_host,
        model=settings.embedding_model,
    )

    # Prepare both backends
    backend_engine = create_async_engine(
        settings.backend_database_url_async,
        echo=False,
        pool_pre_ping=True,
    )
    session_factory = async_sessionmaker(backend_engine, expire_on_commit=False)

    redis_client = Redis.from_url(settings.redis_url, decode_responses=True)

    try:
        # Try MSSQL first, fall back to Redis if it fails
        print("Attempting to create MSSQL store (primary)...")
        vector_store = await VectorStoreFactory.create_with_fallback(
            primary_type="mssql",
            fallback_type="redis",
            embedder=embedder,
            dimensions=settings.vector_dimensions,
            session_factory=session_factory,
            redis_client=redis_client,
        )

        print(f"✓ Vector store created: {vector_store}")
        stats = await vector_store.get_stats()
        print(f"✓ Store type: {stats.get('store_type', 'unknown')}")

        return vector_store

    finally:
        await backend_engine.dispose()
        await redis_client.close()


async def example_polymorphism():
    """Example: Use vector stores polymorphically through base class."""
    print("\n=== Polymorphic Vector Store Usage ===")

    from src.rag.vector_store_base import VectorStoreBase

    settings = get_settings()
    embedder = OllamaEmbedder(
        base_url=settings.ollama_host,
        model=settings.embedding_model,
    )

    # Create backend engine
    backend_engine = create_async_engine(
        settings.backend_database_url_async,
        echo=False,
        pool_pre_ping=True,
    )
    session_factory = async_sessionmaker(backend_engine, expire_on_commit=False)

    try:
        # Create store (type is VectorStoreBase)
        store: VectorStoreBase = await VectorStoreFactory.create(
            store_type="mssql",
            embedder=embedder,
            dimensions=settings.vector_dimensions,
            session_factory=session_factory,
        )

        # Use common interface
        print(f"Store representation: {repr(store)}")
        print(f"Dimensions: {store.dimensions}")

        # All methods work through base class interface
        stats = await store.get_stats()
        print(f"✓ Stats retrieved: {stats}")

        # Example: Add a test document
        await store.add_document(
            document_id="example_001",
            chunks=["This is a test document", "With multiple chunks"],
            source="example.txt",
            metadata={"example": True},
        )
        print("✓ Document added successfully")

        # Search
        results = await store.search(query="test document", top_k=2)
        print(f"✓ Search completed: {len(results)} results")

        # Delete
        deleted = await store.delete_document("example_001")
        print(f"✓ Document deleted: {deleted} chunks removed")

    finally:
        await backend_engine.dispose()


async def main():
    """Run all examples."""
    print("Vector Store Factory Examples")
    print("=" * 60)

    settings = get_settings()

    # Example 1: Create MSSQL store
    try:
        await example_create_mssql_store()
    except Exception as e:
        print(f"✗ MSSQL example failed: {e}")

    # Example 2: Create Redis store
    try:
        await example_create_redis_store()
    except Exception as e:
        print(f"✗ Redis example failed: {e}")

    # Example 3: Create with fallback
    try:
        await example_create_with_fallback()
    except Exception as e:
        print(f"✗ Fallback example failed: {e}")

    # Example 4: Polymorphic usage
    try:
        await example_polymorphism()
    except Exception as e:
        print(f"✗ Polymorphism example failed: {e}")

    print("\n" + "=" * 60)
    print("Examples completed!")


if __name__ == "__main__":
    asyncio.run(main())
