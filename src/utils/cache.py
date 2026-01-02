"""
Response Caching

A TTL-based caching layer for LLM responses to improve performance
on repeated queries. Uses an LRU eviction policy with configurable
max size and time-to-live settings.
"""

import hashlib
import time
from collections import OrderedDict
from dataclasses import dataclass
from typing import Generic, TypeVar

from src.utils.logger import get_logger

logger = get_logger(__name__)

T = TypeVar("T")


@dataclass
class CacheEntry(Generic[T]):
    """A single cache entry with value and metadata."""

    value: T
    created_at: float
    hits: int = 0


@dataclass
class CacheStats:
    """Statistics about cache usage."""

    hits: int = 0
    misses: int = 0
    evictions: int = 0
    size: int = 0
    max_size: int = 0
    ttl_seconds: int = 0

    @property
    def hit_rate(self) -> float:
        """Calculate cache hit rate as a percentage."""
        total = self.hits + self.misses
        return (self.hits / total * 100) if total > 0 else 0.0

    def to_dict(self) -> dict:
        """Convert stats to dictionary."""
        return {
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": f"{self.hit_rate:.1f}%",
            "evictions": self.evictions,
            "size": self.size,
            "max_size": self.max_size,
            "ttl_seconds": self.ttl_seconds,
        }


class ResponseCache(Generic[T]):
    """
    TTL-based LRU cache for LLM responses.

    Features:
    - Configurable max size (number of entries)
    - Configurable TTL (time-to-live) for entries
    - LRU eviction when max size is reached
    - Thread-safe for single-threaded async operations
    - Stats tracking for monitoring

    Usage:
        cache = ResponseCache[str](max_size=100, ttl_seconds=3600)

        # Check cache first
        cached = cache.get(query)
        if cached:
            return cached

        # Generate response and cache it
        response = await generate_response(query)
        cache.set(query, response)
    """

    def __init__(
        self,
        max_size: int = 100,
        ttl_seconds: int = 3600,
        enabled: bool = True,
    ):
        """
        Initialize the cache.

        Args:
            max_size: Maximum number of entries to store
            ttl_seconds: Time-to-live for entries in seconds
            enabled: Whether caching is enabled
        """
        self._cache: OrderedDict[str, CacheEntry[T]] = OrderedDict()
        self._max_size = max(1, max_size)
        self._ttl_seconds = max(0, ttl_seconds)
        self._enabled = enabled

        # Stats
        self._hits = 0
        self._misses = 0
        self._evictions = 0

        logger.info(
            "cache_initialized",
            max_size=self._max_size,
            ttl_seconds=self._ttl_seconds,
            enabled=self._enabled,
        )

    @property
    def enabled(self) -> bool:
        """Check if caching is enabled."""
        return self._enabled

    @enabled.setter
    def enabled(self, value: bool) -> None:
        """Enable or disable caching."""
        self._enabled = value
        logger.info("cache_enabled_changed", enabled=value)

    def _generate_key(self, query: str) -> str:
        """Generate a cache key from the query string."""
        # Use SHA256 for consistent, fixed-length keys
        return hashlib.sha256(query.encode()).hexdigest()

    def _is_expired(self, entry: CacheEntry[T]) -> bool:
        """Check if a cache entry has expired."""
        if self._ttl_seconds == 0:
            return False  # TTL of 0 means no expiration
        return (time.time() - entry.created_at) > self._ttl_seconds

    def get(self, query: str) -> T | None:
        """
        Get a cached response for the query.

        Args:
            query: The user's query string

        Returns:
            Cached response or None if not found/expired
        """
        if not self._enabled:
            return None

        key = self._generate_key(query)
        entry = self._cache.get(key)

        if entry is None:
            self._misses += 1
            return None

        # Check for expiration
        if self._is_expired(entry):
            self._cache.pop(key)
            self._misses += 1
            logger.debug("cache_expired", key=key[:16])
            return None

        # Cache hit - update stats and move to end (most recently used)
        self._hits += 1
        entry.hits += 1
        self._cache.move_to_end(key)

        logger.debug("cache_hit", key=key[:16], entry_hits=entry.hits)
        return entry.value

    def set(self, query: str, value: T) -> None:
        """
        Store a response in the cache.

        Args:
            query: The user's query string
            value: The response to cache
        """
        if not self._enabled:
            return

        key = self._generate_key(query)

        # If key exists, update it
        if key in self._cache:
            self._cache[key] = CacheEntry(value=value, created_at=time.time())
            self._cache.move_to_end(key)
            return

        # Evict oldest entry if at max size
        while len(self._cache) >= self._max_size:
            evicted_key = next(iter(self._cache))
            self._cache.pop(evicted_key)
            self._evictions += 1
            logger.debug("cache_eviction", evicted_key=evicted_key[:16])

        # Add new entry
        self._cache[key] = CacheEntry(value=value, created_at=time.time())
        logger.debug("cache_set", key=key[:16], size=len(self._cache))

    def invalidate(self, query: str) -> bool:
        """
        Remove a specific entry from the cache.

        Args:
            query: The query to invalidate

        Returns:
            True if entry was found and removed
        """
        key = self._generate_key(query)
        if key in self._cache:
            self._cache.pop(key)
            logger.debug("cache_invalidated", key=key[:16])
            return True
        return False

    def clear(self) -> int:
        """
        Clear all entries from the cache.

        Returns:
            Number of entries cleared
        """
        count = len(self._cache)
        self._cache.clear()
        logger.info("cache_cleared", entries_cleared=count)
        return count

    def cleanup_expired(self) -> int:
        """
        Remove all expired entries from the cache.

        Returns:
            Number of entries removed
        """
        if self._ttl_seconds == 0:
            return 0  # No expiration configured

        current_time = time.time()
        expired_keys = [
            key
            for key, entry in self._cache.items()
            if (current_time - entry.created_at) > self._ttl_seconds
        ]

        for key in expired_keys:
            self._cache.pop(key)

        if expired_keys:
            logger.info("cache_cleanup", entries_removed=len(expired_keys))

        return len(expired_keys)

    def get_stats(self) -> CacheStats:
        """Get current cache statistics."""
        return CacheStats(
            hits=self._hits,
            misses=self._misses,
            evictions=self._evictions,
            size=len(self._cache),
            max_size=self._max_size,
            ttl_seconds=self._ttl_seconds,
        )

    def reset_stats(self) -> None:
        """Reset hit/miss/eviction counters."""
        self._hits = 0
        self._misses = 0
        self._evictions = 0
        logger.info("cache_stats_reset")

    def __len__(self) -> int:
        """Return number of entries in the cache."""
        return len(self._cache)

    def __contains__(self, query: str) -> bool:
        """Check if a query is in the cache (without updating stats)."""
        key = self._generate_key(query)
        entry = self._cache.get(key)
        if entry is None:
            return False
        return not self._is_expired(entry)


# Singleton cache instance for agent responses
_response_cache: ResponseCache[str] | None = None


def get_response_cache(
    max_size: int = 100,
    ttl_seconds: int = 3600,
    enabled: bool = True,
) -> ResponseCache[str]:
    """
    Get or create the singleton response cache.

    Args:
        max_size: Maximum number of entries
        ttl_seconds: Time-to-live in seconds
        enabled: Whether caching is enabled

    Returns:
        The response cache instance
    """
    global _response_cache
    if _response_cache is None:
        _response_cache = ResponseCache[str](
            max_size=max_size,
            ttl_seconds=ttl_seconds,
            enabled=enabled,
        )
    return _response_cache


def reset_response_cache() -> None:
    """Reset the singleton response cache."""
    global _response_cache
    _response_cache = None


# ==========================================
# Redis Cache Backend for RAG Operations
# ==========================================


class RedisCacheBackend:
    """Redis-backed cache for RAG operations."""

    def __init__(self, redis_client, prefix: str = "rag"):
        """
        Initialize Redis cache backend.

        Args:
            redis_client: Redis async client (redis.asyncio.Redis)
            prefix: Prefix for all cache keys (default: "rag")
        """
        self.redis = redis_client
        self.prefix = prefix

    def _make_key(self, namespace: str, key: str) -> str:
        """Create prefixed cache key."""
        return f"{self.prefix}:{namespace}:{key}"

    def _hash_content(self, content: str) -> str:
        """Create hash of content for cache key."""
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    async def get_embedding(self, text: str) -> list[float] | None:
        """
        Get cached embedding for text.

        Args:
            text: Text to look up embedding for

        Returns:
            Cached embedding vector or None if not found
        """
        import json

        key = self._make_key("embedding", self._hash_content(text))
        data = await self.redis.get(key)
        if data:
            logger.debug("embedding_cache_hit", key=key[:30])
            return json.loads(data)
        return None

    async def set_embedding(
        self, text: str, embedding: list[float], ttl: int = 604800  # 7 days
    ) -> None:
        """
        Cache embedding for text.

        Args:
            text: Text that was embedded
            embedding: Embedding vector
            ttl: Time-to-live in seconds (default: 7 days)
        """
        import json

        key = self._make_key("embedding", self._hash_content(text))
        await self.redis.setex(key, ttl, json.dumps(embedding))
        logger.debug("embedding_cached", key=key[:30])

    async def get_search_results(
        self, query: str, top_k: int, source_type: str | None
    ) -> list[dict] | None:
        """
        Get cached search results.

        Args:
            query: Search query
            top_k: Number of results
            source_type: Optional source type filter

        Returns:
            Cached search results or None if not found
        """
        import json

        cache_key = f"{query}:{top_k}:{source_type or 'all'}"
        key = self._make_key("search", self._hash_content(cache_key))
        data = await self.redis.get(key)
        if data:
            logger.debug("search_cache_hit", query=query[:30])
            return json.loads(data)
        return None

    async def set_search_results(
        self,
        query: str,
        top_k: int,
        source_type: str | None,
        results: list[dict],
        ttl: int = 3600,  # 1 hour
    ) -> None:
        """
        Cache search results.

        Args:
            query: Search query
            top_k: Number of results
            source_type: Optional source type filter
            results: Search results to cache
            ttl: Time-to-live in seconds (default: 1 hour)
        """
        import json

        cache_key = f"{query}:{top_k}:{source_type or 'all'}"
        key = self._make_key("search", self._hash_content(cache_key))
        await self.redis.setex(key, ttl, json.dumps(results))
        logger.debug("search_cached", query=query[:30])

    async def invalidate_document(self, document_id: str) -> int:
        """
        Invalidate all cache entries for a document.

        Args:
            document_id: Document ID to invalidate

        Returns:
            Number of keys deleted
        """
        pattern = f"{self.prefix}:*:{document_id}*"
        keys = await self.redis.keys(pattern)
        if keys:
            return await self.redis.delete(*keys)
        return 0

    async def get_stats(self) -> dict[str, float | int]:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache stats (hits, misses, hit_rate)
        """
        info = await self.redis.info("stats")
        hits = info.get("keyspace_hits", 0)
        misses = info.get("keyspace_misses", 0)
        total = hits + misses
        hit_rate = hits / total if total > 0 else 0.0

        return {
            "hits": hits,
            "misses": misses,
            "hit_rate": hit_rate,
        }
