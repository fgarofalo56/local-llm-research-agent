"""
API Dependencies
Phase 2.1: Backend Infrastructure & RAG Pipeline

Dependency injection for FastAPI routes.
Manages database sessions, Redis client, vector store, embedder, and MCP manager.
"""

from collections.abc import AsyncGenerator

import structlog
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.utils.config import get_settings

logger = structlog.get_logger()

# Global instances (initialized on startup)
_engine = None
_session_factory = None
_redis_client: Redis | None = None
_vector_store = None
_embedder = None
_mcp_manager = None


async def init_services() -> None:
    """Initialize all services on application startup."""
    global _engine, _session_factory, _redis_client, _vector_store, _embedder, _mcp_manager

    settings = get_settings()

    # Initialize database engine
    try:
        _engine = create_async_engine(
            settings.database_url_async,
            echo=settings.debug,
            pool_pre_ping=True,
        )
        _session_factory = async_sessionmaker(_engine, expire_on_commit=False)
        logger.info("database_engine_initialized")
    except Exception as e:
        logger.warning("database_engine_failed", error=str(e))
        # Continue without database for basic API functionality

    # Initialize Redis client
    try:
        _redis_client = Redis.from_url(settings.redis_url, decode_responses=True)
        await _redis_client.ping()
        logger.info("redis_connection_established")
    except Exception as e:
        logger.warning("redis_connection_failed", error=str(e))
        _redis_client = None

    # Initialize embedder (lazy, only if Redis is available)
    if _redis_client:
        try:
            from src.rag.embedder import OllamaEmbedder

            _embedder = OllamaEmbedder(
                base_url=settings.ollama_host,
                model=settings.embedding_model,
            )
            logger.info("embedder_initialized")
        except Exception as e:
            logger.warning("embedder_init_failed", error=str(e))

    # Initialize vector store (only if Redis and embedder are available)
    if _redis_client and _embedder:
        try:
            from src.rag.redis_vector_store import RedisVectorStore

            _vector_store = RedisVectorStore(
                redis_client=_redis_client,
                embedder=_embedder,
            )
            await _vector_store.create_index()
            logger.info("vector_store_initialized")
        except Exception as e:
            logger.warning("vector_store_init_failed", error=str(e))

    # Initialize MCP manager
    try:
        from src.mcp.dynamic_manager import DynamicMCPManager

        _mcp_manager = DynamicMCPManager(config_path=settings.mcp_config_path)
        await _mcp_manager.load_config()
        logger.info("mcp_manager_initialized")
    except Exception as e:
        logger.warning("mcp_manager_init_failed", error=str(e))


async def shutdown_services() -> None:
    """Cleanup services on application shutdown."""
    global _engine, _redis_client, _mcp_manager

    if _mcp_manager:
        try:
            await _mcp_manager.shutdown()
        except Exception as e:
            logger.error("mcp_manager_shutdown_error", error=str(e))

    if _redis_client:
        try:
            await _redis_client.close()
        except Exception as e:
            logger.error("redis_close_error", error=str(e))

    if _engine:
        try:
            await _engine.dispose()
        except Exception as e:
            logger.error("database_dispose_error", error=str(e))

    logger.info("all_services_shutdown")


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Get database session for dependency injection."""
    if _session_factory is None:
        raise RuntimeError("Database not initialized")

    async with _session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


def get_redis() -> Redis:
    """Get Redis client for dependency injection."""
    if _redis_client is None:
        raise RuntimeError("Redis not initialized")
    return _redis_client


def get_redis_optional() -> Redis | None:
    """Get Redis client (optional, returns None if not available)."""
    return _redis_client


def get_vector_store():
    """Get vector store for dependency injection."""
    if _vector_store is None:
        raise RuntimeError("Vector store not initialized")
    return _vector_store


def get_vector_store_optional():
    """Get vector store (optional, returns None if not available)."""
    return _vector_store


def get_embedder():
    """Get embedder for dependency injection."""
    if _embedder is None:
        raise RuntimeError("Embedder not initialized")
    return _embedder


def get_embedder_optional():
    """Get embedder (optional, returns None if not available)."""
    return _embedder


def get_mcp_manager():
    """Get MCP manager for dependency injection."""
    if _mcp_manager is None:
        raise RuntimeError("MCP manager not initialized")
    return _mcp_manager


def get_mcp_manager_optional():
    """Get MCP manager (optional, returns None if not available)."""
    return _mcp_manager
