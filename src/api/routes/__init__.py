"""
API Routes Package
Phase 2.1 & 2.5: Backend Infrastructure, RAG Pipeline, Advanced Features

FastAPI route modules.
"""

from src.api.routes import (
    agent,
    alerts,
    conversations,
    dashboards,
    documents,
    health,
    mcp_servers,
    queries,
    scheduled_queries,
    settings,
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
]
