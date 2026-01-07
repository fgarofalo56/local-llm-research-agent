"""
Redis Vector Store
Phase 2.1: Backend Infrastructure & RAG Pipeline

Vector store using Redis Stack with vector similarity search.
"""

import hashlib
import json
from typing import Any

import numpy as np
import structlog
from redis.asyncio import Redis
from redisvl.index import AsyncSearchIndex
from redisvl.query import VectorQuery
from redisvl.schema import IndexSchema

from src.rag.embedder import OllamaEmbedder
from src.rag.vector_store_base import VectorStoreBase

logger = structlog.get_logger()


class RedisVectorStore(VectorStoreBase):
    """Vector store using Redis Stack."""

    INDEX_NAME = "documents"
    PREFIX = "doc"

    def __init__(
        self,
        redis_client: Redis,
        embedder: OllamaEmbedder,
        dimensions: int = 768,  # nomic-embed-text default
    ):
        """
        Initialize the Redis vector store.

        Args:
            redis_client: Async Redis client
            embedder: Ollama embedder for generating vectors
            dimensions: Embedding dimensions (default: 768 for nomic-embed-text)
        """
        super().__init__(embedder=embedder, dimensions=dimensions)
        self.redis = redis_client
        self._index: AsyncSearchIndex | None = None

    def _get_schema(self) -> dict:
        """Get the Redis index schema."""
        return {
            "index": {
                "name": self.INDEX_NAME,
                "prefix": self.PREFIX,
            },
            "fields": [
                {"name": "content", "type": "text"},
                {"name": "source", "type": "tag"},
                {"name": "source_type", "type": "tag"},  # 'document', 'schema'
                {"name": "document_id", "type": "tag"},
                {"name": "chunk_index", "type": "numeric"},
                {"name": "metadata", "type": "text"},
                {
                    "name": "embedding",
                    "type": "vector",
                    "attrs": {
                        "dims": self.dimensions,
                        "algorithm": "hnsw",
                        "datatype": "float32",
                        "distance_metric": "cosine",
                    },
                },
            ],
        }

    async def create_index(self, overwrite: bool = False) -> None:
        """
        Create the vector index.

        Args:
            overwrite: If True, drop existing index and recreate
        """
        schema = IndexSchema.from_dict(self._get_schema())
        self._index = AsyncSearchIndex(schema, redis_client=self.redis)

        try:
            await self._index.create(overwrite=overwrite)
            logger.info("vector_index_created", index_name=self.INDEX_NAME)
        except Exception as e:
            if "Index already exists" in str(e):
                logger.info("vector_index_exists", index_name=self.INDEX_NAME)
            else:
                raise

    def _generate_id(self, document_id: str, chunk_index: int) -> str:
        """Generate unique ID for a chunk."""
        return hashlib.md5(f"{document_id}:{chunk_index}".encode()).hexdigest()

    async def add_document(
        self,
        document_id: str,
        chunks: list[str],
        source: str,
        source_type: str = "document",
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """
        Add document chunks to the vector store.

        Args:
            document_id: Unique identifier for the document
            chunks: List of text chunks
            source: Source name (e.g., filename)
            source_type: Type of source ('document', 'schema')
            metadata: Optional metadata dictionary
        """
        logger.info(
            "adding_document",
            document_id=document_id,
            chunk_count=len(chunks),
        )

        # Generate embeddings
        embeddings = await self.embedder.embed_batch(chunks)

        # Prepare records
        records = []
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings, strict=True)):
            # Convert embedding list to numpy array bytes for Redis
            embedding_bytes = np.array(embedding, dtype=np.float32).tobytes()
            record = {
                "id": self._generate_id(document_id, i),
                "content": chunk,
                "source": source,
                "source_type": source_type,
                "document_id": document_id,
                "chunk_index": i,
                "metadata": json.dumps(metadata or {}),
                "embedding": embedding_bytes,
            }
            records.append(record)

        # Load into index
        await self._index.load(records)
        logger.info(
            "document_added",
            document_id=document_id,
            chunks_added=len(records),
        )

    async def search(
        self,
        query: str,
        top_k: int = 5,
        source_type: str | None = None,
    ) -> list[dict[str, Any]]:
        """
        Search for similar documents.

        Args:
            query: Search query text
            top_k: Number of results to return
            source_type: Filter by source type

        Returns:
            List of matching documents with scores
        """
        # Generate query embedding and convert to bytes
        query_embedding = await self.embedder.embed(query)
        query_bytes = np.array(query_embedding, dtype=np.float32).tobytes()

        # Build filter
        filter_expr = None
        if source_type:
            filter_expr = f"@source_type:{{{source_type}}}"

        # Create query
        vector_query = VectorQuery(
            vector=query_bytes,
            vector_field_name="embedding",
            return_fields=[
                "content",
                "source",
                "source_type",
                "document_id",
                "chunk_index",
                "metadata",
            ],
            num_results=top_k,
            filter_expression=filter_expr,
        )

        # Execute search
        results = await self._index.query(vector_query)

        # Format results
        formatted = []
        for result in results:
            formatted.append(
                {
                    "content": result.get("content"),
                    "source": result.get("source"),
                    "source_type": result.get("source_type"),
                    "document_id": result.get("document_id"),
                    "chunk_index": int(result.get("chunk_index", 0)),
                    "metadata": json.loads(result.get("metadata", "{}")),
                    "score": result.get("vector_distance", 0),
                }
            )

        return formatted

    async def hybrid_search(
        self,
        query: str,
        top_k: int = 5,
        source_type: str | None = None,
        alpha: float = 0.5,
    ) -> list[dict[str, Any]]:
        """
        Hybrid search combining semantic (vector) and keyword (full-text) search.

        Uses Reciprocal Rank Fusion (RRF) to combine rankings from both search types.

        Args:
            query: Search query text
            top_k: Number of results to return
            source_type: Filter by source type
            alpha: Weight for semantic search (0.0 = keyword only, 1.0 = semantic only)

        Returns:
            List of matching documents with combined RRF scores
        """
        # RRF constant
        rrf_k = 60

        # If alpha is 1.0, use pure semantic search
        if alpha >= 1.0:
            results = await self.search(query, top_k, source_type)
            for r in results:
                r["search_type"] = "semantic"
            return results

        # Generate query embedding
        query_embedding = await self.embedder.embed(query)
        query_bytes = np.array(query_embedding, dtype=np.float32).tobytes()

        # Get more results than needed for RRF fusion
        fetch_count = top_k * 3

        # Build filter for source type
        filter_expr = None
        if source_type:
            filter_expr = f"@source_type:{{{source_type}}}"

        # --- Vector Search ---
        vector_query = VectorQuery(
            vector=query_bytes,
            vector_field_name="embedding",
            return_fields=[
                "content",
                "source",
                "source_type",
                "document_id",
                "chunk_index",
                "metadata",
            ],
            num_results=fetch_count,
            filter_expression=filter_expr,
        )

        vector_results = await self._index.query(vector_query)

        # Assign vector ranks (lower distance = better = rank 1)
        vector_ranks = {}
        for rank, result in enumerate(vector_results, 1):
            doc_id = result.get("id", f"{result.get('document_id')}:{result.get('chunk_index')}")
            vector_ranks[doc_id] = {
                "rank": rank,
                "data": result,
                "distance": result.get("vector_distance", 0),
            }

        # --- Full-Text Search ---
        keyword_ranks = {}
        if alpha < 1.0:
            try:
                # Escape special characters for RediSearch
                escaped_query = self._escape_search_query(query)

                # Build full-text search query
                from redis.commands.search.query import Query

                ft_query_str = f"@content:{escaped_query}"
                if source_type:
                    ft_query_str = f"@source_type:{{{source_type}}} {ft_query_str}"

                ft_query = (
                    Query(ft_query_str)
                    .return_fields("content", "source", "source_type", "document_id", "chunk_index", "metadata")
                    .paging(0, fetch_count)
                )

                ft_results = await self.redis.ft(self.INDEX_NAME).search(ft_query)

                for rank, doc in enumerate(ft_results.docs, 1):
                    doc_id = doc.id.replace(f"{self.PREFIX}:", "")
                    keyword_ranks[doc_id] = {
                        "rank": rank,
                        "data": {
                            "content": getattr(doc, "content", ""),
                            "source": getattr(doc, "source", ""),
                            "source_type": getattr(doc, "source_type", ""),
                            "document_id": getattr(doc, "document_id", ""),
                            "chunk_index": getattr(doc, "chunk_index", "0"),
                            "metadata": getattr(doc, "metadata", "{}"),
                        },
                    }
            except Exception as e:
                logger.warning(
                    "redis_fulltext_search_failed",
                    error=str(e),
                    message="Falling back to vector-only search",
                )
                # If full-text fails, use pure semantic
                results = await self.search(query, top_k, source_type)
                for r in results:
                    r["search_type"] = "semantic"
                return results

        # --- RRF Fusion ---
        all_doc_ids = set(vector_ranks.keys()) | set(keyword_ranks.keys())

        combined_scores = []
        for doc_id in all_doc_ids:
            vector_score = 0.0
            keyword_score = 0.0
            data = None

            if doc_id in vector_ranks:
                vector_score = 1.0 / (rrf_k + vector_ranks[doc_id]["rank"])
                data = vector_ranks[doc_id]["data"]

            if doc_id in keyword_ranks:
                keyword_score = 1.0 / (rrf_k + keyword_ranks[doc_id]["rank"])
                if data is None:
                    data = keyword_ranks[doc_id]["data"]

            rrf_score = alpha * vector_score + (1 - alpha) * keyword_score

            combined_scores.append({
                "doc_id": doc_id,
                "rrf_score": rrf_score,
                "data": data,
                "distance": vector_ranks.get(doc_id, {}).get("distance", 0),
            })

        # Sort by RRF score (higher is better)
        combined_scores.sort(key=lambda x: x["rrf_score"], reverse=True)

        # Format top results
        formatted = []
        for item in combined_scores[:top_k]:
            data = item["data"]
            metadata = {}
            try:
                metadata = json.loads(data.get("metadata", "{}"))
            except (json.JSONDecodeError, TypeError):
                pass

            formatted.append({
                "content": data.get("content"),
                "source": data.get("source"),
                "source_type": data.get("source_type"),
                "document_id": data.get("document_id"),
                "chunk_index": int(data.get("chunk_index", 0)),
                "metadata": metadata,
                "score": item["rrf_score"],
                "distance": item["distance"],
                "search_type": "hybrid",
            })

        return formatted

    def _escape_search_query(self, query: str) -> str:
        """
        Escape special characters for RediSearch full-text query.

        Args:
            query: Raw search query

        Returns:
            Escaped query safe for RediSearch
        """
        # Characters that need escaping in RediSearch
        special_chars = ['@', '!', '{', '}', '(', ')', '|', '-', '=', '>', '[', ']', '"', "'", '~', '*', ':', '\\', '/']
        result = query
        for char in special_chars:
            result = result.replace(char, f'\\{char}')

        # Handle empty query
        result = result.strip()
        if not result:
            result = '*'

        return result

    async def delete_document(self, document_id: str) -> int:
        """
        Delete all chunks for a document.

        Args:
            document_id: Document ID to delete

        Returns:
            Number of chunks deleted
        """
        # Find all keys for this document
        pattern = f"{self.PREFIX}:*"
        keys_to_delete = []

        async for key in self.redis.scan_iter(pattern):
            # Check if this key belongs to the document
            data = await self.redis.hgetall(key)
            if data.get("document_id") == document_id:
                keys_to_delete.append(key)

        if keys_to_delete:
            await self.redis.delete(*keys_to_delete)
            logger.info(
                "document_deleted",
                document_id=document_id,
                chunks_deleted=len(keys_to_delete),
            )

        return len(keys_to_delete)

    async def get_stats(self) -> dict[str, Any]:
        """
        Get vector store statistics.

        Returns:
            Dictionary with stats (document count, chunk count, etc.)
        """
        try:
            info = await self._index.info()
            return {
                "index_name": self.INDEX_NAME,
                "num_docs": info.get("num_docs", 0),
                "num_records": info.get("num_records", 0),
                "indexing": info.get("indexing", False),
            }
        except Exception as e:
            logger.warning("stats_fetch_error", error=str(e))
            return {
                "index_name": self.INDEX_NAME,
                "error": str(e),
            }
