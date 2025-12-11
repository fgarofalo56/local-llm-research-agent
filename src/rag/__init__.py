"""
RAG Pipeline Package
Phase 2.1: Backend Infrastructure & RAG Pipeline

Components for Retrieval-Augmented Generation:
- Ollama embeddings
- Redis vector store
- Document processing with Docling
- Schema indexing for query enhancement
"""

from src.rag.document_processor import DocumentProcessor
from src.rag.embedder import OllamaEmbedder
from src.rag.redis_vector_store import RedisVectorStore
from src.rag.schema_indexer import SchemaIndexer

__all__ = [
    "OllamaEmbedder",
    "RedisVectorStore",
    "DocumentProcessor",
    "SchemaIndexer",
]
