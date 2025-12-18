"""
RAG Pipeline Package
Phase 2.1: Backend Infrastructure & RAG Pipeline

Components for Retrieval-Augmented Generation:
- Ollama embeddings
- SQL Server 2025 vector store (native VECTOR type)
- Redis vector store (fallback option)
- Document processing with Docling
- Schema indexing for query enhancement
"""

from src.rag.document_processor import DocumentProcessor
from src.rag.embedder import OllamaEmbedder
from src.rag.mssql_vector_store import MSSQLVectorStore
from src.rag.redis_vector_store import RedisVectorStore
from src.rag.schema_indexer import SchemaIndexer

__all__ = [
    "OllamaEmbedder",
    "MSSQLVectorStore",
    "RedisVectorStore",
    "DocumentProcessor",
    "SchemaIndexer",
]
