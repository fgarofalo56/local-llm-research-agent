"""
Redis Cache Example for RAG Operations

Demonstrates how to use RedisCacheBackend for caching embeddings
and search results to improve performance.
"""

import asyncio

from redis.asyncio import Redis

from src.rag.embedder import OllamaEmbedder
from src.utils.cache import RedisCacheBackend
from src.utils.config import get_settings


async def example_embedding_cache():
    """Example: Caching embeddings to reduce duplicate API calls."""
    print("=== Embedding Cache Example ===\n")

    settings = get_settings()

    # Initialize Redis client
    redis_client = Redis.from_url(settings.redis_url, decode_responses=True)

    try:
        await redis_client.ping()
        print("✓ Connected to Redis")

        # Initialize cache backend
        cache = RedisCacheBackend(redis_client, prefix="example_rag")

        # Initialize embedder
        embedder = OllamaEmbedder(
            base_url=settings.ollama_host,
            model=settings.embedding_model,
        )

        # First call - will generate embedding and cache it
        text = "SQL Server is a relational database management system."
        print(f"\n1. Generating embedding for: '{text[:50]}...'")

        embedding1 = await embedder.embed_with_cache(text, cache=cache)
        print(f"   Generated embedding with {len(embedding1)} dimensions")

        # Second call - will retrieve from cache
        print(f"\n2. Requesting same text again (should hit cache)...")
        embedding2 = await embedder.embed_with_cache(text, cache=cache)
        print(f"   Retrieved embedding from cache")

        # Verify they're the same
        assert embedding1 == embedding2
        print("   ✓ Embeddings match!")

        # Get cache stats
        stats = await cache.get_stats()
        print(f"\n3. Cache Statistics:")
        print(f"   - Hits: {stats['hits']}")
        print(f"   - Misses: {stats['misses']}")
        print(f"   - Hit Rate: {stats['hit_rate']:.1%}")

    finally:
        await redis_client.close()
        print("\n✓ Redis connection closed")


async def example_search_cache():
    """Example: Caching search results."""
    print("\n\n=== Search Results Cache Example ===\n")

    settings = get_settings()

    # Initialize Redis client
    redis_client = Redis.from_url(settings.redis_url, decode_responses=True)

    try:
        await redis_client.ping()
        print("✓ Connected to Redis")

        # Initialize cache backend
        cache = RedisCacheBackend(redis_client, prefix="example_search")

        # Simulate search results
        query = "machine learning algorithms"
        top_k = 5
        source_type = "document"

        # First search - cache miss
        print(f"\n1. Searching for: '{query}'")
        cached_results = await cache.get_search_results(query, top_k, source_type)

        if cached_results is None:
            print("   Cache miss - performing search...")

            # Simulate search results
            search_results = [
                {
                    "text": "Introduction to supervised learning algorithms",
                    "score": 0.92,
                    "source": "ml_guide.pdf",
                },
                {
                    "text": "Deep learning neural network architectures",
                    "score": 0.87,
                    "source": "deep_learning.pdf",
                },
                {
                    "text": "Unsupervised clustering techniques",
                    "score": 0.81,
                    "source": "clustering.pdf",
                },
            ]

            # Cache the results (TTL: 1 hour by default)
            await cache.set_search_results(query, top_k, source_type, search_results)
            print(f"   ✓ Cached {len(search_results)} search results")

        # Second search - cache hit
        print(f"\n2. Searching for same query again...")
        cached_results = await cache.get_search_results(query, top_k, source_type)

        if cached_results:
            print(f"   Cache hit! Retrieved {len(cached_results)} results")
            print("\n   Top result:")
            print(f"   - Text: {cached_results[0]['text']}")
            print(f"   - Score: {cached_results[0]['score']}")
            print(f"   - Source: {cached_results[0]['source']}")

    finally:
        await redis_client.close()
        print("\n✓ Redis connection closed")


async def example_document_invalidation():
    """Example: Invalidating cache entries when a document changes."""
    print("\n\n=== Document Invalidation Example ===\n")

    settings = get_settings()

    # Initialize Redis client
    redis_client = Redis.from_url(settings.redis_url, decode_responses=True)

    try:
        await redis_client.ping()
        print("✓ Connected to Redis")

        # Initialize cache backend
        cache = RedisCacheBackend(redis_client, prefix="example_invalidation")

        # Simulate caching embeddings for a document
        doc_id = "doc_12345"
        print(f"\n1. Caching embeddings for document: {doc_id}")

        # Cache some embeddings (simulated)
        await cache.set_embedding(f"{doc_id}_chunk1", [0.1, 0.2, 0.3])
        await cache.set_embedding(f"{doc_id}_chunk2", [0.4, 0.5, 0.6])
        print("   ✓ Cached embeddings for 2 chunks")

        # Cache search results that include this document
        await cache.set_search_results(
            query=f"related to {doc_id}",
            top_k=5,
            source_type="document",
            results=[{"text": "result 1", "score": 0.9}],
        )
        print("   ✓ Cached search results")

        # Invalidate all cache entries for this document
        print(f"\n2. Document {doc_id} has been updated, invalidating cache...")
        count = await cache.invalidate_document(doc_id)
        print(f"   ✓ Invalidated {count} cache entries")

        # Verify embeddings are gone
        print("\n3. Verifying cache invalidation...")
        chunk1_embedding = await cache.get_embedding(f"{doc_id}_chunk1")
        if chunk1_embedding is None:
            print("   ✓ Chunk 1 embedding successfully invalidated")

        chunk2_embedding = await cache.get_embedding(f"{doc_id}_chunk2")
        if chunk2_embedding is None:
            print("   ✓ Chunk 2 embedding successfully invalidated")

    finally:
        await redis_client.close()
        print("\n✓ Redis connection closed")


async def example_cache_configuration():
    """Example: Configuring cache TTL values."""
    print("\n\n=== Cache Configuration Example ===\n")

    settings = get_settings()

    # Initialize Redis client
    redis_client = Redis.from_url(settings.redis_url, decode_responses=True)

    try:
        await redis_client.ping()
        print("✓ Connected to Redis")

        # Initialize cache backend
        cache = RedisCacheBackend(redis_client, prefix="example_config")

        # Cache with custom TTL values
        print("\n1. Caching with custom TTL values:")

        # Long-lived embedding cache (7 days = 604800 seconds)
        await cache.set_embedding(
            "permanent content", [0.1, 0.2, 0.3], ttl=604800
        )
        print("   ✓ Cached embedding with 7-day TTL")

        # Short-lived search results (5 minutes = 300 seconds)
        await cache.set_search_results(
            query="latest news",
            top_k=5,
            source_type="news",
            results=[{"text": "news 1", "score": 0.9}],
            ttl=300,
        )
        print("   ✓ Cached search results with 5-minute TTL")

        print("\n2. TTL Recommendations:")
        print("   - Embeddings: 7 days (604800 sec) - rarely change")
        print("   - Search results: 1 hour (3600 sec) - moderate change")
        print("   - Real-time data: 5 minutes (300 sec) - frequent updates")

    finally:
        await redis_client.close()
        print("\n✓ Redis connection closed")


async def main():
    """Run all examples."""
    print("Redis Cache Examples for RAG Operations")
    print("=" * 50)

    try:
        await example_embedding_cache()
        await example_search_cache()
        await example_document_invalidation()
        await example_cache_configuration()

        print("\n\n" + "=" * 50)
        print("All examples completed successfully!")
        print("\nKey Takeaways:")
        print("1. Use embed_with_cache() to cache embeddings automatically")
        print("2. Cache search results to reduce expensive vector searches")
        print("3. Invalidate cache when documents are updated or deleted")
        print("4. Configure TTL based on data volatility")
        print("=" * 50)

    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nMake sure:")
        print("1. Redis is running (docker-compose up redis-stack)")
        print("2. Ollama is running with nomic-embed-text model")
        print("3. .env file is configured correctly")


if __name__ == "__main__":
    asyncio.run(main())
