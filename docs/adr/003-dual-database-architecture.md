# ADR-003: Dual Database Architecture (Sample vs Backend)

**Date:** 2025-01-15

**Status:** Accepted

---

## Context

The Local LLM Research Agent serves two distinct purposes:
1. **Demo/Research**: Showcase natural language querying against a realistic research analytics database
2. **Application Backend**: Store application state (conversations, documents, queries, dashboards, user settings)

We needed to decide whether to:
- Combine sample data and app state in a single database
- Use separate databases with distinct roles and SQL Server versions

### Requirements
- Realistic sample database for demo queries and testing
- Stable schema for application state (conversations, documents, etc.)
- Preserve sample data across app resets/testing
- Support SQL Server 2025 vector features for embeddings
- Maintain separation of concerns between sample and app data
- Enable independent backup/restore strategies

### Technical Context
- SQL Server 2022 widely available and stable
- SQL Server 2025 introduces native VECTOR type for embeddings
- Docker containers for local deployment
- Sample database based on ResearchAnalytics domain
- Backend needs: conversations, documents, queries, dashboards, vectors

## Decision

We will use a **dual database architecture** with clear separation of responsibilities:

1. **SQL Server 2022 (Port 1433)** - Sample Database
   - Database: `ResearchAnalytics`
   - Purpose: Demo data for natural language queries
   - Schema: Research-themed (Departments, Researchers, Projects, Publications, etc.)
   - Container: `local-agent-mssql`
   - Read/write operations via MCP

2. **SQL Server 2025 (Port 1434)** - Backend Database
   - Database: `LLM_BackEnd`
   - Purpose: Application state + vector embeddings
   - Schemas:
     - `app` - Conversations, queries, dashboards, settings
     - `vectors` - Document embeddings with native VECTOR type
   - Container: `local-agent-mssql-backend`
   - Access via SQLAlchemy ORM + Alembic migrations

### Environment Variables
```bash
# Sample Database (SQL Server 2022)
SQL_SERVER_HOST=localhost
SQL_SERVER_PORT=1433
SQL_DATABASE_NAME=ResearchAnalytics

# Backend Database (SQL Server 2025)
BACKEND_DB_HOST=localhost
BACKEND_DB_PORT=1434
BACKEND_DB_NAME=LLM_BackEnd
```

### Docker Compose Services
```yaml
services:
  mssql:                # SQL Server 2022 - Sample data
    image: mcr.microsoft.com/mssql/server:2022-latest
    ports: ["1433:1433"]

  mssql-backend:        # SQL Server 2025 - App state + vectors
    image: mcr.microsoft.com/mssql/server:2025-latest
    ports: ["1434:1433"]
```

## Consequences

### Positive Consequences
- **Clear Separation of Concerns**: Sample data isolated from application state
- **Version Flexibility**: Use stable SQL Server 2022 for sample, cutting-edge 2025 for vectors
- **Independent Schema Evolution**: Sample schema stable; backend schema evolves via Alembic
- **Backup Independence**: Can backup/restore sample and backend separately
- **Testing Isolation**: Reset sample data without losing conversations/documents
- **Demo Reliability**: Sample database remains pristine for demos/training
- **Migration Safety**: Alembic migrations only touch backend, never sample data
- **Port Isolation**: Different ports prevent accidental cross-database operations
- **Feature Access**: Leverage SQL Server 2025 vector features without upgrading sample DB
- **Resource Monitoring**: Separate containers for performance analysis

### Negative Consequences
- **Infrastructure Complexity**: Two SQL Server containers instead of one
- **Connection Management**: Two connection strings/pools to manage
- **Resource Overhead**: ~2GB RAM per SQL Server container (4GB total)
- **Deployment Complexity**: Two initialization scripts to maintain
- **Networking**: More port mappings and potential conflicts
- **Development Setup**: Developers must start/manage two containers
- **Monitoring**: Need to watch health of two database services
- **Cost**: 2x storage for SQL Server installation in containers

### Neutral Consequences
- **Familiar Pattern**: Mirrors common microservices pattern of per-service databases
- **Documentation**: Must clearly document which DB is used for what
- **Environment Variables**: More env vars but clear naming convention

## Alternatives Considered

### Alternative 1: Single SQL Server 2025 Instance
- **Pros:**
  - Simpler infrastructure (one container)
  - Lower resource usage
  - Single connection pool
  - Fewer ports to manage
  - Easier backup strategy
- **Cons:**
  - Sample and app data mixed in same server
  - Must use SQL Server 2025 for all (overkill for sample data)
  - Schema conflicts possible (namespace collision)
  - Can't reset sample data without affecting app state
  - No version flexibility
  - Single point of failure
- **Reason for rejection:** Mixing concerns makes testing/demos risky; no version flexibility

### Alternative 2: Separate Schemas in Single Database
- **Pros:**
  - One SQL Server instance
  - Lower resource usage
  - Single connection string
  - Simple backup/restore
- **Cons:**
  - Sample and app in same database (namespace sharing)
  - Can't use different SQL Server versions
  - Database-level operations affect both
  - No isolation for security/permissions
  - Migrations could accidentally touch sample schema
- **Reason for rejection:** Insufficient isolation between sample and app concerns

### Alternative 3: PostgreSQL for Backend
- **Pros:**
  - Lower resource usage than SQL Server
  - Excellent pgvector support
  - Free and open-source
  - Rich ecosystem
- **Cons:**
  - Mixed database platforms (SQL Server + PostgreSQL)
  - Team needs expertise in both platforms
  - Different tooling/management for each
  - pyodbc + psycopg2 dependencies
  - No consistent SQL dialect
  - MCP integration only for SQL Server
- **Reason for rejection:** Adds complexity and mixed expertise requirements

### Alternative 4: SQLite for Backend
- **Pros:**
  - Zero-configuration embedded DB
  - Minimal resource usage
  - File-based (easy backup)
  - Fast for small datasets
- **Cons:**
  - No native vector support (requires extensions)
  - Limited concurrency (write locks)
  - Not production-grade for multi-user
  - No stored procedures/advanced SQL
  - Missing enterprise features
- **Reason for rejection:** Inadequate for vector operations and concurrent access

### Alternative 5: Redis for Backend State
- **Pros:**
  - Fast in-memory operations
  - Already deployed for caching
  - Simple key-value operations
- **Cons:**
  - Not relational (no SQL queries)
  - Data modeling complexity
  - No ACID transactions
  - No built-in migrations
  - Limited querying capabilities
  - Persistence concerns for critical state
- **Reason for rejection:** Insufficient for complex relational app state

### Alternative 6: Single SQL Server 2022 with External Vector Store
- **Pros:**
  - One SQL Server (simpler)
  - Use stable SQL Server 2022
  - Dedicated vector DB for performance
- **Cons:**
  - Three systems to manage (SQL 2022 + vector DB + Redis)
  - Data split across multiple systems
  - Complex query logic (join SQL with vectors)
  - Additional infrastructure
- **Reason for rejection:** More complex than dual SQL Server; see ADR-001

## References

- **Related ADRs**:
  - [ADR-001: SQL Server Vectors](001-sql-server-vectors.md) - Why SQL Server 2025 for vectors
- **Implementation Files**:
  - `docker/docker-compose.yml` - Both SQL Server containers
  - `docker/init/` - Sample database initialization scripts
  - `docker/init-backend/` - Backend database initialization scripts
  - `src/api/deps.py` - Dependency injection for backend DB
  - `src/mcp/mssql_config.py` - MCP configuration for sample DB
  - `alembic/` - Migrations for backend database only
- **Database Schemas**:
  - Sample: `dbo` (Departments, Researchers, Projects, etc.)
  - Backend `app`: conversations, documents, queries, dashboards
  - Backend `vectors`: document_embeddings, schema_embeddings
- **Configuration**:
  - `.env`: Separate connection strings for each database
  - `alembic.ini`: Points to BACKEND_DB_* settings

---

**Note:** This decision should be revisited if:
1. Resource constraints require reducing to single SQL Server instance
2. SQL Server 2022 adds native vector support (eliminating need for 2025)
3. Project moves to cloud deployment where managed instances are used
4. Team adopts microservices requiring per-service databases
5. Vector store requirements exceed SQL Server capabilities
