"""
Cache management for research agent.

Provides caching functionality to avoid redundant LLM calls for identical queries.
"""

from src.utils.cache import CacheStats, ResponseCache


class AgentCache:
    """
    Manages response caching for the research agent.

    Provides methods to enable/disable caching, get statistics,
    clear cache, and invalidate specific entries.
    """

    def __init__(self, cache: ResponseCache[str]):
        """
        Initialize agent cache manager.

        Args:
            cache: ResponseCache instance to manage
        """
        self._cache = cache
        self._enabled = cache.enabled

    @property
    def cache_enabled(self) -> bool:
        """Check if caching is enabled."""
        return self._cache.enabled

    @cache_enabled.setter
    def cache_enabled(self, value: bool) -> None:
        """Enable or disable caching."""
        self._cache.enabled = value
        self._enabled = value

    def get_cache_stats(self) -> CacheStats:
        """Get current cache statistics."""
        return self._cache.get_stats()

    def clear_cache(self) -> int:
        """
        Clear the response cache.

        Returns:
            Number of entries cleared
        """
        return self._cache.clear()

    def invalidate_cache(self, query: str) -> bool:
        """
        Invalidate a specific cache entry.

        Args:
            query: The query to invalidate

        Returns:
            True if entry was found and removed
        """
        return self._cache.invalidate(query)
