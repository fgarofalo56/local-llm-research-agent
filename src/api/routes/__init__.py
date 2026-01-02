"""
API Routes Package
Phase 2.1, 2.5, 3: Backend Infrastructure, RAG Pipeline, Advanced Features, Superset

FastAPI route modules.
"""

from src.api.routes import (
    agent,
    alerts,
    analytics,
    auth,
    conversations,
    dashboards,
    database_connections,
    documents,
    health,
    mcp_servers,
    queries,
    scheduled_queries,
    settings,
    superset,
)

__all__ = [
    "health",
    "documents",
    "conversations",
    "queries",
    "dashboards",
    "mcp_servers",
    "settings",
    "agent",
    "alerts",
    "scheduled_queries",
    "superset",
    "database_connections",
    "analytics",
    "auth",
]
