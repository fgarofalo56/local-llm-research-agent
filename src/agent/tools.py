"""
RAG Tools for Pydantic AI Agent

Provides tools for knowledge base search, document retrieval, and RAG operations.
These tools integrate with the SQL Server 2025 vector store for hybrid search.
"""

from typing import Any

import structlog
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.rag.embedder import OllamaEmbedder
from src.rag.mssql_vector_store import MSSQLVectorStore

logger = structlog.get_logger()


# =============================================================================
# Response Models
# =============================================================================


class SearchResult(BaseModel):
    """A single search result from the knowledge base."""

    document_id: str = Field(description="Unique document identifier")
    chunk_id: int = Field(description="Chunk index within document")
    content: str = Field(description="Text content of the chunk")
    source: str = Field(description="Source filename or identifier")
    source_type: str = Field(description="Type: document, schema, web")
    relevance_score: float = Field(description="Combined relevance score (0-1)")
    vector_score: float = Field(description="Vector similarity score")
    text_score: float = Field(description="Text match score")
    metadata: dict[str, Any] = Field(default_factory=dict)


class KnowledgeSource(BaseModel):
    """A knowledge source/collection in the system."""

    name: str = Field(description="Source name")
    document_count: int = Field(description="Number of documents")
    chunk_count: int = Field(description="Total chunks indexed")
    source_type: str = Field(description="Type: document, schema, web")
    last_updated: str | None = Field(default=None, description="Last update timestamp")


class DocumentContent(BaseModel):
    """Full document content with metadata."""

    document_id: str = Field(description="Document identifier")
    source: str = Field(description="Source filename")
    source_type: str = Field(description="Type: document, schema, web")
    full_content: str = Field(description="Full document text")
    chunks: list[str] = Field(description="Individual text chunks")
    metadata: dict[str, Any] = Field(default_factory=dict)
    word_count: int = Field(description="Total word count")


# =============================================================================
# RAG Tool Functions
# =============================================================================


class RAGTools:
    """
    RAG tools for Pydantic AI agent integration.

    Provides:
    - search_knowledge_base: Hybrid vector + keyword search
    - list_knowledge_sources: Show available document collections
    - get_document_content: Retrieve full document by ID
    """

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        embedder: OllamaEmbedder | None = None,
        vector_weight: float = 0.7,
        text_weight: float = 0.3,
    ):
        """
        Initialize RAG tools.

        Args:
            session_factory: SQLAlchemy async session factory for LLM_BackEnd
            embedder: Ollama embedder (created if not provided)
            vector_weight: Weight for vector similarity (default 0.7)
            text_weight: Weight for text match (default 0.3)
        """
        self._session_factory = session_factory
        self._embedder = embedder or OllamaEmbedder()
        self._vector_weight = vector_weight
        self._text_weight = text_weight
        self._vector_store: MSSQLVectorStore | None = None

    async def _get_vector_store(self) -> MSSQLVectorStore:
        """Get or create the vector store instance."""
        if self._vector_store is None:
            self._vector_store = MSSQLVectorStore(
                session_factory=self._session_factory,
                embedder=self._embedder,
            )
        return self._vector_store

    async def search_knowledge_base(
        self,
        query: str,
        top_k: int = 5,
        source_filter: str | None = None,
        min_score: float = 0.3,
    ) -> list[SearchResult]:
        """
        Search the knowledge base using hybrid vector + keyword search.

        Combines semantic similarity (vector search) with keyword matching
        for more accurate and relevant results.

        Args:
            query: Natural language search query
            top_k: Maximum number of results to return (default 5)
            source_filter: Optional filter by source name
            min_score: Minimum relevance score threshold (default 0.3)

        Returns:
            List of SearchResult objects with relevance scores
        """
        logger.info(
            "rag_search_started",
            query=query[:100],
            top_k=top_k,
            source_filter=source_filter,
        )

        try:
            # Generate query embedding
            query_embedding = await self._embedder.embed(query)
            embedding_json = f"[{','.join(str(x) for x in query_embedding)}]"

            async with self._session_factory() as session:
                # Hybrid search query combining vector and text search
                sql = text("""
                    WITH VectorSearch AS (
                        SELECT
                            dc.document_id,
                            dc.chunk_index,
                            dc.chunk_text,
                            dc.source,
                            dc.source_type,
                            dc.metadata,
                            1.0 - VECTOR_DISTANCE('cosine', dc.embedding, CAST(:query_vector AS VECTOR(768))) AS vector_score
                        FROM vectors.document_chunks dc
                        WHERE dc.embedding IS NOT NULL
                        {source_filter}
                    ),
                    TextSearch AS (
                        SELECT
                            dc.document_id,
                            dc.chunk_index,
                            CASE
                                WHEN dc.chunk_text LIKE '%' + :query_text + '%' THEN 0.5
                                WHEN dc.chunk_text LIKE '%' + :first_word + '%' THEN 0.3
                                ELSE 0.0
                            END AS text_score
                        FROM vectors.document_chunks dc
                        {source_filter_text}
                    )
                    SELECT
                        v.document_id,
                        v.chunk_index,
                        v.chunk_text,
                        v.source,
                        v.source_type,
                        v.metadata,
                        v.vector_score,
                        ISNULL(t.text_score, 0.0) AS text_score,
                        (v.vector_score * :vector_weight + ISNULL(t.text_score, 0.0) * :text_weight) AS combined_score
                    FROM VectorSearch v
                    LEFT JOIN TextSearch t ON v.document_id = t.document_id AND v.chunk_index = t.chunk_index
                    WHERE v.vector_score >= :min_vector_score
                    ORDER BY combined_score DESC
                    OFFSET 0 ROWS FETCH NEXT :top_k ROWS ONLY
                """.format(
                    source_filter=f"AND dc.source = :source_name" if source_filter else "",
                    source_filter_text=f"WHERE dc.source = :source_name" if source_filter else "",
                ))

                params = {
                    "query_vector": embedding_json,
                    "query_text": query,
                    "first_word": query.split()[0] if query else "",
                    "vector_weight": self._vector_weight,
                    "text_weight": self._text_weight,
                    "min_vector_score": max(0.1, min_score - 0.2),  # Lower threshold for initial filter
                    "top_k": top_k,
                }
                if source_filter:
                    params["source_name"] = source_filter

                result = await session.execute(sql, params)
                rows = result.fetchall()

            results = []
            for row in rows:
                combined_score = float(row.combined_score)
                if combined_score >= min_score:
                    results.append(
                        SearchResult(
                            document_id=str(row.document_id),
                            chunk_id=row.chunk_index,
                            content=row.chunk_text,
                            source=row.source,
                            source_type=row.source_type or "document",
                            relevance_score=round(combined_score, 4),
                            vector_score=round(float(row.vector_score), 4),
                            text_score=round(float(row.text_score), 4),
                            metadata=row.metadata if row.metadata else {},
                        )
                    )

            logger.info(
                "rag_search_completed",
                query=query[:50],
                results_found=len(results),
            )

            return results

        except Exception as e:
            logger.error("rag_search_error", error=str(e), query=query[:50])
            raise

    async def list_knowledge_sources(self) -> list[KnowledgeSource]:
        """
        List all available knowledge sources/collections.

        Returns:
            List of KnowledgeSource objects with document counts
        """
        logger.info("listing_knowledge_sources")

        try:
            async with self._session_factory() as session:
                # Query for source statistics
                sql = text("""
                    SELECT
                        source,
                        source_type,
                        COUNT(DISTINCT document_id) AS document_count,
                        COUNT(*) AS chunk_count,
                        MAX(created_at) AS last_updated
                    FROM vectors.document_chunks
                    GROUP BY source, source_type
                    ORDER BY source
                """)

                result = await session.execute(sql)
                rows = result.fetchall()

            sources = [
                KnowledgeSource(
                    name=row.source,
                    document_count=row.document_count,
                    chunk_count=row.chunk_count,
                    source_type=row.source_type or "document",
                    last_updated=str(row.last_updated) if row.last_updated else None,
                )
                for row in rows
            ]

            logger.info("knowledge_sources_listed", count=len(sources))
            return sources

        except Exception as e:
            logger.error("list_sources_error", error=str(e))
            raise

    async def get_document_content(self, document_id: str) -> DocumentContent | None:
        """
        Retrieve full document content by ID.

        Args:
            document_id: Document identifier

        Returns:
            DocumentContent with all chunks and metadata, or None if not found
        """
        logger.info("retrieving_document", document_id=document_id)

        try:
            async with self._session_factory() as session:
                # Get all chunks for the document
                sql = text("""
                    SELECT
                        document_id,
                        chunk_index,
                        chunk_text,
                        source,
                        source_type,
                        metadata
                    FROM vectors.document_chunks
                    WHERE document_id = :doc_id
                    ORDER BY chunk_index
                """)

                result = await session.execute(sql, {"doc_id": int(document_id)})
                rows = result.fetchall()

            if not rows:
                logger.warning("document_not_found", document_id=document_id)
                return None

            # Reconstruct document from chunks
            chunks = [row.chunk_text for row in rows]
            full_content = "\n\n".join(chunks)
            first_row = rows[0]

            doc = DocumentContent(
                document_id=document_id,
                source=first_row.source,
                source_type=first_row.source_type or "document",
                full_content=full_content,
                chunks=chunks,
                metadata=first_row.metadata if first_row.metadata else {},
                word_count=len(full_content.split()),
            )

            logger.info(
                "document_retrieved",
                document_id=document_id,
                chunks=len(chunks),
                words=doc.word_count,
            )

            return doc

        except Exception as e:
            logger.error("get_document_error", error=str(e), document_id=document_id)
            raise

    async def search_by_keywords(
        self,
        keywords: list[str],
        top_k: int = 5,
        match_all: bool = False,
    ) -> list[SearchResult]:
        """
        Search using keyword matching only (no vector similarity).

        Args:
            keywords: List of keywords to search for
            top_k: Maximum results to return
            match_all: If True, require all keywords to match

        Returns:
            List of SearchResult objects
        """
        logger.info("keyword_search", keywords=keywords, match_all=match_all)

        try:
            async with self._session_factory() as session:
                # Build keyword conditions
                if match_all:
                    where_clause = " AND ".join(
                        f"chunk_text LIKE '%' + :kw{i} + '%'"
                        for i in range(len(keywords))
                    )
                else:
                    where_clause = " OR ".join(
                        f"chunk_text LIKE '%' + :kw{i} + '%'"
                        for i in range(len(keywords))
                    )

                sql = text(f"""
                    SELECT
                        document_id,
                        chunk_index,
                        chunk_text,
                        source,
                        source_type,
                        metadata
                    FROM vectors.document_chunks
                    WHERE {where_clause}
                    ORDER BY document_id, chunk_index
                    OFFSET 0 ROWS FETCH NEXT :top_k ROWS ONLY
                """)

                params = {"top_k": top_k}
                for i, kw in enumerate(keywords):
                    params[f"kw{i}"] = kw

                result = await session.execute(sql, params)
                rows = result.fetchall()

            results = [
                SearchResult(
                    document_id=str(row.document_id),
                    chunk_id=row.chunk_index,
                    content=row.chunk_text,
                    source=row.source,
                    source_type=row.source_type or "document",
                    relevance_score=0.5,  # Keyword match score
                    vector_score=0.0,
                    text_score=0.5,
                    metadata=row.metadata if row.metadata else {},
                )
                for row in rows
            ]

            logger.info("keyword_search_completed", results=len(results))
            return results

        except Exception as e:
            logger.error("keyword_search_error", error=str(e))
            raise


# =============================================================================
# Factory Function
# =============================================================================


def create_rag_tools(
    session_factory: async_sessionmaker[AsyncSession],
    embedder: OllamaEmbedder | None = None,
) -> RAGTools:
    """
    Create RAG tools instance for agent integration.

    Args:
        session_factory: SQLAlchemy session factory for LLM_BackEnd database
        embedder: Optional pre-configured embedder

    Returns:
        RAGTools instance
    """
    return RAGTools(
        session_factory=session_factory,
        embedder=embedder,
    )


# =============================================================================
# Pydantic AI Tool Decorators (for direct agent integration)
# =============================================================================


# These will be used when integrating with the agent's toolsets
# The actual tool registration happens in the agent module

__all__ = [
    "RAGTools",
    "SearchResult",
    "KnowledgeSource",
    "DocumentContent",
    "create_rag_tools",
]
