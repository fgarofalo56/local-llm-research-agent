"""
API Routes Package
Phase 2.1: Backend Infrastructure & RAG Pipeline

FastAPI route modules.
"""

from src.api.routes import (
    agent,
    conversations,
    dashboards,
    documents,
    health,
    mcp_servers,
    queries,
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
]
