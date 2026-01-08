"""
Vector Store Abstract Base Class

Defines the common interface for all vector store implementations.
Ensures type safety and consistent behavior across MSSQL and Redis stores.
"""

from abc import ABC, abstractmethod
from typing import Any, Protocol

import structlog

logger = structlog.get_logger()


class VectorStoreProtocol(Protocol):
    """Protocol defining the vector store interface for type checking."""

    async def create_index(self, overwrite: bool = False) -> None:
        """Create the vector index."""
        ...

    async def add_document(
        self,
        document_id: str,
        chunks: list[str],
        source: str,
        source_type: str = "document",
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Add document chunks to the vector store."""
        ...

    async def search(
        self,
        query: str,
        top_k: int = 5,
        source_type: str | None = None,
    ) -> list[dict[str, Any]]:
        """Search for similar documents."""
        ...

    async def hybrid_search(
        self,
        query: str,
        top_k: int = 5,
        source_type: str | None = None,
        alpha: float = 0.5,
    ) -> list[dict[str, Any]]:
        """Hybrid search combining semantic and keyword search."""
        ...

    async def delete_document(self, document_id: str) -> int:
        """Delete all chunks for a document."""
        ...

    async def get_stats(self) -> dict[str, Any]:
        """Get vector store statistics."""
        ...


class VectorStoreBase(ABC):
    """
    Abstract base class for vector stores.

    Defines the common interface that all vector store implementations
    must follow. Supports both document storage and retrieval.
    """

    def __init__(self, embedder: Any, dimensions: int = 768):
        """
        Initialize the vector store.

        Args:
            embedder: Embedding generator (OllamaEmbedder)
            dimensions: Embedding dimensions (default: 768 for nomic-embed-text)
        """
        self.embedder = embedder
        self.dimensions = dimensions

    @abstractmethod
    async def create_index(self, overwrite: bool = False) -> None:
        """
        Create or verify the vector index.

        Args:
            overwrite: If True, recreate the index if it exists

        Raises:
            RuntimeError: If index creation fails
        """
        pass

    @abstractmethod
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
            chunks: List of text chunks to embed and store
            source: Source name (e.g., filename, URL)
            source_type: Type of source ('document', 'schema', etc.)
            metadata: Optional metadata dictionary

        Raises:
            Exception: If document addition fails
        """
        pass

    @abstractmethod
    async def search(
        self,
        query: str,
        top_k: int = 5,
        source_type: str | None = None,
    ) -> list[dict[str, Any]]:
        """
        Search for similar documents using vector similarity.

        Args:
            query: Search query text
            top_k: Number of results to return
            source_type: Optional filter by source type

        Returns:
            List of dictionaries containing:
                - content: The text content
                - source: Source name
                - source_type: Type of source
                - document_id: Document identifier
                - chunk_index: Index of chunk within document
                - metadata: Additional metadata
                - score: Similarity score (lower is better for cosine distance)

        Raises:
            Exception: If search fails
        """
        pass

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
        This provides better results for queries that benefit from both conceptual
        similarity (semantic) and exact term matching (keyword).

        Args:
            query: Search query text
            top_k: Number of results to return
            source_type: Optional filter by source type
            alpha: Weight for semantic search (0.0 = keyword only, 1.0 = semantic only)
                   Default 0.5 gives equal weight to both.

        Returns:
            List of dictionaries containing:
                - content: The text content
                - source: Source name
                - source_type: Type of source
                - document_id: Document identifier
                - chunk_index: Index of chunk within document
                - metadata: Additional metadata
                - score: Combined RRF score (higher is better)
                - search_type: 'hybrid', 'semantic', or 'keyword'

        Note:
            Default implementation falls back to regular semantic search.
            Subclasses should override to provide true hybrid search.
        """
        logger.debug(
            "hybrid_search_fallback",
            message="Using semantic search fallback - hybrid not implemented",
            store_type=self.__class__.__name__,
        )
        return await self.search(query, top_k, source_type)

    @abstractmethod
    async def delete_document(self, document_id: str) -> int:
        """
        Delete all chunks for a specific document.

        Args:
            document_id: Document ID to delete

        Returns:
            Number of chunks deleted

        Raises:
            Exception: If deletion fails
        """
        pass

    @abstractmethod
    async def get_stats(self) -> dict[str, Any]:
        """
        Get statistics about the vector store.

        Returns:
            Dictionary with statistics such as:
                - num_documents: Total number of unique documents
                - num_chunks: Total number of chunks
                - store_type: Type of vector store
                - dimensions: Embedding dimensions
                - Any other store-specific metrics

        Raises:
            Exception: If stats retrieval fails
        """
        pass

    async def clear_all(self) -> dict[str, int]:
        """
        Clear all data from the vector store.

        Optional method with default implementation that raises NotImplementedError.
        Subclasses should override if they support this operation.

        Returns:
            Dictionary with counts of deleted items

        Raises:
            NotImplementedError: If not implemented by subclass
        """
        raise NotImplementedError(f"{self.__class__.__name__} does not implement clear_all()")

    def __repr__(self) -> str:
        """String representation of the vector store."""
        return f"{self.__class__.__name__}(dimensions={self.dimensions})"
