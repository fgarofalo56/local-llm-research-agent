"""
Vector Store Factory

Factory pattern for creating vector store instances based on configuration.
Supports MSSQL (SQL Server 2025) and Redis Stack implementations.
"""

from typing import Literal

import structlog
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import async_sessionmaker

from src.rag.embedder import OllamaEmbedder
from src.rag.mssql_vector_store import MSSQLVectorStore
from src.rag.redis_vector_store import RedisVectorStore
from src.rag.vector_store_base import VectorStoreBase

logger = structlog.get_logger()

VectorStoreType = Literal["mssql", "redis"]


class VectorStoreFactory:
    """Factory for creating vector store instances."""

    @staticmethod
    async def create(
        store_type: VectorStoreType,
        embedder: OllamaEmbedder,
        dimensions: int = 768,
        session_factory: async_sessionmaker | None = None,
        redis_client: Redis | None = None,
    ) -> VectorStoreBase:
        """
        Create a vector store instance.

        Args:
            store_type: Type of vector store ('mssql' or 'redis')
            embedder: Ollama embedder instance
            dimensions: Embedding dimensions (default: 768)
            session_factory: SQLAlchemy session factory (required for MSSQL)
            redis_client: Redis client (required for Redis)

        Returns:
            Initialized vector store instance

        Raises:
            ValueError: If invalid store type or missing required dependencies
            RuntimeError: If vector store initialization fails
        """
        store_type_lower = store_type.lower()

        if store_type_lower == "mssql":
            return await VectorStoreFactory._create_mssql_store(
                embedder=embedder,
                dimensions=dimensions,
                session_factory=session_factory,
            )
        elif store_type_lower == "redis":
            return await VectorStoreFactory._create_redis_store(
                embedder=embedder,
                dimensions=dimensions,
                redis_client=redis_client,
            )
        else:
            raise ValueError(
                f"Invalid vector store type: {store_type}. Supported types: 'mssql', 'redis'"
            )

    @staticmethod
    async def _create_mssql_store(
        embedder: OllamaEmbedder,
        dimensions: int,
        session_factory: async_sessionmaker | None,
    ) -> MSSQLVectorStore:
        """
        Create MSSQL vector store.

        Args:
            embedder: Ollama embedder instance
            dimensions: Embedding dimensions
            session_factory: SQLAlchemy session factory

        Returns:
            Initialized MSSQL vector store

        Raises:
            ValueError: If session_factory is None
            RuntimeError: If initialization fails
        """
        if session_factory is None:
            raise ValueError("session_factory is required for MSSQL vector store")

        logger.info("creating_mssql_vector_store", dimensions=dimensions)

        try:
            store = MSSQLVectorStore(
                session_factory=session_factory,
                embedder=embedder,
                dimensions=dimensions,
            )
            await store.create_index()
            logger.info("mssql_vector_store_created", dimensions=dimensions)
            return store
        except Exception as e:
            logger.error("mssql_vector_store_creation_failed", error=str(e))
            raise RuntimeError(f"Failed to create MSSQL vector store: {e}") from e

    @staticmethod
    async def _create_redis_store(
        embedder: OllamaEmbedder,
        dimensions: int,
        redis_client: Redis | None,
    ) -> RedisVectorStore:
        """
        Create Redis vector store.

        Args:
            embedder: Ollama embedder instance
            dimensions: Embedding dimensions
            redis_client: Redis client instance

        Returns:
            Initialized Redis vector store

        Raises:
            ValueError: If redis_client is None
            RuntimeError: If initialization fails
        """
        if redis_client is None:
            raise ValueError("redis_client is required for Redis vector store")

        logger.info("creating_redis_vector_store", dimensions=dimensions)

        try:
            store = RedisVectorStore(
                redis_client=redis_client,
                embedder=embedder,
                dimensions=dimensions,
            )
            await store.create_index()
            logger.info("redis_vector_store_created", dimensions=dimensions)
            return store
        except Exception as e:
            logger.error("redis_vector_store_creation_failed", error=str(e))
            raise RuntimeError(f"Failed to create Redis vector store: {e}") from e

    @staticmethod
    async def create_with_fallback(
        primary_type: VectorStoreType,
        fallback_type: VectorStoreType,
        embedder: OllamaEmbedder,
        dimensions: int = 768,
        session_factory: async_sessionmaker | None = None,
        redis_client: Redis | None = None,
    ) -> VectorStoreBase:
        """
        Create a vector store with fallback support.

        Attempts to create the primary store type. If that fails, falls back
        to the secondary type.

        Args:
            primary_type: Primary store type to try
            fallback_type: Fallback store type if primary fails
            embedder: Ollama embedder instance
            dimensions: Embedding dimensions
            session_factory: SQLAlchemy session factory
            redis_client: Redis client

        Returns:
            Initialized vector store (primary or fallback)

        Raises:
            RuntimeError: If both primary and fallback fail
        """
        # Try primary store
        try:
            logger.info("attempting_primary_vector_store", type=primary_type)
            return await VectorStoreFactory.create(
                store_type=primary_type,
                embedder=embedder,
                dimensions=dimensions,
                session_factory=session_factory,
                redis_client=redis_client,
            )
        except Exception as primary_error:
            logger.warning(
                "primary_vector_store_failed",
                type=primary_type,
                error=str(primary_error),
            )

            # Try fallback store
            try:
                logger.info(
                    "attempting_fallback_vector_store",
                    type=fallback_type,
                )
                store = await VectorStoreFactory.create(
                    store_type=fallback_type,
                    embedder=embedder,
                    dimensions=dimensions,
                    session_factory=session_factory,
                    redis_client=redis_client,
                )
                logger.info("using_fallback_vector_store", type=fallback_type)
                return store
            except Exception as fallback_error:
                logger.error(
                    "both_vector_stores_failed",
                    primary_type=primary_type,
                    fallback_type=fallback_type,
                    primary_error=str(primary_error),
                    fallback_error=str(fallback_error),
                )
                raise RuntimeError(
                    f"Failed to create vector store. "
                    f"Primary ({primary_type}): {primary_error}. "
                    f"Fallback ({fallback_type}): {fallback_error}"
                ) from fallback_error
