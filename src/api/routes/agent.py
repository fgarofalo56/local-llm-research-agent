"""
Agent Routes
Phase 2.1: Backend Infrastructure & RAG Pipeline

Endpoints for interacting with the research agent.
"""

import structlog
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from src.api.deps import get_vector_store_optional
from src.utils.config import get_settings

router = APIRouter()
logger = structlog.get_logger()


class ChatRequest(BaseModel):
    """Request model for chat."""

    message: str
    conversation_id: int | None = None
    use_rag: bool = True
    mcp_servers: list[str] | None = None  # List of server IDs to use


class ChatResponse(BaseModel):
    """Response model for chat."""

    response: str
    conversation_id: int | None
    sources: list[dict] | None = None  # RAG sources used
    tool_calls: list[dict] | None = None


class RAGSearchRequest(BaseModel):
    """Request model for RAG search."""

    query: str
    top_k: int = 5
    source_type: str | None = None  # 'document', 'schema', or None for all


class RAGSearchResponse(BaseModel):
    """Response model for RAG search."""

    results: list[dict]
    query: str


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    vector_store=Depends(get_vector_store_optional),
):
    """
    Send a message to the research agent.

    This is a placeholder endpoint for Phase 2.2 integration.
    Currently returns a simple acknowledgment.
    """
    logger.info(
        "chat_request",
        message_length=len(request.message),
        use_rag=request.use_rag,
        mcp_servers=request.mcp_servers,
    )

    # Placeholder response
    return ChatResponse(
        response="Agent chat endpoint is available. Full implementation in Phase 2.2.",
        conversation_id=request.conversation_id,
        sources=None,
        tool_calls=None,
    )


@router.post("/search", response_model=RAGSearchResponse)
async def rag_search(
    request: RAGSearchRequest,
    vector_store=Depends(get_vector_store_optional),
):
    """
    Search the RAG vector store.

    Returns relevant documents/schema based on the query.
    """
    if not vector_store:
        raise HTTPException(
            status_code=503,
            detail="Vector store not available",
        )

    try:
        results = await vector_store.search(
            query=request.query,
            top_k=request.top_k,
            source_type=request.source_type,
        )

        return RAGSearchResponse(
            results=results,
            query=request.query,
        )

    except Exception as e:
        logger.error("rag_search_error", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Search failed: {str(e)}",
        )


@router.get("/models")
async def list_models():
    """List available LLM models."""
    settings = get_settings()

    return {
        "provider": settings.llm_provider,
        "models": {
            "chat": settings.ollama_model,
            "embedding": settings.embedding_model,
        },
        "ollama_host": settings.ollama_host,
    }


@router.get("/rag/stats")
async def get_rag_stats(
    vector_store=Depends(get_vector_store_optional),
):
    """Get RAG vector store statistics."""
    if not vector_store:
        return {"status": "unavailable"}

    try:
        stats = await vector_store.get_stats()
        return {"status": "available", **stats}
    except Exception as e:
        logger.error("rag_stats_error", error=str(e))
        return {"status": "error", "error": str(e)}
