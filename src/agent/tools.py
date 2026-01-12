"""
Agent Tools for Pydantic AI Agent

Provides tools for:
- RAG: Knowledge base search, document retrieval, and RAG operations
- Web Search: Built-in web search for current events and fact-checking

These tools integrate with the SQL Server 2025 vector store for hybrid search
and external web search APIs for real-time information.
"""

import asyncio
from datetime import datetime
from typing import Any

import httpx
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
# Web Search Response Models
# =============================================================================


class WebSearchResult(BaseModel):
    """A single web search result."""

    title: str = Field(description="Page title")
    url: str = Field(description="URL of the result")
    snippet: str = Field(description="Text snippet/description")
    source: str = Field(description="Search engine source (duckduckgo, brave)")
    published_date: str | None = Field(default=None, description="Publication date if available")


class WebSearchResponse(BaseModel):
    """Web search response with results and metadata."""

    query: str = Field(description="Original search query")
    results: list[WebSearchResult] = Field(description="Search results")
    total_results: int = Field(description="Number of results returned")
    search_engine: str = Field(description="Search engine used")
    searched_at: str = Field(description="Timestamp of search")


# =============================================================================
# Web Search Tools
# =============================================================================


class WebSearchTools:
    """
    Web search tools for the Pydantic AI agent.

    Provides:
    - search_web: Search the web using DuckDuckGo (free, no API key needed)
    - The Brave Search MCP server can be used for more comprehensive results

    Rate limited to 10 requests per minute to avoid abuse.
    """

    def __init__(
        self,
        max_requests_per_minute: int = 10,
        timeout_seconds: int = 30,
    ):
        """
        Initialize web search tools.

        Args:
            max_requests_per_minute: Rate limit for searches
            timeout_seconds: Request timeout in seconds
        """
        self._max_rpm = max_requests_per_minute
        self._timeout = timeout_seconds
        self._request_times: list[datetime] = []
        self._lock = asyncio.Lock()

    async def _check_rate_limit(self) -> bool:
        """Check if we're within rate limits."""
        async with self._lock:
            now = datetime.now()
            # Remove requests older than 1 minute
            self._request_times = [t for t in self._request_times if (now - t).total_seconds() < 60]
            if len(self._request_times) >= self._max_rpm:
                return False
            self._request_times.append(now)
            return True

    async def search_web(
        self,
        query: str,
        max_results: int = 5,
    ) -> WebSearchResponse:
        """
        Search the web for information using DuckDuckGo.

        Use this tool for:
        - Current events and recent news
        - Fact-checking and verification
        - Finding up-to-date information
        - Researching topics not in the knowledge base

        Args:
            query: Search query (be specific for better results)
            max_results: Maximum number of results to return (default 5)

        Returns:
            WebSearchResponse with search results

        Note:
            This uses DuckDuckGo's HTML interface which doesn't require an API key.
            For more comprehensive results, enable the Brave Search MCP server.
        """
        logger.info("web_search_started", query=query[:100], max_results=max_results)

        # Check rate limit
        if not await self._check_rate_limit():
            logger.warning("web_search_rate_limited", query=query[:50])
            return WebSearchResponse(
                query=query,
                results=[],
                total_results=0,
                search_engine="rate_limited",
                searched_at=datetime.now().isoformat(),
            )

        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                # Use DuckDuckGo's HTML search (no API key needed)
                # This is a simple implementation - production should use proper API
                params = {
                    "q": query,
                    "kl": "us-en",  # US English results
                }
                headers = {"User-Agent": "Mozilla/5.0 (compatible; ResearchAgent/1.0)"}

                response = await client.get(
                    "https://html.duckduckgo.com/html/",
                    params=params,
                    headers=headers,
                )
                response.raise_for_status()

                # Parse results from HTML (simple extraction)
                results = self._parse_duckduckgo_html(response.text, max_results)

            search_response = WebSearchResponse(
                query=query,
                results=results,
                total_results=len(results),
                search_engine="duckduckgo",
                searched_at=datetime.now().isoformat(),
            )

            logger.info(
                "web_search_completed",
                query=query[:50],
                results=len(results),
            )

            return search_response

        except httpx.TimeoutException:
            logger.error("web_search_timeout", query=query[:50])
            return WebSearchResponse(
                query=query,
                results=[],
                total_results=0,
                search_engine="timeout",
                searched_at=datetime.now().isoformat(),
            )
        except Exception as e:
            logger.error("web_search_error", error=str(e), query=query[:50])
            return WebSearchResponse(
                query=query,
                results=[],
                total_results=0,
                search_engine="error",
                searched_at=datetime.now().isoformat(),
            )

    def _parse_duckduckgo_html(self, html: str, max_results: int) -> list[WebSearchResult]:
        """
        Parse DuckDuckGo HTML search results.

        This is a simple parser - for production use, consider using
        a proper HTML parser like BeautifulSoup.
        """
        import re

        results = []

        # Simple regex pattern to extract results
        # DuckDuckGo HTML format: <a class="result__a" href="...">title</a>
        # followed by <a class="result__snippet">snippet</a>
        result_pattern = re.compile(
            r'<a[^>]*class="result__a"[^>]*href="([^"]+)"[^>]*>([^<]+)</a>.*?'
            r'<a[^>]*class="result__snippet"[^>]*>([^<]+)</a>',
            re.DOTALL | re.IGNORECASE,
        )

        matches = result_pattern.findall(html)

        for url, title, snippet in matches[:max_results]:
            # Clean up the extracted text
            title = re.sub(r"<[^>]+>", "", title).strip()
            snippet = re.sub(r"<[^>]+>", "", snippet).strip()

            # Skip if no meaningful content
            if not title or not url:
                continue

            results.append(
                WebSearchResult(
                    title=title,
                    url=url,
                    snippet=snippet,
                    source="duckduckgo",
                    published_date=None,
                )
            )

        # If regex didn't work, try alternative pattern
        if not results:
            # Alternative: Look for result__url and result__title
            alt_pattern = re.compile(
                r'<a[^>]*class="[^"]*result__url[^"]*"[^>]*href="([^"]+)"[^>]*>.*?</a>.*?'
                r'<a[^>]*class="[^"]*result__title[^"]*"[^>]*>([^<]+)</a>',
                re.DOTALL | re.IGNORECASE,
            )
            alt_matches = alt_pattern.findall(html)
            for url, title in alt_matches[:max_results]:
                title = re.sub(r"<[^>]+>", "", title).strip()
                if title and url:
                    results.append(
                        WebSearchResult(
                            title=title,
                            url=url,
                            snippet="",
                            source="duckduckgo",
                            published_date=None,
                        )
                    )

        return results


def create_web_search_tools(
    max_requests_per_minute: int = 10,
    timeout_seconds: int = 30,
) -> WebSearchTools:
    """
    Create web search tools instance.

    Args:
        max_requests_per_minute: Rate limit (default 10)
        timeout_seconds: Request timeout (default 30)

    Returns:
        WebSearchTools instance
    """
    return WebSearchTools(
        max_requests_per_minute=max_requests_per_minute,
        timeout_seconds=timeout_seconds,
    )


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
                # Build query conditionally to avoid string formatting security warnings
                vector_filter = "AND dc.source = :source_name" if source_filter else ""
                text_filter = "WHERE dc.source = :source_name" if source_filter else ""

                base_query = """
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
                        """
                base_query += vector_filter
                base_query += """
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
                        """
                base_query += text_filter
                base_query += """
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
                """
                sql = text(base_query)

                params = {
                    "query_vector": embedding_json,
                    "query_text": query,
                    "first_word": query.split()[0] if query else "",
                    "vector_weight": self._vector_weight,
                    "text_weight": self._text_weight,
                    "min_vector_score": max(
                        0.1, min_score - 0.2
                    ),  # Lower threshold for initial filter
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
                # Build keyword conditions using parameterized placeholders
                # Each keyword gets a named parameter :kw0, :kw1, etc.
                keyword_conditions = []
                for i in range(len(keywords)):
                    keyword_conditions.append("chunk_text LIKE '%' + :kw" + str(i) + " + '%'")

                conjunction = " AND " if match_all else " OR "
                where_clause = conjunction.join(keyword_conditions)

                # Build query using string concatenation to avoid f-string security warnings
                base_query = """
                    SELECT
                        document_id,
                        chunk_index,
                        chunk_text,
                        source,
                        source_type,
                        metadata
                    FROM vectors.document_chunks
                    WHERE """
                base_query += where_clause
                base_query += """
                    ORDER BY document_id, chunk_index
                    OFFSET 0 ROWS FETCH NEXT :top_k ROWS ONLY
                """
                sql = text(base_query)

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
    # RAG tools
    "RAGTools",
    "SearchResult",
    "KnowledgeSource",
    "DocumentContent",
    "create_rag_tools",
    # Web search tools
    "WebSearchTools",
    "WebSearchResult",
    "WebSearchResponse",
    "create_web_search_tools",
]
