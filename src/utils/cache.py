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
