"""
Tests for Response Cache

Tests the TTL-based LRU cache functionality for LLM responses.
"""

import time

import pytest

from src.utils.cache import CacheStats, ResponseCache, get_response_cache, reset_response_cache


class TestResponseCache:
    """Tests for the ResponseCache class."""

    def test_basic_set_get(self):
        """Test basic set and get operations."""
        cache: ResponseCache[str] = ResponseCache(max_size=10, ttl_seconds=3600)

        cache.set("query1", "response1")
        assert cache.get("query1") == "response1"

    def test_cache_miss(self):
        """Test cache miss returns None."""
        cache: ResponseCache[str] = ResponseCache(max_size=10, ttl_seconds=3600)

        assert cache.get("nonexistent") is None

    def test_cache_disabled(self):
        """Test that disabled cache doesn't store values."""
        cache: ResponseCache[str] = ResponseCache(max_size=10, ttl_seconds=3600, enabled=False)

        cache.set("query1", "response1")
        assert cache.get("query1") is None
        assert len(cache) == 0

    def test_enable_disable(self):
        """Test enabling and disabling cache at runtime."""
        cache: ResponseCache[str] = ResponseCache(max_size=10, ttl_seconds=3600, enabled=True)

        cache.set("query1", "response1")
        assert cache.get("query1") == "response1"

        cache.enabled = False
        cache.set("query2", "response2")
        assert cache.get("query2") is None

        cache.enabled = True
        cache.set("query3", "response3")
        assert cache.get("query3") == "response3"

    def test_ttl_expiration(self):
        """Test that entries expire after TTL."""
        cache: ResponseCache[str] = ResponseCache(max_size=10, ttl_seconds=1)

        cache.set("query1", "response1")
        assert cache.get("query1") == "response1"

        # Wait for TTL to expire
        time.sleep(1.5)

        assert cache.get("query1") is None

    def test_no_ttl_expiration(self):
        """Test that TTL of 0 means no expiration."""
        cache: ResponseCache[str] = ResponseCache(max_size=10, ttl_seconds=0)

        cache.set("query1", "response1")
        assert cache.get("query1") == "response1"
        # Entry should still be valid with TTL=0

    def test_max_size_eviction(self):
        """Test LRU eviction when max size is reached."""
        cache: ResponseCache[str] = ResponseCache(max_size=3, ttl_seconds=3600)

        cache.set("query1", "response1")
        cache.set("query2", "response2")
        cache.set("query3", "response3")

        # All should be present
        assert cache.get("query1") == "response1"
        assert cache.get("query2") == "response2"
        assert cache.get("query3") == "response3"

        # Add fourth entry - should evict query1 (oldest)
        cache.set("query4", "response4")

        assert cache.get("query1") is None  # Evicted
        assert cache.get("query2") == "response2"
        assert cache.get("query3") == "response3"
        assert cache.get("query4") == "response4"

    def test_lru_access_order(self):
        """Test that accessing an entry moves it to end (most recently used)."""
        cache: ResponseCache[str] = ResponseCache(max_size=3, ttl_seconds=3600)

        cache.set("query1", "response1")
        cache.set("query2", "response2")
        cache.set("query3", "response3")

        # Access query1 to make it most recently used
        _ = cache.get("query1")

        # Add new entry - should evict query2 (now the oldest)
        cache.set("query4", "response4")

        assert cache.get("query1") == "response1"  # Still present
        assert cache.get("query2") is None  # Evicted
        assert cache.get("query3") == "response3"
        assert cache.get("query4") == "response4"

    def test_invalidate(self):
        """Test invalidating a specific entry."""
        cache: ResponseCache[str] = ResponseCache(max_size=10, ttl_seconds=3600)

        cache.set("query1", "response1")
        cache.set("query2", "response2")

        assert cache.invalidate("query1") is True
        assert cache.get("query1") is None
        assert cache.get("query2") == "response2"

        # Invalidating non-existent entry returns False
        assert cache.invalidate("nonexistent") is False

    def test_clear(self):
        """Test clearing all entries."""
        cache: ResponseCache[str] = ResponseCache(max_size=10, ttl_seconds=3600)

        cache.set("query1", "response1")
        cache.set("query2", "response2")

        count = cache.clear()
        assert count == 2
        assert len(cache) == 0
        assert cache.get("query1") is None
        assert cache.get("query2") is None

    def test_cleanup_expired(self):
        """Test cleanup of expired entries."""
        cache: ResponseCache[str] = ResponseCache(max_size=10, ttl_seconds=1)

        cache.set("query1", "response1")
        cache.set("query2", "response2")

        # Wait for expiration
        time.sleep(1.5)

        count = cache.cleanup_expired()
        assert count == 2
        assert len(cache) == 0

    def test_contains(self):
        """Test the __contains__ operator."""
        cache: ResponseCache[str] = ResponseCache(max_size=10, ttl_seconds=3600)

        cache.set("query1", "response1")
        assert "query1" in cache
        assert "query2" not in cache


class TestCacheStats:
    """Tests for the CacheStats class."""

    def test_stats_tracking(self):
        """Test that stats are tracked correctly."""
        cache: ResponseCache[str] = ResponseCache(max_size=10, ttl_seconds=3600)

        # Initial stats
        stats = cache.get_stats()
        assert stats.hits == 0
        assert stats.misses == 0
        assert stats.size == 0

        # Cache miss
        cache.get("nonexistent")
        stats = cache.get_stats()
        assert stats.misses == 1

        # Set and hit
        cache.set("query1", "response1")
        cache.get("query1")
        stats = cache.get_stats()
        assert stats.hits == 1
        assert stats.size == 1

    def test_hit_rate(self):
        """Test hit rate calculation."""
        stats = CacheStats(hits=3, misses=1)
        assert stats.hit_rate == 75.0

        # Zero total
        stats = CacheStats(hits=0, misses=0)
        assert stats.hit_rate == 0.0

    def test_eviction_stats(self):
        """Test eviction counting."""
        cache: ResponseCache[str] = ResponseCache(max_size=2, ttl_seconds=3600)

        cache.set("query1", "response1")
        cache.set("query2", "response2")
        cache.set("query3", "response3")  # Evicts query1

        stats = cache.get_stats()
        assert stats.evictions == 1

    def test_reset_stats(self):
        """Test resetting stats."""
        cache: ResponseCache[str] = ResponseCache(max_size=10, ttl_seconds=3600)

        cache.get("miss")
        cache.set("hit", "value")
        cache.get("hit")

        stats = cache.get_stats()
        assert stats.hits > 0 or stats.misses > 0

        cache.reset_stats()
        stats = cache.get_stats()
        assert stats.hits == 0
        assert stats.misses == 0
        assert stats.evictions == 0
        # Size should not be reset
        assert stats.size == 1

    def test_stats_to_dict(self):
        """Test stats serialization to dict."""
        stats = CacheStats(
            hits=10,
            misses=5,
            evictions=2,
            size=100,
            max_size=200,
            ttl_seconds=3600,
        )
        result = stats.to_dict()

        assert result["hits"] == 10
        assert result["misses"] == 5
        assert result["evictions"] == 2
        assert result["size"] == 100
        assert result["max_size"] == 200
        assert result["ttl_seconds"] == 3600
        assert "hit_rate" in result


class TestSingletonCache:
    """Tests for the singleton cache functions."""

    def setup_method(self):
        """Reset singleton before each test."""
        reset_response_cache()

    def test_get_response_cache_singleton(self):
        """Test that get_response_cache returns singleton."""
        cache1 = get_response_cache(max_size=100)
        cache2 = get_response_cache(max_size=200)  # Different params ignored

        assert cache1 is cache2

    def test_reset_response_cache(self):
        """Test that reset creates new instance."""
        cache1 = get_response_cache()
        reset_response_cache()
        cache2 = get_response_cache()

        assert cache1 is not cache2
