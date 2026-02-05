"""
Agent Routes
Phase 2.1 & 2.2: Backend Infrastructure, RAG Pipeline & WebSocket Chat

Endpoints for interacting with the research agent.
"""

import contextlib

import structlog
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from src.agent.research_agent import ResearchAgentError, create_research_agent
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
    hybrid: bool = False  # Enable hybrid search (semantic + keyword)
    alpha: float = 0.5  # Weight for semantic search (0.0 = keyword only, 1.0 = semantic only)


class RAGSearchResponse(BaseModel):
    """Response model for RAG search."""

    results: list[dict]
    query: str
    search_type: str = "semantic"  # 'semantic', 'hybrid', or 'keyword'


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

    Supports two search modes:
    - **Semantic search** (default): Uses vector similarity for conceptual matching
    - **Hybrid search**: Combines semantic + keyword (full-text) search using RRF

    Args (in request body):
        query: Search query text
        top_k: Number of results to return (default: 5)
        source_type: Filter by source type ('document', 'schema', or None for all)
        hybrid: Enable hybrid search (default: False)
        alpha: Weight for semantic vs keyword (0.0 = keyword only, 1.0 = semantic only)
    """
    if not vector_store:
        raise HTTPException(
            status_code=503,
            detail="Vector store not available",
        )

    try:
        if request.hybrid:
            # Use hybrid search combining semantic + keyword
            results = await vector_store.hybrid_search(
                query=request.query,
                top_k=request.top_k,
                source_type=request.source_type,
                alpha=request.alpha,
            )
            search_type = "hybrid"
            logger.info(
                "hybrid_search_performed",
                query_length=len(request.query),
                top_k=request.top_k,
                alpha=request.alpha,
                results_count=len(results),
            )
        else:
            # Use standard semantic search
            results = await vector_store.search(
                query=request.query,
                top_k=request.top_k,
                source_type=request.source_type,
            )
            search_type = "semantic"

        return RAGSearchResponse(
            results=results,
            query=request.query,
            search_type=search_type,
        )

    except Exception as e:
        logger.error("rag_search_error", error=str(e), hybrid=request.hybrid)
        raise HTTPException(
            status_code=500,
            detail=f"Search failed: {str(e)}",
        )


@router.get("/models")
async def list_models():
    """List available LLM models and provider configuration."""
    settings = get_settings()

    return {
        "provider": settings.llm_provider,
        "models": {
            "chat": (
                settings.ollama_model
                if settings.llm_provider == "ollama"
                else settings.foundry_model
            ),
            "embedding": settings.embedding_model,
        },
        "providers": {
            "ollama": {
                "host": settings.ollama_host,
                "model": settings.ollama_model,
            },
            "foundry_local": {
                "endpoint": settings.foundry_endpoint,
                "model": settings.foundry_model,
                "auto_start": settings.foundry_auto_start,
            },
        },
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


# WebSocket endpoint for real-time chat (Phase 2.2)
@router.websocket("/ws/{conversation_id}")
async def agent_websocket(
    websocket: WebSocket,
    conversation_id: int,
):
    """
    WebSocket endpoint for real-time agent interactions.

    Receives messages and streams responses back to the client.

    Message format (client -> server):
    {
        "type": "message",
        "content": "user message",
        "mcp_servers": ["mssql"]  # optional
    }

    Response format (server -> client):
    - {"type": "chunk", "content": "partial response"}
    - {"type": "tool_call", "tool_name": "...", "tool_args": {...}}
    - {"type": "complete", "message": {...}}
    - {"type": "error", "error": "..."}
    - {"type": "ping"} (heartbeat)

    Optional provider configuration (client -> server):
    {
        "type": "message",
        "content": "user message",
        "provider": "ollama" or "foundry_local",  # optional
        "model": "model-name",  # optional
        "mcp_servers": ["mssql"]  # optional
    }
    """
    from src.api.deps import get_websocket_manager_optional

    ws_manager = get_websocket_manager_optional()

    # Use WebSocket manager if available
    if ws_manager:
        connection_id = f"agent-{conversation_id}-{id(websocket)}"
        connection = await ws_manager.connect(websocket, connection_id, conversation_id)
        logger.info(
            "websocket_connected", conversation_id=conversation_id, connection_id=connection_id
        )
    else:
        # Fallback to direct WebSocket if manager not available
        await websocket.accept()
        connection = None
        logger.info("websocket_connected", conversation_id=conversation_id)

    # Create agent for this session
    agent = None

    try:
        while True:
            # Receive message from client
            if connection:
                data = await connection.receive_json()
                if data is None:
                    break
            else:
                data = await websocket.receive_json()

            if data.get("type") == "message":
                content = data.get("content", "")
                mcp_server_ids = data.get("mcp_servers", ["mssql"])
                provider_type = data.get("provider")  # 'ollama' or 'foundry_local'
                model_name = data.get("model")

                # New settings for thinking and RAG
                thinking_enabled = data.get("thinking_enabled", False)
                rag_enabled = data.get("rag_enabled", False)
                rag_top_k = data.get("rag_top_k", 5)
                rag_hybrid_search = data.get("rag_hybrid_search", False)

                logger.info(
                    "websocket_message_received",
                    conversation_id=conversation_id,
                    content_length=len(content),
                    mcp_servers=mcp_server_ids,
                    provider=provider_type,
                    model=model_name,
                    thinking_enabled=thinking_enabled,
                    rag_enabled=rag_enabled,
                )

                # Initialize augmented content and RAG sources
                augmented_content = content
                rag_sources = []

                # RAG context augmentation if enabled
                if rag_enabled:
                    try:
                        vector_store = get_vector_store_optional()
                        if vector_store:
                            # Use hybrid search if enabled, otherwise semantic search
                            if rag_hybrid_search:
                                rag_alpha = data.get("rag_alpha", 0.5)
                                rag_results = await vector_store.hybrid_search(
                                    query=content,
                                    top_k=rag_top_k,
                                    alpha=rag_alpha,
                                )
                                search_mode = "hybrid"
                            else:
                                rag_results = await vector_store.search(
                                    query=content,
                                    top_k=rag_top_k,
                                )
                                search_mode = "semantic"

                            if rag_results:
                                context_parts = []
                                for result in rag_results:
                                    context_parts.append(result.get("content", ""))
                                    rag_sources.append(
                                        {
                                            "document_id": result.get("document_id"),
                                            "title": result.get("title", "Unknown"),
                                            "score": result.get("score", 0.0),
                                            "search_type": result.get("search_type", search_mode),
                                        }
                                    )
                                rag_context = "\n---\n".join(context_parts)
                                augmented_content = f"Based on the following context from relevant documents:\n\n{rag_context}\n\nUser question: {content}"
                                logger.info(
                                    "rag_context_added",
                                    sources_count=len(rag_sources),
                                    search_mode=search_mode,
                                )
                    except Exception as e:
                        logger.warning("rag_search_failed", error=str(e))

                # Thinking mode - switch to reasoning model if enabled
                effective_model = model_name
                if thinking_enabled and not model_name:
                    effective_model = "qwq:latest"
                    logger.info("thinking_mode_enabled", model=effective_model)

                # Create agent instance with optional provider/model configuration
                try:
                    agent = create_research_agent(
                        provider_type=provider_type,
                        model_name=effective_model,
                        thinking_mode=thinking_enabled,
                    )

                    # Send warning if model doesn't support tool calling
                    if agent.tool_warning:
                        warning_msg = {
                            "type": "warning",
                            "warning": agent.tool_warning,
                            "warning_type": "tool_calling_not_supported",
                        }
                        if connection:
                            await connection.send_json(warning_msg)
                        else:
                            await websocket.send_json(warning_msg)
                        logger.warning(
                            "agent_tool_warning_sent",
                            warning=agent.tool_warning,
                            provider=provider_type,
                            model=effective_model,
                        )

                except Exception as e:
                    logger.error("agent_creation_error", error=str(e))
                    error_msg = {
                        "type": "error",
                        "error": f"Failed to create agent: {str(e)}",
                    }
                    if connection:
                        await connection.send_json(error_msg)
                    else:
                        await websocket.send_json(error_msg)
                    continue

                # Stream response with MCP server connection
                # CRITICAL: async with agent establishes MCP server connections
                full_response = ""
                try:
                    async with agent:  # Establish MCP server connections
                        async for chunk in agent.chat_stream(augmented_content):
                            full_response += chunk
                            chunk_msg = {
                                "type": "chunk",
                                "content": chunk,
                            }
                            if connection:
                                await connection.send_json(chunk_msg)
                            else:
                                await websocket.send_json(chunk_msg)

                        # Get token usage after streaming
                        stats = agent.get_last_response_stats()
                        token_usage = stats.get("token_usage")

                        # Send completion message
                        complete_msg = {
                            "type": "complete",
                            "message": {
                                "id": 0,  # Would be set by database in full implementation
                                "conversation_id": conversation_id,
                                "role": "assistant",
                                "content": full_response,
                                "tool_calls": None,
                                "metadata": {"sources": rag_sources} if rag_sources else None,
                                "tokens_used": token_usage.total_tokens if token_usage else None,
                                "created_at": None,
                            },
                        }
                        if connection:
                            await connection.send_json(complete_msg)
                        else:
                            await websocket.send_json(complete_msg)

                        logger.info(
                            "websocket_response_sent",
                            conversation_id=conversation_id,
                            response_length=len(full_response),
                            tokens=token_usage.total_tokens if token_usage else 0,
                        )

                except ResearchAgentError as e:
                    logger.error("agent_chat_error", error=str(e))
                    error_msg = {
                        "type": "error",
                        "error": str(e),
                    }
                    if connection:
                        await connection.send_json(error_msg)
                    else:
                        await websocket.send_json(error_msg)

    except WebSocketDisconnect:
        logger.info("websocket_disconnected", conversation_id=conversation_id)
    except Exception as e:
        logger.error("websocket_error", error=str(e))
        with contextlib.suppress(Exception):
            error_msg = {
                "type": "error",
                "error": str(e),
            }
            if connection:
                await connection.send_json(error_msg)
            else:
                await websocket.send_json(error_msg)
    finally:
        # Disconnect from WebSocket manager if used
        if ws_manager and connection:
            await ws_manager.disconnect(connection.connection_id)


class PowerBIExportRequest(BaseModel):
    """Request model for Power BI export."""

    query: str
    table_name: str
    report_name: str | None = None


class PowerBIExportResponse(BaseModel):
    """Response model for Power BI export."""

    status: str
    file_path: str | None = None
    message: str | None = None


@router.post("/powerbi-export", response_model=PowerBIExportResponse)
async def export_to_powerbi(request: PowerBIExportRequest):
    """
    Export query results to Power BI PBIX file.

    This endpoint creates a PBIX file using the Power BI MCP server if available.
    """
    logger.info(
        "powerbi_export_request",
        table_name=request.table_name,
        report_name=request.report_name,
    )

    # Power BI MCP integration placeholder
    # In a full implementation, this would:
    # 1. Check if Power BI MCP server is configured
    # 2. Execute the query to get data
    # 3. Use MCP to create the PBIX file

    # For now, return informative message about the feature
    return PowerBIExportResponse(
        status="error",
        message="Power BI MCP server is not configured. Please add a Power BI MCP server "
        "to your mcp_config.json to enable this feature. Visit https://github.com/microsoft/powerbi-mcp "
        "for more information.",
    )
