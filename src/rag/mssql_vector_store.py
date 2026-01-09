"""
SQL Server 2025 Vector Store
Uses native VECTOR data type and VECTOR_DISTANCE for similarity search.

This module provides vector storage using SQL Server 2025's native vector
capabilities, eliminating the need for Redis for vector operations.
"""

import json
from typing import Any

import structlog
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.rag.embedder import OllamaEmbedder
from src.rag.vector_store_base import VectorStoreBase

logger = structlog.get_logger()


class MSSQLVectorStore(VectorStoreBase):
    """Vector store using SQL Server 2025 native VECTOR type."""

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        embedder: OllamaEmbedder,
        dimensions: int = 768,  # nomic-embed-text default
    ):
        """
        Initialize the SQL Server vector store.

        Args:
            session_factory: SQLAlchemy async session factory
            embedder: Ollama embedder for generating vectors
            dimensions: Embedding dimensions (default: 768 for nomic-embed-text)
        """
        super().__init__(embedder=embedder, dimensions=dimensions)
        self._session_factory = session_factory

    async def create_index(self, overwrite: bool = False) -> None:
        """
        Verify vector tables exist (created by init scripts).

        Args:
            overwrite: If True, recreate tables (not typically needed)
        """
        async with self._session_factory() as session:
            # Verify the vectors schema and tables exist
            result = await session.execute(
                text("""
                    SELECT COUNT(*) as cnt
                    FROM INFORMATION_SCHEMA.TABLES
                    WHERE TABLE_SCHEMA = 'vectors'
                    AND TABLE_NAME IN ('document_chunks', 'schema_embeddings')
                """)
            )
            row = result.fetchone()
            table_count = row[0] if row else 0

            if table_count >= 2:
                logger.info("mssql_vector_tables_verified", tables_found=table_count)
            else:
                logger.warning(
                    "mssql_vector_tables_missing",
                    expected=2,
                    found=table_count,
                )
                raise RuntimeError("Vector tables not found. Run init-backend scripts first.")

    def _embedding_to_json(self, embedding: list[float]) -> str:
        """Convert embedding list to JSON array string for SQL Server."""
        return json.dumps(embedding)

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
            document_id: Unique identifier for the document (must be int-compatible)
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

        # Generate embeddings in batch
        embeddings = await self.embedder.embed_batch(chunks)

        async with self._session_factory() as session:
            # Insert chunks with embeddings
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings, strict=True)):
                embedding_json = self._embedding_to_json(embedding)
                metadata_json = json.dumps(metadata or {})

                # Use DECLARE to properly convert JSON to VECTOR type
                await session.execute(
                    text("""
                        DECLARE @vec VECTOR(768) = :embedding;
                        INSERT INTO vectors.document_chunks
                        (document_id, chunk_index, content, source, source_type, metadata, embedding)
                        VALUES
                        (:doc_id, :chunk_idx, :content, :source, :source_type, :metadata, @vec)
                    """),
                    {
                        "doc_id": int(document_id),
                        "chunk_idx": i,
                        "content": chunk,
                        "source": source,
                        "source_type": source_type,
                        "metadata": metadata_json,
                        "embedding": embedding_json,
                    },
                )

            await session.commit()

        logger.info(
            "document_added",
            document_id=document_id,
            chunks_added=len(chunks),
        )

    async def search(
        self,
        query: str,
        top_k: int = 5,
        source_type: str | None = None,
        document_id: int | None = None,
    ) -> list[dict[str, Any]]:
        """
        Search for similar documents using cosine distance.

        Args:
            query: Search query text
            top_k: Number of results to return
            source_type: Filter by source type
            document_id: Filter by specific document

        Returns:
            List of matching documents with scores
        """
        # Generate query embedding
        query_embedding = await self.embedder.embed(query)
        embedding_json = self._embedding_to_json(query_embedding)

        async with self._session_factory() as session:
            # Use the stored procedure for optimized search
            # Note: We pass the JSON array string directly - SQL Server will convert it to VECTOR
            result = await session.execute(
                text("""
                    DECLARE @query_vec VECTOR(768) = :embedding;
                    EXEC vectors.SearchDocuments
                        @query_vector = @query_vec,
                        @top_n = :top_k,
                        @source_type = :source_type,
                        @document_id = :document_id
                """),
                {
                    "embedding": embedding_json,
                    "top_k": top_k,
                    "source_type": source_type,
                    "document_id": document_id,
                },
            )

            rows = result.fetchall()

        # Format results
        formatted = []
        for row in rows:
            metadata = {}
            if row.metadata:
                try:
                    metadata = json.loads(row.metadata)
                except (json.JSONDecodeError, TypeError):
                    pass

            formatted.append(
                {
                    "id": row.id,
                    "content": row.content,
                    "source": row.source,
                    "source_type": row.source_type,
                    "document_id": str(row.document_id),
                    "chunk_index": row.chunk_index,
                    "metadata": metadata,
                    "score": row.distance,  # Cosine distance (lower is better)
                }
            )

        return formatted

    async def hybrid_search(
        self,
        query: str,
        top_k: int = 5,
        source_type: str | None = None,
        document_id: int | None = None,
        alpha: float = 0.5,
    ) -> list[dict[str, Any]]:
        """
        Hybrid search combining semantic (vector) and keyword (full-text) search.

        Uses Reciprocal Rank Fusion (RRF) to combine rankings from both search types.

        Args:
            query: Search query text
            top_k: Number of results to return
            source_type: Filter by source type
            document_id: Filter by specific document
            alpha: Weight for semantic search (0.0 = keyword only, 1.0 = semantic only)

        Returns:
            List of matching documents with combined RRF scores
        """
        # Generate query embedding
        query_embedding = await self.embedder.embed(query)
        embedding_json = self._embedding_to_json(query_embedding)

        # Prepare search text for full-text search
        search_text = self._prepare_search_text(query)

        async with self._session_factory() as session:
            try:
                # Use the hybrid search stored procedure
                # Note: We declare the VECTOR variable first for proper type conversion
                result = await session.execute(
                    text("""
                        DECLARE @query_vec VECTOR(768) = :embedding;
                        EXEC vectors.HybridSearchDocuments
                            @query_vector = @query_vec,
                            @query_text = :search_text,
                            @top_n = :top_k,
                            @source_type = :source_type,
                            @document_id = :document_id,
                            @alpha = :alpha
                    """),
                    {
                        "embedding": embedding_json,
                        "search_text": search_text,
                        "top_k": top_k,
                        "source_type": source_type,
                        "document_id": document_id,
                        "alpha": alpha,
                    },
                )

                rows = result.fetchall()
            except Exception as e:
                # If hybrid search fails (e.g., full-text not set up), fall back to semantic
                logger.warning(
                    "hybrid_search_fallback",
                    error=str(e),
                    message="Falling back to semantic search",
                )
                return await self.search(query, top_k, source_type, document_id)

        # Format results
        formatted = []
        for row in rows:
            metadata = {}
            if row.metadata:
                try:
                    metadata = json.loads(row.metadata)
                except (json.JSONDecodeError, TypeError):
                    pass

            formatted.append(
                {
                    "id": row.id,
                    "content": row.content,
                    "source": row.source,
                    "source_type": row.source_type,
                    "document_id": str(row.document_id),
                    "chunk_index": row.chunk_index,
                    "metadata": metadata,
                    "score": row.rrf_score,  # RRF score (higher is better)
                    "distance": row.distance,  # Cosine distance from vector search
                    "search_type": row.search_type,
                }
            )

        return formatted

    def _prepare_search_text(self, query: str) -> str:
        """
        Prepare search text for SQL Server full-text search.

        Removes special characters and formats for CONTAINSTABLE.

        Args:
            query: Raw search query

        Returns:
            Prepared search text
        """
        # Remove characters that break full-text search
        special_chars = ['"', "'", "(", ")", "&", "|", "!", "~", "*"]
        result = query
        for char in special_chars:
            result = result.replace(char, " ")

        result = " ".join(result.split())  # Normalize whitespace

        if not result:
            return "*"

        # Wrap in quotes for phrase search if multiple words
        if " " in result:
            result = f'"{result}"'

        return result

    async def search_schema(
        self,
        query: str,
        top_k: int = 10,
        database_name: str | None = None,
        object_type: str | None = None,
    ) -> list[dict[str, Any]]:
        """
        Search schema embeddings for relevant database objects.

        Args:
            query: Search query text
            top_k: Number of results to return
            database_name: Filter by database
            object_type: Filter by object type ('table', 'column', etc.)

        Returns:
            List of matching schema objects with scores
        """
        # Generate query embedding
        query_embedding = await self.embedder.embed(query)
        embedding_json = self._embedding_to_json(query_embedding)

        async with self._session_factory() as session:
            # Use DECLARE to properly convert JSON to VECTOR type
            result = await session.execute(
                text("""
                    DECLARE @query_vec VECTOR(768) = :embedding;
                    EXEC vectors.SearchSchema
                        @query_vector = @query_vec,
                        @top_n = :top_k,
                        @database_name = :database_name,
                        @object_type = :object_type
                """),
                {
                    "embedding": embedding_json,
                    "top_k": top_k,
                    "database_name": database_name,
                    "object_type": object_type,
                },
            )

            rows = result.fetchall()

        # Format results
        formatted = []
        for row in rows:
            formatted.append(
                {
                    "id": row.id,
                    "object_type": row.object_type,
                    "object_name": row.object_name,
                    "database_name": row.database_name,
                    "schema_name": row.schema_name,
                    "description": row.description,
                    "score": row.distance,
                }
            )

        return formatted

    async def add_schema_embedding(
        self,
        object_type: str,
        object_name: str,
        description: str,
        database_name: str | None = None,
        schema_name: str | None = None,
    ) -> None:
        """
        Add or update a schema object embedding.

        Args:
            object_type: Type of object ('table', 'column', 'view', 'procedure')
            object_name: Full object name
            description: Human-readable description
            database_name: Source database name
            schema_name: Source schema name
        """
        # Generate embedding for the description
        embedding = await self.embedder.embed(description)
        embedding_json = self._embedding_to_json(embedding)

        async with self._session_factory() as session:
            # Upsert: delete existing and insert new
            await session.execute(
                text("""
                    DELETE FROM vectors.schema_embeddings
                    WHERE database_name = :database_name
                    AND schema_name = :schema_name
                    AND object_type = :object_type
                    AND object_name = :object_name
                """),
                {
                    "database_name": database_name,
                    "schema_name": schema_name,
                    "object_type": object_type,
                    "object_name": object_name,
                },
            )

            # Use DECLARE to properly convert JSON to VECTOR type
            await session.execute(
                text("""
                    DECLARE @vec VECTOR(768) = :embedding;
                    INSERT INTO vectors.schema_embeddings
                    (object_type, object_name, database_name, schema_name, description, embedding)
                    VALUES
                    (:object_type, :object_name, :database_name, :schema_name, :description, @vec)
                """),
                {
                    "object_type": object_type,
                    "object_name": object_name,
                    "database_name": database_name,
                    "schema_name": schema_name,
                    "description": description,
                    "embedding": embedding_json,
                },
            )

            await session.commit()

        logger.info(
            "schema_embedding_added",
            object_type=object_type,
            object_name=object_name,
        )

    async def delete_document(self, document_id: str) -> int:
        """
        Delete all chunks for a document.

        Args:
            document_id: Document ID to delete

        Returns:
            Number of chunks deleted
        """
        async with self._session_factory() as session:
            result = await session.execute(
                text("""
                    DELETE FROM vectors.document_chunks
                    WHERE document_id = :doc_id
                """),
                {"doc_id": int(document_id)},
            )
            await session.commit()

            deleted_count = result.rowcount
            logger.info(
                "document_deleted",
                document_id=document_id,
                chunks_deleted=deleted_count,
            )
            return deleted_count

    async def get_stats(self) -> dict[str, Any]:
        """
        Get vector store statistics.

        Returns:
            Dictionary with stats (document count, chunk count, etc.)
        """
        async with self._session_factory() as session:
            try:
                # Get chunk count
                chunk_result = await session.execute(
                    text("SELECT COUNT(*) as cnt FROM vectors.document_chunks")
                )
                chunk_row = chunk_result.fetchone()
                chunk_count = chunk_row[0] if chunk_row else 0

                # Get unique document count
                doc_result = await session.execute(
                    text("SELECT COUNT(DISTINCT document_id) as cnt FROM vectors.document_chunks")
                )
                doc_row = doc_result.fetchone()
                doc_count = doc_row[0] if doc_row else 0

                # Get schema embedding count
                schema_result = await session.execute(
                    text("SELECT COUNT(*) as cnt FROM vectors.schema_embeddings")
                )
                schema_row = schema_result.fetchone()
                schema_count = schema_row[0] if schema_row else 0

                return {
                    "store_type": "mssql",
                    "dimensions": self.dimensions,
                    "num_documents": doc_count,
                    "num_chunks": chunk_count,
                    "num_schema_embeddings": schema_count,
                }
            except Exception as e:
                logger.warning("stats_fetch_error", error=str(e))
                return {
                    "store_type": "mssql",
                    "error": str(e),
                }

    async def clear_all(self) -> dict[str, int]:
        """
        Clear all vector data (use with caution).

        Returns:
            Dictionary with counts of deleted items
        """
        async with self._session_factory() as session:
            # Delete all document chunks
            chunk_result = await session.execute(text("DELETE FROM vectors.document_chunks"))
            chunks_deleted = chunk_result.rowcount

            # Delete all schema embeddings
            schema_result = await session.execute(text("DELETE FROM vectors.schema_embeddings"))
            schemas_deleted = schema_result.rowcount

            await session.commit()

            logger.warning(
                "vector_store_cleared",
                chunks_deleted=chunks_deleted,
                schemas_deleted=schemas_deleted,
            )

            return {
                "chunks_deleted": chunks_deleted,
                "schemas_deleted": schemas_deleted,
            }
