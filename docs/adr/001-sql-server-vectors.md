# ADR-001: SQL Server 2025 Native Vector Store for RAG Pipeline

**Date:** 2025-01-15

**Status:** Accepted

---

## Context

The Local LLM Research Agent requires a vector store for its RAG (Retrieval-Augmented Generation) pipeline to support document embeddings and similarity search. The system needed a solution that aligns with its core principles of local-first architecture, privacy, and simplicity.

### Requirements
- Store 768-dimensional embeddings from Ollama's nomic-embed-text model
- Fast cosine similarity search for document retrieval
- Integrate seamlessly with existing SQL Server infrastructure
- Support for metadata filtering alongside vector search
- 100% local deployment with no cloud dependencies
- Minimal operational overhead

### Technical Context
- Primary database: SQL Server 2022 (ResearchAnalytics sample)
- Backend database: SQL Server 2025 (LLM_BackEnd with app state)
- Target hardware: High-spec workstation (RTX 5090, 128GB RAM)
- Document processing: PDF/DOCX parsing with local embeddings
- Use case: Context-aware SQL queries with schema and document knowledge

## Decision

We will use **SQL Server 2025's native VECTOR type** as the primary vector store for the RAG pipeline, with Redis Stack as a fallback option.

### Implementation Details
- Use SQL Server 2025's `VECTOR(768)` type for embedding storage
- Implement cosine similarity search using `VECTOR_DISTANCE('cosine', ...)`
- Store embeddings in `LLM_BackEnd.vectors` schema
- Tables:
  - `vectors.documents` - Document chunks with embeddings
  - `vectors.schema_embeddings` - Database schema embeddings
- Redis Stack as configurable fallback via `VECTOR_STORE_TYPE` env var

### Key Technologies
- SQL Server 2025 with native VECTOR support
- SQLAlchemy 2.0 for ORM mapping
- Ollama nomic-embed-text for 768-dimensional embeddings

## Consequences

### Positive Consequences
- **Unified Data Platform**: Single database platform for both operational data and vectors eliminates infrastructure complexity
- **Native Performance**: SQL Server's native vector operations provide optimized similarity search without external dependencies
- **Transactional Consistency**: ACID guarantees for vector operations alongside metadata updates
- **Familiar Tooling**: Standard SQL Server management tools (SSMS, Azure Data Studio) for vector data
- **Hybrid Queries**: Direct SQL joins between vectors and business data for metadata filtering
- **Local Privacy**: All vector data stays within local SQL Server instance
- **Zero Additional Services**: No need to deploy/manage separate vector databases
- **Backup & Recovery**: Standard SQL Server backup strategies cover vector data
- **Enterprise Features**: Built-in security, auditing, and high-availability options

### Negative Consequences
- **SQL Server 2025 Requirement**: Requires newest SQL Server version (not GA at time of decision)
- **Version Dependency**: Two SQL Server instances needed (2022 for sample, 2025 for vectors)
- **Scaling Limitations**: Vector search may not scale as well as specialized vector databases for millions of embeddings
- **Limited Vector Features**: Fewer vector-specific features compared to Pinecone/Weaviate (no approximate nearest neighbor indexes in initial release)
- **Windows Container Requirement**: SQL Server 2025 containers require Windows containers or Linux with appropriate SQL Server image

### Neutral Consequences
- **Fallback Option Required**: Redis Stack maintained as fallback for compatibility/migration
- **Migration Path**: Easy migration to specialized vector DB if scaling requirements change
- **Learning Curve**: Team needs to learn SQL Server 2025 vector syntax

## Alternatives Considered

### Alternative 1: Pinecone
- **Pros:**
  - Purpose-built for vector search
  - Excellent performance at scale
  - Rich feature set (hybrid search, metadata filtering)
  - Managed service with minimal ops
- **Cons:**
  - Cloud-only service violates local-first principle
  - Data privacy concerns for sensitive research data
  - Requires internet connectivity
  - Monthly costs for hosted service
  - Additional authentication/API complexity
- **Reason for rejection:** Violates core local-first and privacy requirements

### Alternative 2: Weaviate
- **Pros:**
  - Open-source and self-hostable
  - Advanced vector search features
  - Good performance characteristics
  - Active community support
- **Cons:**
  - Additional infrastructure to deploy/manage
  - Separate database adds complexity
  - Docker container overhead
  - Data duplication between SQL Server and Weaviate
  - Additional monitoring and backup strategy needed
- **Reason for rejection:** Adds significant operational complexity for marginal performance gains

### Alternative 3: Redis Stack (RediSearch)
- **Pros:**
  - Already deployed for caching
  - Fast in-memory vector search
  - Simple deployment
  - Good integration with Python ecosystem
- **Cons:**
  - In-memory storage limits dataset size
  - Data persistence concerns for large corpora
  - Limited query capabilities vs. SQL
  - No direct joins with business data
  - Separate tooling/management from SQL Server
- **Reason for rejection:** Kept as fallback option, but SQL Server provides better data integration

### Alternative 4: pgvector (PostgreSQL)
- **Pros:**
  - Mature and battle-tested
  - Good vector search performance
  - Rich ecosystem and tooling
  - Free and open-source
- **Cons:**
  - Requires separate PostgreSQL deployment
  - Team expertise in SQL Server, not PostgreSQL
  - Data duplication/synchronization complexity
  - Incompatible with existing SQL Server infrastructure
- **Reason for rejection:** Doesn't leverage existing SQL Server investment

### Alternative 5: Chroma DB
- **Pros:**
  - Purpose-built for LLM applications
  - Simple Python API
  - Good developer experience
  - Embedded mode available
- **Cons:**
  - Additional database to manage
  - Less mature than alternatives
  - Limited enterprise features
  - Separate backup/monitoring strategy
- **Reason for rejection:** Adds complexity without significant benefits over SQL Server native vectors

## References

- **SQL Server 2025 Vector Documentation**: [Microsoft Docs on VECTOR type](https://learn.microsoft.com/en-us/sql/t-sql/data-types/vector-data-type)
- **Related ADRs**:
  - [ADR-003: Dual Database Architecture](003-dual-database-architecture.md) - Explains why SQL Server 2025 backend exists
- **Implementation Files**:
  - `src/rag/mssql_vector_store.py` - Primary vector store implementation
  - `src/rag/redis_vector_store.py` - Fallback implementation
  - `docker/init-backend/03-create-vectors-schema.sql` - Vector schema initialization
- **Configuration**:
  - `.env`: `VECTOR_STORE_TYPE=mssql` (or `redis`)
  - `.env`: `VECTOR_DIMENSIONS=768`

---

**Note:** This decision can be revisited if:
1. SQL Server 2025 vector performance proves inadequate for scale
2. Advanced vector features (approximate nearest neighbor) become critical
3. Cloud deployment becomes a requirement
4. Dataset size exceeds SQL Server's practical vector limits (millions of high-dim vectors)
