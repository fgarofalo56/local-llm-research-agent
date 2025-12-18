# RAG Pipeline API Reference

> **Document Processing & Vector Search**

The RAG (Retrieval-Augmented Generation) pipeline provides document processing, embedding generation, vector storage, and similarity search capabilities.

---

## Overview

The RAG pipeline consists of five main components:

| Component | Module | Purpose |
|-----------|--------|---------|
| **Embedder** | `src/rag/embedder.py` | Generate vector embeddings via Ollama |
| **MSSQL Vector Store** | `src/rag/mssql_vector_store.py` | Store and search vectors in SQL Server 2025 (primary) |
| **Redis Vector Store** | `src/rag/redis_vector_store.py` | Store and search vectors in Redis (fallback) |
| **Document Processor** | `src/rag/document_processor.py` | Parse PDF/DOCX documents |
| **Schema Indexer** | `src/rag/schema_indexer.py` | Index database schema |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Document Upload                           │
│  ┌─────────────────┐                                        │
│  │  PDF/DOCX/TXT   │                                        │
│  └────────┬────────┘                                        │
└───────────┼─────────────────────────────────────────────────┘
            │
            ▼
┌─────────────────────────────────────────────────────────────┐
│                 Document Processor (Docling)                 │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  Extract Text → Clean → Chunk (512 tokens, 50 overlap) │    │
│  └────────────────────────────────────────────────────┘    │
└───────────┬─────────────────────────────────────────────────┘
            │
            ▼
┌─────────────────────────────────────────────────────────────┐
│                 Ollama Embedder (nomic-embed-text)           │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  Text Chunks → 768-dimensional Vectors              │    │
│  └────────────────────────────────────────────────────┘    │
└───────────┬─────────────────────────────────────────────────┘
            │
            ├──────────────────────────────┐
            ▼                              ▼
┌───────────────────────────────┐  ┌───────────────────────────────┐
│   SQL Server 2025 (Primary)   │  │   Redis Stack (Fallback)      │
│  ┌─────────────────────────┐  │  │  ┌─────────────────────────┐  │
│  │  VECTOR(768) native     │  │  │  │  HNSW Index             │  │
│  │  VECTOR_DISTANCE cosine │  │  │  │  Cosine Similarity      │  │
│  └─────────────────────────┘  │  │  └─────────────────────────┘  │
└───────────────────────────────┘  └───────────────────────────────┘
```

### Vector Store Selection

The vector store is selected based on `VECTOR_STORE_TYPE` in `.env`:

| Value | Vector Store | Database | Features |
|-------|--------------|----------|----------|
| `mssql` (default) | MSSQLVectorStore | SQL Server 2025 | Native VECTOR type, VECTOR_DISTANCE |
| `redis` | RedisVectorStore | Redis Stack | HNSW index, in-memory |

If the primary store fails to initialize, the system automatically falls back to Redis.

---

## OllamaEmbedder

### `src/rag/embedder.py`

Generates text embeddings using Ollama's local embedding models.

### Class: `OllamaEmbedder`

```python
from src.rag.embedder import OllamaEmbedder

embedder = OllamaEmbedder(
    host="http://localhost:11434",
    model="nomic-embed-text"
)
```

#### Constructor Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `host` | str | `http://localhost:11434` | Ollama server URL |
| `model` | str | `nomic-embed-text` | Embedding model name |

#### Methods

##### `async embed(text: str) -> list[float]`

Generate embedding for a single text.

```python
embedding = await embedder.embed("What is machine learning?")
# Returns: [0.123, -0.456, 0.789, ...] (768 dimensions)
```

##### `async embed_batch(texts: list[str]) -> list[list[float]]`

Generate embeddings for multiple texts.

```python
texts = ["Document 1", "Document 2", "Document 3"]
embeddings = await embedder.embed_batch(texts)
# Returns: [[...], [...], [...]]
```

### Embedding Model Options

| Model | Dimensions | Speed | Quality |
|-------|------------|-------|---------|
| `nomic-embed-text` | 768 | Fast | Good |
| `mxbai-embed-large` | 1024 | Medium | Better |
| `all-minilm` | 384 | Very Fast | Basic |

---

## MSSQLVectorStore

### `src/rag/mssql_vector_store.py`

Vector store implementation using SQL Server 2025's native VECTOR type.

### Class: `MSSQLVectorStore`

```python
from sqlalchemy.ext.asyncio import async_sessionmaker
from src.rag.embedder import OllamaEmbedder
from src.rag.mssql_vector_store import MSSQLVectorStore

session_factory = async_sessionmaker(engine)
embedder = OllamaEmbedder()
vector_store = MSSQLVectorStore(
    session_factory=session_factory,
    embedder=embedder,
    dimensions=768
)
```

#### Constructor Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `session_factory` | async_sessionmaker | Required | SQLAlchemy async session factory |
| `embedder` | OllamaEmbedder | Required | Embedding generator |
| `dimensions` | int | 768 | Vector dimensions (must match embedding model) |

#### Methods

##### `async create_index(overwrite: bool = False) -> None`

Create the vector tables and stored procedures in SQL Server.

```python
await vector_store.create_index(overwrite=True)
```

This creates:
- `vectors.document_chunks` table with VECTOR(768) column
- `vectors.schema_chunks` table for database schema embeddings
- `vectors.SearchDocuments` stored procedure
- `vectors.SearchSchema` stored procedure

##### `async add_document(...) -> None`

Add document chunks to the vector store.

```python
await vector_store.add_document(
    document_id="doc_123",
    chunks=["Chunk 1 text", "Chunk 2 text"],
    source="report.pdf",
    source_type="document",  # or "schema"
    metadata={"author": "John Doe"}
)
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `document_id` | str | Unique document identifier |
| `chunks` | list[str] | Text chunks to index |
| `source` | str | Source name (filename) |
| `source_type` | str | `"document"` or `"schema"` |
| `metadata` | dict | Optional metadata |

##### `async search(query: str, top_k: int = 5, source_type: str = None, document_id: str = None) -> list[dict]`

Search for similar documents using VECTOR_DISTANCE.

```python
results = await vector_store.search(
    query="What are the project requirements?",
    top_k=5,
    source_type="document"
)

for result in results:
    print(f"Distance: {result['distance']}")
    print(f"Content: {result['content']}")
    print(f"Source: {result['source']}")
```

**Returns:**
```python
[
    {
        "content": "The project requires...",
        "source": "requirements.pdf",
        "source_type": "document",
        "document_id": "doc_123",
        "chunk_index": 3,
        "metadata": {"author": "John"},
        "distance": 0.15  # Lower is more similar (cosine distance)
    }
]
```

##### `async delete_document(document_id: str) -> int`

Delete all chunks for a document.

```python
deleted_count = await vector_store.delete_document("doc_123")
print(f"Deleted {deleted_count} chunks")
```

##### `async get_stats() -> dict`

Get vector store statistics.

```python
stats = await vector_store.get_stats()
# Returns: {"document_chunks": 100, "schema_chunks": 50}
```

### Database Schema

The MSSQL vector store uses these tables:

**vectors.document_chunks:**
| Column | Type | Description |
|--------|------|-------------|
| `id` | INT IDENTITY | Primary key |
| `document_id` | INT | Document reference |
| `chunk_index` | INT | Chunk position |
| `content` | NVARCHAR(MAX) | Chunk text |
| `embedding` | VECTOR(768) | Vector embedding |
| `source` | NVARCHAR(255) | Source filename |
| `source_type` | NVARCHAR(50) | Type: document/schema |
| `metadata` | NVARCHAR(MAX) | JSON metadata |

**Stored Procedures:**
- `vectors.SearchDocuments` - Vector similarity search with optional filters
- `vectors.SearchSchema` - Schema-specific vector search

---

## RedisVectorStore

### `src/rag/redis_vector_store.py`

Vector store implementation using Redis Stack with HNSW indexing. This is the fallback option when SQL Server 2025 is not available.

### Class: `RedisVectorStore`

```python
from redis.asyncio import Redis
from src.rag.embedder import OllamaEmbedder
from src.rag.redis_vector_store import RedisVectorStore

redis = Redis.from_url("redis://localhost:6379")
embedder = OllamaEmbedder()
vector_store = RedisVectorStore(
    redis_client=redis,
    embedder=embedder,
    dimensions=768
)
```

#### Constructor Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `redis_client` | Redis | Required | Async Redis client |
| `embedder` | OllamaEmbedder | Required | Embedding generator |
| `dimensions` | int | 768 | Vector dimensions |

#### Methods

##### `async create_index(overwrite: bool = False) -> None`

Create the vector index in Redis.

```python
await vector_store.create_index(overwrite=True)
```

##### `async add_document(...) -> None`

Add document chunks to the vector store.

```python
await vector_store.add_document(
    document_id="doc_123",
    chunks=["Chunk 1 text", "Chunk 2 text"],
    source="report.pdf",
    source_type="document",  # or "schema"
    metadata={"author": "John Doe"}
)
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `document_id` | str | Unique document identifier |
| `chunks` | list[str] | Text chunks to index |
| `source` | str | Source name (filename) |
| `source_type` | str | `"document"` or `"schema"` |
| `metadata` | dict | Optional metadata |

##### `async search(query: str, top_k: int = 5, source_type: str = None) -> list[dict]`

Search for similar documents.

```python
results = await vector_store.search(
    query="What are the project requirements?",
    top_k=5,
    source_type="document"
)

for result in results:
    print(f"Score: {result['score']}")
    print(f"Content: {result['content']}")
    print(f"Source: {result['source']}")
```

**Returns:**
```python
[
    {
        "content": "The project requires...",
        "source": "requirements.pdf",
        "source_type": "document",
        "document_id": "doc_123",
        "chunk_index": 3,
        "metadata": {"author": "John"},
        "score": 0.92  # Lower is more similar (cosine distance)
    }
]
```

##### `async delete_document(document_id: str) -> int`

Delete all chunks for a document.

```python
deleted_count = await vector_store.delete_document("doc_123")
print(f"Deleted {deleted_count} chunks")
```

##### `async get_stats() -> dict`

Get vector store statistics.

```python
stats = await vector_store.get_stats()
# Returns: {"index_name": "documents", "num_docs": 100, "num_records": 500}
```

### Index Schema

The Redis index schema:

| Field | Type | Description |
|-------|------|-------------|
| `content` | TEXT | Chunk text content |
| `source` | TAG | Source filename |
| `source_type` | TAG | `document` or `schema` |
| `document_id` | TAG | Document identifier |
| `chunk_index` | NUMERIC | Chunk position |
| `metadata` | TEXT | JSON metadata |
| `embedding` | VECTOR | 768-dim float32, HNSW, cosine |

---

## DocumentProcessor

### `src/rag/document_processor.py`

Processes documents using Docling for text extraction and chunking.

### Class: `DocumentProcessor`

```python
from src.rag.document_processor import DocumentProcessor

processor = DocumentProcessor(
    chunk_size=512,
    chunk_overlap=50
)
```

#### Constructor Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `chunk_size` | int | 512 | Characters per chunk |
| `chunk_overlap` | int | 50 | Overlap between chunks |

#### Methods

##### `async process_file(file_path: Path) -> list[str]`

Process a document file and return text chunks.

```python
from pathlib import Path

chunks = await processor.process_file(Path("document.pdf"))
# Returns: ["Chunk 1...", "Chunk 2...", ...]
```

**Supported Formats:**
- PDF (`.pdf`)
- Word Documents (`.docx`)
- Text Files (`.txt`)
- Markdown (`.md`)

##### `async process_text(text: str) -> list[str]`

Process raw text into chunks.

```python
text = "Long document text..."
chunks = await processor.process_text(text)
```

### Chunking Strategy

The chunking algorithm:
1. Splits text at sentence boundaries
2. Combines sentences until reaching `chunk_size`
3. Maintains `chunk_overlap` characters between chunks
4. Ensures no mid-word splits

---

## SchemaIndexer

### `src/rag/schema_indexer.py`

Indexes database schema information for RAG context.

### Class: `SchemaIndexer`

```python
from src.rag.schema_indexer import SchemaIndexer

indexer = SchemaIndexer(vector_store=vector_store)
```

#### Methods

##### `async index_mcp_schema(mcp_manager) -> int`

Index database schema from MCP server.

```python
chunks_created = await indexer.index_mcp_schema(mcp_manager)
print(f"Created {chunks_created} schema chunks")
```

This indexes:
- Table names and descriptions
- Column names, types, and constraints
- Foreign key relationships
- Index information

##### `async index_schema_text(schema_text: str) -> int`

Index raw schema text.

```python
schema = """
Table: Researchers
- id (INT, PRIMARY KEY)
- name (VARCHAR(100))
- department_id (INT, FOREIGN KEY -> Departments.id)
"""
chunks_created = await indexer.index_schema_text(schema)
```

---

## Configuration

### Environment Variables

```bash
# Vector Store Selection
VECTOR_STORE_TYPE=mssql            # "mssql" (primary) or "redis" (fallback)
VECTOR_DIMENSIONS=768              # Must match embedding model

# Backend Database (SQL Server 2025 for MSSQL vector store)
BACKEND_DB_HOST=localhost
BACKEND_DB_PORT=1434
BACKEND_DB_NAME=LLM_BackEnd
BACKEND_DB_TRUST_CERT=true

# Redis Vector Store (fallback)
REDIS_URL=redis://localhost:6379

# Embedding Model
EMBEDDING_MODEL=nomic-embed-text   # 768 dimensions

# Document Processing
CHUNK_SIZE=512
CHUNK_OVERLAP=50

# RAG Search
RAG_TOP_K=5

# Storage
UPLOAD_DIR=data/uploads
MAX_UPLOAD_SIZE_MB=50
```

### Settings Class

```python
from src.utils.config import settings

# Access RAG settings
print(settings.redis_url)          # redis://localhost:6379
print(settings.embedding_model)    # nomic-embed-text
print(settings.chunk_size)         # 512
print(settings.chunk_overlap)      # 50
print(settings.rag_top_k)          # 5
```

---

## Usage Examples

### Full RAG Pipeline with MSSQL Vector Store

```python
import asyncio
from pathlib import Path
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from src.rag.embedder import OllamaEmbedder
from src.rag.mssql_vector_store import MSSQLVectorStore
from src.rag.document_processor import DocumentProcessor

async def main():
    # Initialize database connection
    engine = create_async_engine(
        "mssql+aioodbc://sa:password@localhost:1434/LLM_BackEnd"
        "?driver=ODBC+Driver+18+for+SQL+Server&TrustServerCertificate=yes"
    )
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    # Initialize components
    embedder = OllamaEmbedder()
    vector_store = MSSQLVectorStore(session_factory, embedder, dimensions=768)
    processor = DocumentProcessor()

    # Create index (tables and stored procedures)
    await vector_store.create_index()

    # Process and index a document
    result = await processor.process_file(Path("report.pdf"))
    await vector_store.add_document(
        document_id="report_001",
        chunks=result["chunks"],
        source="report.pdf",
        source_type="document"
    )

    # Search using native VECTOR_DISTANCE
    results = await vector_store.search(
        query="What are the main findings?",
        top_k=5
    )

    for result in results:
        print(f"[{result['distance']:.3f}] {result['content'][:100]}...")

    await engine.dispose()

asyncio.run(main())
```

### Full RAG Pipeline with Redis Vector Store (Fallback)

```python
import asyncio
from pathlib import Path
from redis.asyncio import Redis
from src.rag.embedder import OllamaEmbedder
from src.rag.redis_vector_store import RedisVectorStore
from src.rag.document_processor import DocumentProcessor

async def main():
    # Initialize components
    redis = Redis.from_url("redis://localhost:6379")
    embedder = OllamaEmbedder()
    vector_store = RedisVectorStore(redis, embedder)
    processor = DocumentProcessor()

    # Create index
    await vector_store.create_index()

    # Process and index a document
    result = await processor.process_file(Path("report.pdf"))
    await vector_store.add_document(
        document_id="report_001",
        chunks=result["chunks"],
        source="report.pdf",
        source_type="document"
    )

    # Search
    results = await vector_store.search(
        query="What are the main findings?",
        top_k=5
    )

    for result in results:
        print(f"[{result['score']:.3f}] {result['content'][:100]}...")

    await redis.close()

asyncio.run(main())
```

### Integration with Agent

```python
from src.rag.redis_vector_store import RedisVectorStore

async def get_rag_context(query: str, vector_store: RedisVectorStore) -> str:
    """Get RAG context for agent prompt."""
    results = await vector_store.search(query, top_k=3)

    context_parts = []
    for i, result in enumerate(results, 1):
        context_parts.append(
            f"[{i}] Source: {result['source']}\n"
            f"Content: {result['content']}\n"
        )

    return "\n".join(context_parts)

# Use in agent prompt
rag_context = await get_rag_context(user_query, vector_store)
enhanced_prompt = f"""
Context from documents:
{rag_context}

User question: {user_query}
"""
```

---

## Performance Considerations

### Embedding Generation

- Batch embeddings when possible (`embed_batch`)
- Cache frequently used embeddings
- Use appropriate model for speed vs quality trade-off

### Vector Search

- HNSW provides fast approximate nearest neighbor search
- Adjust `top_k` based on needs (more results = slower)
- Filter by `source_type` to narrow search scope

### Document Processing

- Large documents are automatically chunked
- Chunk size affects retrieval granularity
- Overlap ensures context preservation

---

*Last Updated: December 2025*
