# Redis Caching for RAG Operations

## Quick Start

### Enable Redis Caching

Redis caching is automatically available when Redis is running. The system gracefully degrades if Redis is unavailable.

```python
from redis.asyncio import Redis
from src.rag.embedder import OllamaEmbedder
from src.utils.cache import RedisCacheBackend

# Initialize Redis client
redis_client = Redis.from_url("redis://localhost:6379", decode_responses=True)

# Create cache backend
cache = RedisCacheBackend(redis_client, prefix="rag")

# Initialize embedder
embedder = OllamaEmbedder()

# Use caching
embedding = await embedder.embed_with_cache("sample text", cache=cache)
```

### Start Redis

```bash
# Using Docker Compose
docker-compose -f docker/docker-compose.yml --env-file .env up -d redis-stack

# Verify Redis is running
docker ps | grep redis
```

## API Reference

### RedisCacheBackend

#### Initialization

```python
cache = RedisCacheBackend(
    redis_client,      # Redis async client
    prefix="rag"       # Cache key prefix (default: "rag")
)
```

#### Embedding Cache

```python
# Get cached embedding
embedding = await cache.get_embedding(text)
# Returns: list[float] | None

# Cache an embedding
await cache.set_embedding(
    text,              # Text that was embedded
    embedding,         # Embedding vector
    ttl=604800        # Time-to-live in seconds (default: 7 days)
)
```

#### Search Results Cache

```python
# Get cached search results
results = await cache.get_search_results(
    query="machine learning",
    top_k=5,
    source_type="document"  # Optional filter
)
# Returns: list[dict] | None

# Cache search results
await cache.set_search_results(
    query="machine learning",
    top_k=5,
    source_type="document",
    results=[...],
    ttl=3600          # Time-to-live in seconds (default: 1 hour)
)
```

#### Cache Management

```python
# Invalidate all entries for a document
count = await cache.invalidate_document(document_id)
# Returns: Number of keys deleted

# Get cache statistics
stats = await cache.get_stats()
# Returns: {"hits": int, "misses": int, "hit_rate": float}
```

### OllamaEmbedder

#### Caching Method

```python
embedder = OllamaEmbedder()

# With cache
embedding = await embedder.embed_with_cache(
    text="sample text",
    cache=cache  # Optional, uses direct embedding if None
)

# Without cache (existing method still works)
embedding = await embedder.embed(text)
```

## Common Patterns

### Pattern 1: Vector Store with Caching

```python
class MyVectorStore:
    def __init__(self, embedder, cache=None):
        self.embedder = embedder
        self.cache = cache

    async def add_document(self, document_id, chunks):
        for chunk in chunks:
            # Use cache if available
            if self.cache:
                embedding = await self.embedder.embed_with_cache(
                    chunk, cache=self.cache
                )
            else:
                embedding = await self.embedder.embed(chunk)

            # Store embedding...
```

### Pattern 2: Search with Result Caching

```python
async def search_documents(query, top_k=5, cache=None):
    # Check cache first
    if cache:
        cached = await cache.get_search_results(query, top_k, "document")
        if cached:
            return cached

    # Perform search
    results = await perform_vector_search(query, top_k)

    # Cache results
    if cache:
        await cache.set_search_results(query, top_k, "document", results)

    return results
```

### Pattern 3: Cache Invalidation on Update

```python
async def update_document(document_id, new_content, cache=None):
    # Invalidate old cache entries
    if cache:
        count = await cache.invalidate_document(document_id)
        logger.info("cache_invalidated", entries=count)

    # Update document
    await store_document(document_id, new_content)

    # Re-process and cache new embeddings
    chunks = chunk_text(new_content)
    for chunk in chunks:
        if cache:
            await embedder.embed_with_cache(chunk, cache=cache)
```

## Configuration

### TTL Recommendations

Choose TTL based on data volatility:

| Use Case | Recommended TTL | Reason |
|----------|----------------|--------|
| Static documents | 7 days (604800s) | Content rarely changes |
| User documents | 1 day (86400s) | May be updated occasionally |
| Search results | 1 hour (3600s) | New documents added regularly |
| Real-time data | 5 minutes (300s) | Frequently updated |

### Cache Key Prefix

Use different prefixes to separate cache namespaces:

```python
# Production cache
prod_cache = RedisCacheBackend(redis, prefix="prod_rag")

# Development cache
dev_cache = RedisCacheBackend(redis, prefix="dev_rag")

# Test cache
test_cache = RedisCacheBackend(redis, prefix="test_rag")
```

## Monitoring

### Check Cache Performance

```python
stats = await cache.get_stats()

print(f"Hit Rate: {stats['hit_rate']:.1%}")
print(f"Total Hits: {stats['hits']}")
print(f"Total Misses: {stats['misses']}")

# Good: > 70% hit rate
# Moderate: 40-70% hit rate
# Poor: < 40% hit rate (consider adjusting TTL or cache strategy)
```

### Using RedisInsight

1. Open RedisInsight at http://localhost:8008
2. Connect to localhost:6379
3. Search for keys with pattern: `rag:*`
4. View cache contents and TTLs
5. Monitor memory usage

### Cache Size Estimation

```python
# Embedding size: ~768 floats * 8 bytes = ~6KB per embedding
# Search results: ~1-10KB per query (depends on result count)

# Example: 1000 cached embeddings
# Memory: 1000 * 6KB = 6MB

# Example: 500 cached searches with 5 results each
# Memory: 500 * 5KB = 2.5MB
```

## Troubleshooting

### Cache Not Working

**Problem**: Cache always misses

**Solutions**:
1. Check Redis connection:
   ```python
   await redis_client.ping()  # Should not raise exception
   ```

2. Verify cache is passed to methods:
   ```python
   # Wrong: cache parameter not provided
   await embedder.embed_with_cache(text)

   # Correct: cache parameter provided
   await embedder.embed_with_cache(text, cache=cache)
   ```

3. Check cache keys are being created:
   ```bash
   redis-cli KEYS "rag:*"
   ```

### High Memory Usage

**Problem**: Redis consuming too much memory

**Solutions**:
1. Reduce TTL values to expire entries sooner
2. Use more specific cache prefixes and clear unused namespaces
3. Set Redis maxmemory policy:
   ```bash
   redis-cli CONFIG SET maxmemory 256mb
   redis-cli CONFIG SET maxmemory-policy allkeys-lru
   ```

### Stale Cache Data

**Problem**: Getting outdated results

**Solutions**:
1. Reduce TTL for volatile data
2. Invalidate cache on updates:
   ```python
   await cache.invalidate_document(document_id)
   ```
3. Clear all cache entries:
   ```bash
   redis-cli FLUSHDB
   ```

## Best Practices

### 1. Always Handle Missing Cache Gracefully

```python
# Good: Works with or without cache
if cache:
    embedding = await embedder.embed_with_cache(text, cache=cache)
else:
    embedding = await embedder.embed(text)

# Also good: embed_with_cache handles None cache
embedding = await embedder.embed_with_cache(text, cache=cache)
```

### 2. Invalidate Cache on Changes

```python
# When deleting a document
await delete_document(document_id)
if cache:
    await cache.invalidate_document(document_id)

# When updating a document
await update_document(document_id, new_content)
if cache:
    await cache.invalidate_document(document_id)
```

### 3. Monitor Cache Performance

```python
# Log cache stats periodically
stats = await cache.get_stats()
logger.info(
    "cache_performance",
    hit_rate=stats['hit_rate'],
    hits=stats['hits'],
    misses=stats['misses']
)
```

### 4. Use Appropriate TTL Values

```python
# Long-lived: Embeddings for static documents
await cache.set_embedding(text, embedding, ttl=604800)  # 7 days

# Medium-lived: Search results
await cache.set_search_results(query, top_k, source, results, ttl=3600)  # 1 hour

# Short-lived: Real-time or frequently changing data
await cache.set_search_results(query, top_k, source, results, ttl=300)  # 5 minutes
```

### 5. Clean Up on Shutdown

```python
# In application shutdown
async def shutdown():
    if cache:
        await cache.redis.close()
```

## Examples

See `examples/redis_cache_example.py` for complete working examples:

```bash
# Run examples
uv run python examples/redis_cache_example.py
```

Examples include:
- Embedding cache with statistics
- Search results caching
- Document invalidation
- Custom TTL configuration

## See Also

- [Redis Stack Documentation](https://redis.io/docs/stack/)
- [redis-py Documentation](https://redis.readthedocs.io/)
- [RAG Pipeline Guide](./rag-pipeline.md)
- [Performance Tuning](./performance-tuning.md)
