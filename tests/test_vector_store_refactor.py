"""
Test Vector Store Refactoring

Tests for the abstract base class and factory pattern.
"""

from unittest.mock import Mock

import pytest

from src.rag.embedder import OllamaEmbedder
from src.rag.mssql_vector_store import MSSQLVectorStore
from src.rag.redis_vector_store import RedisVectorStore
from src.rag.vector_store_base import VectorStoreBase, VectorStoreProtocol
from src.rag.vector_store_factory import VectorStoreFactory


class TestVectorStoreBase:
    """Test the abstract base class."""

    def test_mssql_is_subclass(self):
        """Test that MSSQLVectorStore is a subclass of VectorStoreBase."""
        assert issubclass(MSSQLVectorStore, VectorStoreBase)

    def test_redis_is_subclass(self):
        """Test that RedisVectorStore is a subclass of VectorStoreBase."""
        assert issubclass(RedisVectorStore, VectorStoreBase)

    def test_mssql_has_required_methods(self):
        """Test that MSSQLVectorStore has all required abstract methods."""
        required_methods = [
            "create_index",
            "add_document",
            "search",
            "delete_document",
            "get_stats",
        ]
        for method in required_methods:
            assert hasattr(MSSQLVectorStore, method)
            assert callable(getattr(MSSQLVectorStore, method))

    def test_redis_has_required_methods(self):
        """Test that RedisVectorStore has all required abstract methods."""
        required_methods = [
            "create_index",
            "add_document",
            "search",
            "delete_document",
            "get_stats",
        ]
        for method in required_methods:
            assert hasattr(RedisVectorStore, method)
            assert callable(getattr(RedisVectorStore, method))

    def test_base_class_repr(self):
        """Test that base class provides a __repr__ method."""
        # We can't instantiate the abstract class directly,
        # but we can verify the repr works through subclasses
        mock_session_factory = Mock()
        mock_embedder = Mock(spec=OllamaEmbedder)

        store = MSSQLVectorStore(
            session_factory=mock_session_factory,
            embedder=mock_embedder,
            dimensions=768,
        )

        repr_str = repr(store)
        assert "MSSQLVectorStore" in repr_str
        assert "768" in repr_str


class TestVectorStoreFactory:
    """Test the factory pattern."""

    @pytest.mark.asyncio
    async def test_create_mssql_requires_session_factory(self):
        """Test that MSSQL creation requires session_factory."""
        mock_embedder = Mock(spec=OllamaEmbedder)

        with pytest.raises(ValueError, match="session_factory is required"):
            await VectorStoreFactory.create(
                store_type="mssql",
                embedder=mock_embedder,
                dimensions=768,
                session_factory=None,
                redis_client=None,
            )

    @pytest.mark.asyncio
    async def test_create_redis_requires_redis_client(self):
        """Test that Redis creation requires redis_client."""
        mock_embedder = Mock(spec=OllamaEmbedder)

        with pytest.raises(ValueError, match="redis_client is required"):
            await VectorStoreFactory.create(
                store_type="redis",
                embedder=mock_embedder,
                dimensions=768,
                session_factory=None,
                redis_client=None,
            )

    def test_invalid_store_type(self):
        """Test that invalid store type raises ValueError."""
        mock_embedder = Mock(spec=OllamaEmbedder)

        with pytest.raises(ValueError, match="Invalid vector store type"):
            # Use asyncio.run since this is an async function
            import asyncio

            asyncio.run(
                VectorStoreFactory.create(
                    store_type="invalid",  # type: ignore
                    embedder=mock_embedder,
                    dimensions=768,
                )
            )


class TestTypeCompatibility:
    """Test type compatibility and protocol adherence."""

    def test_mssql_satisfies_protocol(self):
        """Test that MSSQLVectorStore satisfies VectorStoreProtocol."""
        mock_session_factory = Mock()
        mock_embedder = Mock(spec=OllamaEmbedder)

        store = MSSQLVectorStore(
            session_factory=mock_session_factory,
            embedder=mock_embedder,
            dimensions=768,
        )

        # Protocol check - if this type checks, it satisfies the protocol
        _: VectorStoreProtocol = store

    def test_redis_satisfies_protocol(self):
        """Test that RedisVectorStore satisfies VectorStoreProtocol."""
        mock_redis = Mock()
        mock_embedder = Mock(spec=OllamaEmbedder)

        store = RedisVectorStore(
            redis_client=mock_redis,
            embedder=mock_embedder,
            dimensions=768,
        )

        # Protocol check - if this type checks, it satisfies the protocol
        _: VectorStoreProtocol = store

    def test_base_class_can_be_type_hint(self):
        """Test that VectorStoreBase can be used as a type hint."""

        def accept_vector_store(store: VectorStoreBase) -> str:
            return repr(store)

        mock_session_factory = Mock()
        mock_embedder = Mock(spec=OllamaEmbedder)

        mssql_store = MSSQLVectorStore(
            session_factory=mock_session_factory,
            embedder=mock_embedder,
            dimensions=768,
        )

        # This should type check correctly
        result = accept_vector_store(mssql_store)
        assert isinstance(result, str)


class TestBackwardCompatibility:
    """Test that existing code patterns still work."""

    def test_direct_mssql_instantiation(self):
        """Test that MSSQLVectorStore can still be instantiated directly."""
        mock_session_factory = Mock()
        mock_embedder = Mock(spec=OllamaEmbedder)

        # Old pattern - should still work
        store = MSSQLVectorStore(
            session_factory=mock_session_factory,
            embedder=mock_embedder,
            dimensions=768,
        )

        assert isinstance(store, MSSQLVectorStore)
        assert isinstance(store, VectorStoreBase)
        assert store.dimensions == 768

    def test_direct_redis_instantiation(self):
        """Test that RedisVectorStore can still be instantiated directly."""
        mock_redis = Mock()
        mock_embedder = Mock(spec=OllamaEmbedder)

        # Old pattern - should still work
        store = RedisVectorStore(
            redis_client=mock_redis,
            embedder=mock_embedder,
            dimensions=768,
        )

        assert isinstance(store, RedisVectorStore)
        assert isinstance(store, VectorStoreBase)
        assert store.dimensions == 768

    def test_schema_indexer_compatibility(self):
        """Test that SchemaIndexer accepts any VectorStoreBase."""
        from src.rag.schema_indexer import SchemaIndexer

        mock_session_factory = Mock()
        mock_embedder = Mock(spec=OllamaEmbedder)

        # Create MSSQL store
        mssql_store = MSSQLVectorStore(
            session_factory=mock_session_factory,
            embedder=mock_embedder,
            dimensions=768,
        )

        # SchemaIndexer should accept it
        indexer = SchemaIndexer(vector_store=mssql_store)
        assert indexer.vector_store is mssql_store

        # Create Redis store
        mock_redis = Mock()
        redis_store = RedisVectorStore(
            redis_client=mock_redis,
            embedder=mock_embedder,
            dimensions=768,
        )

        # SchemaIndexer should accept it too
        indexer2 = SchemaIndexer(vector_store=redis_store)
        assert indexer2.vector_store is redis_store
