"""
FastAPI Application
Phase 2.1: Backend Infrastructure & RAG Pipeline

Main entry point for the FastAPI backend API.
"""

from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware

from src.api.deps import init_services, shutdown_services
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
from src.api.routes.agent import agent_websocket

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup and shutdown."""
    logger.info("starting_application")
    await init_services()
    yield
    logger.info("shutting_down_application")
    await shutdown_services()


# Create FastAPI application
app = FastAPI(
    title="Local LLM Research Analytics API",
    description="API for local LLM-powered SQL Server analytics with RAG support",
    version="2.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite dev server
        "http://localhost:3000",  # Alternative React port
        "http://localhost:8501",  # Streamlit
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8501",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, prefix="/api/health", tags=["Health"])
app.include_router(documents.router, prefix="/api/documents", tags=["Documents"])
app.include_router(conversations.router, prefix="/api/conversations", tags=["Conversations"])
app.include_router(queries.router, prefix="/api/queries", tags=["Queries"])
app.include_router(dashboards.router, prefix="/api/dashboards", tags=["Dashboards"])
app.include_router(mcp_servers.router, prefix="/api/mcp-servers", tags=["MCP Servers"])
app.include_router(settings.router, prefix="/api/settings", tags=["Settings"])
app.include_router(agent.router, prefix="/api/agent", tags=["Agent"])
app.include_router(alerts.router, prefix="/api/alerts", tags=["Alerts"])
app.include_router(scheduled_queries.router, prefix="/api/scheduled-queries", tags=["Scheduled Queries"])


@app.get("/")
async def root():
    """Root endpoint returning API information."""
    return {
        "message": "Local LLM Research Analytics API",
        "version": "2.2.0",
        "docs": "/docs",
        "health": "/api/health",
    }


# Top-level WebSocket route for easier frontend access
# This provides /ws/agent/{id} in addition to /api/agent/ws/{id}
@app.websocket("/ws/agent/{conversation_id}")
async def websocket_agent(websocket: WebSocket, conversation_id: int):
    """WebSocket endpoint for agent chat at /ws/agent/{conversation_id}."""
    await agent_websocket(websocket, conversation_id)


# WebSocket endpoint for real-time alert notifications
@app.websocket("/ws/alerts")
async def websocket_alerts(websocket: WebSocket):
    """WebSocket endpoint for real-time alert notifications."""
    from src.services.notification_service import NotificationService

    await websocket.accept()
    client_id = f"alerts-{id(websocket)}"

    # Register this client for notifications
    NotificationService.register_client(client_id, websocket)
    logger.info("alert_websocket_connected", client_id=client_id)

    try:
        # Keep connection alive and wait for disconnect
        while True:
            try:
                # Wait for ping/pong or disconnect
                data = await websocket.receive_text()
                # Handle ping
                if data == "ping":
                    await websocket.send_text("pong")
            except Exception:
                break
    finally:
        NotificationService.unregister_client(client_id, websocket)
        logger.info("alert_websocket_disconnected", client_id=client_id)
