"""
Tests for Redis Cache Backend for RAG Operations

Tests the Redis-backed caching functionality for embeddings and search results.
"""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.utils.cache import RedisCacheBackend


@pytest.fixture
def mock_redis():
    """Mock Redis async client."""
    redis = MagicMock()
    redis.get = AsyncMock(return_value=None)
    redis.setex = AsyncMock()
    redis.keys = AsyncMock(return_value=[])
    redis.delete = AsyncMock(return_value=0)
    redis.info = AsyncMock(
        return_value={
            "keyspace_hits": 100,
            "keyspace_misses": 50,
        }
    )
    return redis


@pytest.fixture
def cache_backend(mock_redis):
    """Create RedisCacheBackend instance with mock Redis."""
    return RedisCacheBackend(mock_redis, prefix="test_rag")


class TestRedisCacheBackend:
    """Tests for RedisCacheBackend class."""

    @pytest.mark.asyncio
    async def test_initialization(self, mock_redis):
        """Test cache backend initialization."""
        cache = RedisCacheBackend(mock_redis, prefix="custom")
        assert cache.redis is mock_redis
        assert cache.prefix == "custom"

    @pytest.mark.asyncio
    async def test_default_prefix(self, mock_redis):
        """Test default prefix is 'rag'."""
        cache = RedisCacheBackend(mock_redis)
        assert cache.prefix == "rag"

    def test_make_key(self, cache_backend):
        """Test cache key generation."""
        key = cache_backend._make_key("embedding", "abc123")
        assert key == "test_rag:embedding:abc123"

    def test_hash_content(self, cache_backend):
        """Test content hashing."""
        hash1 = cache_backend._hash_content("test content")
        hash2 = cache_backend._hash_content("test content")
        hash3 = cache_backend._hash_content("different content")

        # Same content produces same hash
        assert hash1 == hash2
        # Different content produces different hash
        assert hash1 != hash3
        # Hash is 16 characters (SHA256 truncated)
        assert len(hash1) == 16

    @pytest.mark.asyncio
    async def test_get_embedding_miss(self, cache_backend, mock_redis):
        """Test getting embedding that doesn't exist."""
        mock_redis.get.return_value = None

        result = await cache_backend.get_embedding("test text")

        assert result is None
        mock_redis.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_embedding_hit(self, cache_backend, mock_redis):
        """Test getting cached embedding."""
        embedding = [0.1, 0.2, 0.3]
        mock_redis.get.return_value = json.dumps(embedding)

        result = await cache_backend.get_embedding("test text")

        assert result == embedding
        mock_redis.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_set_embedding(self, cache_backend, mock_redis):
        """Test caching an embedding."""
        embedding = [0.1, 0.2, 0.3]

        await cache_backend.set_embedding("test text", embedding)

        mock_redis.setex.assert_called_once()
        # Check that TTL is set (default 7 days = 604800 seconds)
        args = mock_redis.setex.call_args
        assert args[0][1] == 604800  # TTL
        # Check that embedding is JSON serialized
        assert json.loads(args[0][2]) == embedding

    @pytest.mark.asyncio
    async def test_set_embedding_custom_ttl(self, cache_backend, mock_redis):
        """Test caching an embedding with custom TTL."""
        embedding = [0.1, 0.2, 0.3]

        await cache_backend.set_embedding("test text", embedding, ttl=3600)

        args = mock_redis.setex.call_args
        assert args[0][1] == 3600  # Custom TTL

    @pytest.mark.asyncio
    async def test_get_search_results_miss(self, cache_backend, mock_redis):
        """Test getting search results that don't exist."""
        mock_redis.get.return_value = None

        result = await cache_backend.get_search_results(
            query="test query", top_k=5, source_type="document"
        )

        assert result is None
        mock_redis.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_search_results_hit(self, cache_backend, mock_redis):
        """Test getting cached search results."""
        search_results = [
            {"text": "result 1", "score": 0.9},
            {"text": "result 2", "score": 0.8},
        ]
        mock_redis.get.return_value = json.dumps(search_results)

        result = await cache_backend.get_search_results(
            query="test query", top_k=5, source_type="document"
        )

        assert result == search_results
        mock_redis.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_search_results_none_source_type(self, cache_backend, mock_redis):
        """Test search results with None source_type uses 'all'."""
        mock_redis.get.return_value = None

        await cache_backend.get_search_results(
            query="test query", top_k=5, source_type=None
        )

        # Should use 'all' in cache key when source_type is None
        # Verify the cache key was generated with 'all' by checking the hash matches
        expected_hash = cache_backend._hash_content("test query:5:all")
        expected_key = cache_backend._make_key("search", expected_hash)

        call_args = mock_redis.get.call_args[0][0]
        assert call_args == expected_key

    @pytest.mark.asyncio
    async def test_set_search_results(self, cache_backend, mock_redis):
        """Test caching search results."""
        search_results = [
            {"text": "result 1", "score": 0.9},
            {"text": "result 2", "score": 0.8},
        ]

        await cache_backend.set_search_results(
            query="test query",
            top_k=5,
            source_type="document",
            results=search_results,
        )

        mock_redis.setex.assert_called_once()
        # Check default TTL (1 hour = 3600 seconds)
        args = mock_redis.setex.call_args
        assert args[0][1] == 3600
        # Check results are serialized
        assert json.loads(args[0][2]) == search_results

    @pytest.mark.asyncio
    async def test_set_search_results_custom_ttl(self, cache_backend, mock_redis):
        """Test caching search results with custom TTL."""
        search_results = [{"text": "result 1", "score": 0.9}]

        await cache_backend.set_search_results(
            query="test query",
            top_k=5,
            source_type="document",
            results=search_results,
            ttl=7200,
        )

        args = mock_redis.setex.call_args
        assert args[0][1] == 7200  # Custom TTL

    @pytest.mark.asyncio
    async def test_invalidate_document_no_keys(self, cache_backend, mock_redis):
        """Test invalidating document with no matching keys."""
        mock_redis.keys.return_value = []

        count = await cache_backend.invalidate_document("doc123")

        assert count == 0
        mock_redis.keys.assert_called_once()
        mock_redis.delete.assert_not_called()

    @pytest.mark.asyncio
    async def test_invalidate_document_with_keys(self, cache_backend, mock_redis):
        """Test invalidating document with matching keys."""
        mock_redis.keys.return_value = [
            "test_rag:embedding:doc123_chunk1",
            "test_rag:search:doc123_query",
        ]
        mock_redis.delete.return_value = 2

        count = await cache_backend.invalidate_document("doc123")

        assert count == 2
        mock_redis.keys.assert_called_once_with("test_rag:*:doc123*")
        mock_redis.delete.assert_called_once_with(
            "test_rag:embedding:doc123_chunk1",
            "test_rag:search:doc123_query",
        )

    @pytest.mark.asyncio
    async def test_get_stats(self, cache_backend, mock_redis):
        """Test getting cache statistics."""
        mock_redis.info.return_value = {
            "keyspace_hits": 100,
            "keyspace_misses": 50,
        }

        stats = await cache_backend.get_stats()

        assert stats["hits"] == 100
        assert stats["misses"] == 50
        assert stats["hit_rate"] == 100 / 150  # 0.6666...
        mock_redis.info.assert_called_once_with("stats")

    @pytest.mark.asyncio
    async def test_get_stats_no_activity(self, cache_backend, mock_redis):
        """Test getting stats with no cache activity."""
        mock_redis.info.return_value = {
            "keyspace_hits": 0,
            "keyspace_misses": 0,
        }

        stats = await cache_backend.get_stats()

        assert stats["hits"] == 0
        assert stats["misses"] == 0
        assert stats["hit_rate"] == 0.0

    @pytest.mark.asyncio
    async def test_embedding_cache_key_consistency(self, cache_backend):
        """Test that same text generates same cache key."""
        text = "consistent text"
        hash1 = cache_backend._hash_content(text)
        hash2 = cache_backend._hash_content(text)

        key1 = cache_backend._make_key("embedding", hash1)
        key2 = cache_backend._make_key("embedding", hash2)

        assert key1 == key2

    @pytest.mark.asyncio
    async def test_search_cache_key_includes_all_parameters(self, cache_backend):
        """Test that search cache key includes query, top_k, and source_type."""
        # Different queries should produce different keys
        hash1 = cache_backend._hash_content("query1:5:document")
        hash2 = cache_backend._hash_content("query2:5:document")
        assert hash1 != hash2

        # Different top_k should produce different keys
        hash3 = cache_backend._hash_content("query1:5:document")
        hash4 = cache_backend._hash_content("query1:10:document")
        assert hash3 != hash4

        # Different source_type should produce different keys
        hash5 = cache_backend._hash_content("query1:5:document")
        hash6 = cache_backend._hash_content("query1:5:schema")
        assert hash5 != hash6


class TestEmbedderWithCache:
    """Tests for OllamaEmbedder.embed_with_cache method."""

    @pytest.fixture
    def mock_embedder(self):
        """Mock OllamaEmbedder."""
        from src.rag.embedder import OllamaEmbedder

        embedder = OllamaEmbedder()
        embedder.embed = AsyncMock(return_value=[0.1, 0.2, 0.3])
        return embedder

    @pytest.mark.asyncio
    async def test_embed_with_cache_no_cache(self, mock_embedder):
        """Test embed_with_cache without cache."""
        result = await mock_embedder.embed_with_cache("test text", cache=None)

        assert result == [0.1, 0.2, 0.3]
        mock_embedder.embed.assert_called_once_with("test text")

    @pytest.mark.asyncio
    async def test_embed_with_cache_miss(self, mock_embedder, cache_backend, mock_redis):
        """Test embed_with_cache with cache miss."""
        mock_redis.get.return_value = None

        result = await mock_embedder.embed_with_cache("test text", cache=cache_backend)

        assert result == [0.1, 0.2, 0.3]
        mock_embedder.embed.assert_called_once_with("test text")
        mock_redis.setex.assert_called_once()  # Should cache the result

    @pytest.mark.asyncio
    async def test_embed_with_cache_hit(self, mock_embedder, cache_backend, mock_redis):
        """Test embed_with_cache with cache hit."""
        cached_embedding = [0.4, 0.5, 0.6]
        mock_redis.get.return_value = json.dumps(cached_embedding)

        result = await mock_embedder.embed_with_cache("test text", cache=cache_backend)

        assert result == cached_embedding
        mock_embedder.embed.assert_not_called()  # Should not generate new embedding
        mock_redis.setex.assert_not_called()  # Should not cache again

    @pytest.mark.asyncio
    async def test_embed_with_cache_saves_on_miss(
        self, mock_embedder, cache_backend, mock_redis
    ):
        """Test that cache saves embedding on miss."""
        mock_redis.get.return_value = None
        expected_embedding = [0.1, 0.2, 0.3]

        await mock_embedder.embed_with_cache("test text", cache=cache_backend)

        # Verify setex was called with correct embedding
        args = mock_redis.setex.call_args
        saved_embedding = json.loads(args[0][2])
        assert saved_embedding == expected_embedding


class TestIntegrationScenarios:
    """Integration test scenarios for Redis caching."""

    @pytest.mark.asyncio
    async def test_embedding_workflow(self, cache_backend, mock_redis):
        """Test complete embedding cache workflow."""
        text = "sample text for embedding"
        embedding = [0.1, 0.2, 0.3, 0.4, 0.5]

        # First request - cache miss
        mock_redis.get.return_value = None
        result = await cache_backend.get_embedding(text)
        assert result is None

        # Save to cache
        await cache_backend.set_embedding(text, embedding)
        assert mock_redis.setex.called

        # Second request - cache hit
        mock_redis.get.return_value = json.dumps(embedding)
        result = await cache_backend.get_embedding(text)
        assert result == embedding

    @pytest.mark.asyncio
    async def test_search_results_workflow(self, cache_backend, mock_redis):
        """Test complete search results cache workflow."""
        query = "research papers"
        top_k = 5
        source_type = "document"
        results = [
            {"text": "paper 1", "score": 0.95},
            {"text": "paper 2", "score": 0.87},
        ]

        # First search - cache miss
        mock_redis.get.return_value = None
        cached = await cache_backend.get_search_results(query, top_k, source_type)
        assert cached is None

        # Save results
        await cache_backend.set_search_results(query, top_k, source_type, results)
        assert mock_redis.setex.called

        # Second search - cache hit
        mock_redis.get.return_value = json.dumps(results)
        cached = await cache_backend.get_search_results(query, top_k, source_type)
        assert cached == results

    @pytest.mark.asyncio
    async def test_document_invalidation_workflow(self, cache_backend, mock_redis):
        """Test document invalidation workflow."""
        # Setup: document has cached entries
        doc_id = "doc_12345"
        mock_redis.keys.return_value = [
            f"test_rag:embedding:{doc_id}_chunk1",
            f"test_rag:embedding:{doc_id}_chunk2",
            f"test_rag:search:query_{doc_id}",
        ]
        mock_redis.delete.return_value = 3

        # Invalidate document
        count = await cache_backend.invalidate_document(doc_id)

        assert count == 3
        mock_redis.keys.assert_called_once()
        mock_redis.delete.assert_called_once()
