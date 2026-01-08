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

# Preset themes configuration
PRESET_THEMES = [
    {
        "name": "default",
        "display_name": "Default (Light)",
        "config": """{
            "primaryColor": "#FF4B4B",
            "backgroundColor": "#FFFFFF",
            "secondaryBackgroundColor": "#F0F2F6",
            "textColor": "#262730",
            "font": "sans serif"
        }""",
        "is_active": True,
    },
    {
        "name": "dark",
        "display_name": "Dark Mode",
        "config": """{
            "primaryColor": "#FF4B4B",
            "backgroundColor": "#0E1117",
            "secondaryBackgroundColor": "#262730",
            "textColor": "#FAFAFA",
            "font": "sans serif"
        }""",
        "is_active": False,
    },
    {
        "name": "blue",
        "display_name": "Professional Blue",
        "config": """{
            "primaryColor": "#1E88E5",
            "backgroundColor": "#FFFFFF",
            "secondaryBackgroundColor": "#E3F2FD",
            "textColor": "#1A237E",
            "font": "sans serif"
        }""",
        "is_active": False,
    },
    {
        "name": "green",
        "display_name": "Forest Green",
        "config": """{
            "primaryColor": "#43A047",
            "backgroundColor": "#FFFFFF",
            "secondaryBackgroundColor": "#E8F5E9",
            "textColor": "#1B5E20",
            "font": "sans serif"
        }""",
        "is_active": False,
    },
    {
        "name": "purple",
        "display_name": "Royal Purple",
        "config": """{
            "primaryColor": "#7E57C2",
            "backgroundColor": "#FFFFFF",
            "secondaryBackgroundColor": "#EDE7F6",
            "textColor": "#311B92",
            "font": "sans serif"
        }""",
        "is_active": False,
    },
]


async def _seed_preset_themes(session_factory) -> None:
    """Seed preset themes into the database if they don't exist."""
    from sqlalchemy import select

    from src.api.models.database import ThemeConfig

    async with session_factory() as session:
        # Check if any preset themes exist
        result = await session.execute(select(ThemeConfig).where(ThemeConfig.is_preset == True))
        existing_presets = {t.name for t in result.scalars().all()}

        # Add missing preset themes
        for theme_data in PRESET_THEMES:
            if theme_data["name"] not in existing_presets:
                theme = ThemeConfig(
                    name=theme_data["name"],
                    display_name=theme_data["display_name"],
                    config=theme_data["config"],
                    is_preset=True,
                    is_active=theme_data["is_active"],
                )
                session.add(theme)
                logger.info("theme_added", name=theme_data["name"])

        await session.commit()


# Global instances (initialized on startup)
_engine = None  # Sample database (ResearchAnalytics)
_session_factory = None  # Sample database sessions
_backend_engine = None  # Backend database (LLM_BackEnd)
_backend_session_factory = None  # Backend database sessions
_redis_client: Redis | None = None
_vector_store = None
_embedder = None
_mcp_manager = None
_alert_scheduler = None
_query_scheduler = None
_websocket_manager = None


async def init_services() -> None:
    """Initialize all services on application startup."""
    global _engine, _session_factory, _backend_engine, _backend_session_factory
    global _redis_client, _vector_store, _embedder, _mcp_manager
    global _alert_scheduler, _query_scheduler, _websocket_manager

    settings = get_settings()

    # Initialize sample database engine (ResearchAnalytics - for demo queries)
    try:
        _engine = create_async_engine(
            settings.database_url_async,
            echo=settings.debug,
            pool_pre_ping=True,
        )
        _session_factory = async_sessionmaker(_engine, expire_on_commit=False)
        logger.info("sample_database_engine_initialized", database="ResearchAnalytics")
    except Exception as e:
        logger.warning("sample_database_engine_failed", error=str(e))

    # Initialize backend database engine (LLM_BackEnd - app state + vectors)
    try:
        _backend_engine = create_async_engine(
            settings.backend_database_url_async,
            echo=settings.debug,
            pool_pre_ping=True,
        )
        _backend_session_factory = async_sessionmaker(_backend_engine, expire_on_commit=False)
        logger.info("backend_database_engine_initialized", database="LLM_BackEnd")
    except Exception as e:
        logger.warning("backend_database_engine_failed", error=str(e))
        # Fall back to sample database for app state if backend not available
        if _session_factory:
            _backend_session_factory = _session_factory
            logger.info("using_sample_database_for_backend_fallback")

    # Initialize Redis client (for caching, optional vector fallback)
    try:
        _redis_client = Redis.from_url(settings.redis_url, decode_responses=True)
        await _redis_client.ping()
        logger.info("redis_connection_established")
    except Exception as e:
        logger.warning("redis_connection_failed", error=str(e))
        _redis_client = None

    # Initialize embedder (required for vector operations)
    try:
        from src.rag.embedder import OllamaEmbedder

        _embedder = OllamaEmbedder(
            base_url=settings.ollama_host,
            model=settings.embedding_model,
        )
        logger.info("embedder_initialized", model=settings.embedding_model)
    except Exception as e:
        logger.warning("embedder_init_failed", error=str(e))

    # Initialize vector store based on configuration
    if _embedder:
        vector_store_type = settings.vector_store_type.lower()

        # Try MSSQL vector store first (SQL Server 2025)
        if vector_store_type == "mssql" and _backend_session_factory:
            try:
                from src.rag.mssql_vector_store import MSSQLVectorStore

                _vector_store = MSSQLVectorStore(
                    session_factory=_backend_session_factory,
                    embedder=_embedder,
                    dimensions=settings.vector_dimensions,
                )
                await _vector_store.create_index()
                logger.info(
                    "vector_store_initialized", type="mssql", dimensions=settings.vector_dimensions
                )
            except Exception as e:
                logger.warning("mssql_vector_store_init_failed", error=str(e))
                # Fall back to Redis if MSSQL fails
                if _redis_client:
                    logger.info("falling_back_to_redis_vector_store")
                    vector_store_type = "redis"

        # Redis vector store (fallback or explicit choice)
        if vector_store_type == "redis" and _redis_client and _vector_store is None:
            try:
                from src.rag.redis_vector_store import RedisVectorStore

                _vector_store = RedisVectorStore(
                    redis_client=_redis_client,
                    embedder=_embedder,
                    dimensions=settings.vector_dimensions,
                )
                await _vector_store.create_index()
                logger.info(
                    "vector_store_initialized", type="redis", dimensions=settings.vector_dimensions
                )
            except Exception as e:
                logger.warning("redis_vector_store_init_failed", error=str(e))

    # Initialize MCP manager
    try:
        from src.mcp.dynamic_manager import DynamicMCPManager

        _mcp_manager = DynamicMCPManager(config_path=settings.mcp_config_path)
        await _mcp_manager.load_config()
        logger.info("mcp_manager_initialized")
    except Exception as e:
        logger.warning("mcp_manager_init_failed", error=str(e))

    # Initialize schedulers (only if backend database is available)
    if _backend_session_factory:
        try:
            from src.services.alert_scheduler import AlertScheduler
            from src.services.query_scheduler import QueryScheduler

            _alert_scheduler = AlertScheduler(session_factory=_backend_session_factory)
            await _alert_scheduler.start()
            logger.info("alert_scheduler_initialized")

            _query_scheduler = QueryScheduler(session_factory=_backend_session_factory)
            await _query_scheduler.start()
            logger.info("query_scheduler_initialized")
        except Exception as e:
            logger.warning("schedulers_init_failed", error=str(e))

        # Seed preset themes
        try:
            await _seed_preset_themes(_backend_session_factory)
            logger.info("preset_themes_seeded")
        except Exception as e:
            logger.warning("theme_seeding_failed", error=str(e))

    # Initialize WebSocket manager with heartbeat
    try:
        from src.api.websocket import websocket_manager as ws_mgr

        _websocket_manager = ws_mgr
        await _websocket_manager.start_heartbeat()
        logger.info("websocket_manager_initialized")
    except Exception as e:
        logger.warning("websocket_manager_init_failed", error=str(e))


async def shutdown_services() -> None:
    """Cleanup services on application shutdown."""
    global _engine, _backend_engine, _redis_client, _mcp_manager
    global _alert_scheduler, _query_scheduler, _websocket_manager

    # Stop WebSocket manager first
    if _websocket_manager:
        try:
            await _websocket_manager.shutdown()
        except Exception as e:
            logger.error("websocket_manager_shutdown_error", error=str(e))

    # Stop schedulers
    if _alert_scheduler:
        try:
            await _alert_scheduler.stop()
        except Exception as e:
            logger.error("alert_scheduler_shutdown_error", error=str(e))

    if _query_scheduler:
        try:
            await _query_scheduler.stop()
        except Exception as e:
            logger.error("query_scheduler_shutdown_error", error=str(e))

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

    # Dispose backend database engine
    if _backend_engine:
        try:
            await _backend_engine.dispose()
            logger.info("backend_database_disposed")
        except Exception as e:
            logger.error("backend_database_dispose_error", error=str(e))

    # Dispose sample database engine
    if _engine:
        try:
            await _engine.dispose()
            logger.info("sample_database_disposed")
        except Exception as e:
            logger.error("sample_database_dispose_error", error=str(e))

    logger.info("all_services_shutdown")


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Get backend database session for dependency injection.

    This is the primary database connection for application state,
    including conversations, messages, dashboards, documents, and vectors.
    Uses LLM_BackEnd database (SQL Server 2025 with native vector support).
    """
    if _backend_session_factory is None:
        raise RuntimeError("Backend database not initialized")

    async with _backend_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def get_sample_db() -> AsyncGenerator[AsyncSession, None]:
    """Get sample database session for dependency injection.

    This is the sample/demo database (ResearchAnalytics) used for
    demonstrating SQL queries and LLM capabilities. Not for app state.
    """
    if _session_factory is None:
        raise RuntimeError("Sample database not initialized")

    async with _session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


def get_backend_session_factory():
    """Get the backend session factory for background tasks."""
    return _backend_session_factory


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


def get_alert_scheduler():
    """Get alert scheduler for dependency injection."""
    return _alert_scheduler


def get_query_scheduler():
    """Get query scheduler for dependency injection."""
    return _query_scheduler


def get_websocket_manager():
    """Get WebSocket manager for dependency injection."""
    if _websocket_manager is None:
        raise RuntimeError("WebSocket manager not initialized")
    return _websocket_manager


def get_websocket_manager_optional():
    """Get WebSocket manager (optional, returns None if not available)."""
    return _websocket_manager
