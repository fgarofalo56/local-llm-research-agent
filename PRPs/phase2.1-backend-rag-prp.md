# Phase 2.1: Backend Infrastructure & RAG Pipeline

## Overview

| Attribute | Value |
|-----------|-------|
| **Phase** | 2.1 |
| **Focus** | Python, FastAPI, Database, RAG |
| **Estimated Effort** | 3-4 days |
| **Prerequisites** | Phase 1 complete, Docker running |

## Goal

Establish the backend infrastructure for Phase 2 features including FastAPI application, database schema expansion, Redis Stack vector store, RAG pipeline with Docling, and dynamic MCP server configuration.

## Success Criteria

- [ ] Redis Stack container running alongside SQL Server
- [ ] FastAPI application starts with Swagger docs at `/docs`
- [ ] All new database tables created via Alembic migrations
- [ ] Health check endpoints return status for all services
- [ ] MCP servers load dynamically from `mcp_config.json`
- [ ] Documents can be uploaded via API and processed by Docling
- [ ] Document chunks stored in Redis with vector embeddings
- [ ] Schema descriptions indexed in RAG for query enhancement
- [ ] Existing CLI and Streamlit interfaces still work

## Technology Stack Additions

### Python Dependencies

Add to `pyproject.toml`:

```toml
[project]
dependencies = [
    # Existing dependencies...
    
    # Phase 2.1 additions
    "fastapi>=0.115.0",
    "uvicorn[standard]>=0.32.0",
    "sqlalchemy>=2.0.0",
    "alembic>=1.14.0",
    "python-multipart>=0.0.12",
    "aiofiles>=24.1.0",
    "websockets>=14.0",
    "docling>=2.15.0",
    "redisvl>=0.3.0",
    "redis>=5.0.0",
    "apscheduler>=3.10.0",
]
```

### Docker Services

```yaml
# docker/docker-compose.yml
version: '3.8'

services:
  mssql:
    image: mcr.microsoft.com/mssql/server:2022-latest
    container_name: local-llm-mssql
    environment:
      - ACCEPT_EULA=Y
      - MSSQL_SA_PASSWORD=${MSSQL_SA_PASSWORD:-LocalLLM@2024!}
      - MSSQL_PID=Developer
    ports:
      - "1433:1433"
    volumes:
      - mssql_data:/var/opt/mssql
    healthcheck:
      test: /opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P "$$MSSQL_SA_PASSWORD" -C -Q "SELECT 1"
      interval: 10s
      timeout: 5s
      retries: 5

  redis-stack:
    image: redis/redis-stack:latest
    container_name: local-llm-redis
    ports:
      - "6379:6379"
      - "8001:8001"  # RedisInsight GUI
    volumes:
      - redis_data:/data
    environment:
      - REDIS_ARGS=--save 60 1 --appendonly yes
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  api:
    build:
      context: ..
      dockerfile: docker/Dockerfile.api
    container_name: local-llm-api
    ports:
      - "8000:8000"
    environment:
      - SQL_SERVER_HOST=mssql
      - REDIS_URL=redis://redis-stack:6379
      - OLLAMA_HOST=${OLLAMA_HOST:-http://host.docker.internal:11434}
    volumes:
      - ../data/uploads:/app/uploads
      - ../data/models:/app/models
    depends_on:
      mssql:
        condition: service_healthy
      redis-stack:
        condition: service_healthy

volumes:
  mssql_data:
  redis_data:
```

## Implementation Plan

### Step 1: Docker Infrastructure

#### 1.1 Update docker-compose.yml

Add Redis Stack service as shown above.

#### 1.2 Create API Dockerfile

```dockerfile
# docker/Dockerfile.api
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Install uv for fast package management
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.cargo/bin:$PATH"

# Copy project files
COPY pyproject.toml .
COPY src/ src/

# Install dependencies
RUN uv sync

# Expose port
EXPOSE 8000

# Run FastAPI
CMD ["uv", "run", "uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### 1.3 Create data directories

```bash
mkdir -p data/uploads data/models
```

---

### Step 2: Database Schema

#### 2.1 Create Alembic configuration

```bash
uv run alembic init alembic
```

#### 2.2 Update alembic.ini

```ini
# alembic.ini
[alembic]
script_location = alembic
sqlalchemy.url = driver://user:pass@localhost/dbname

# Will be overridden by env.py
```

#### 2.3 Create alembic/env.py

```python
# alembic/env.py
import os
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context

config = context.config

# Override sqlalchemy.url from environment
database_url = os.getenv(
    "DATABASE_URL",
    "mssql+pyodbc://sa:LocalLLM%402024%21@localhost:1433/ResearchAnalytics?driver=ODBC+Driver+18+for+SQL+Server&TrustServerCertificate=yes"
)
config.set_main_option("sqlalchemy.url", database_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

from src.api.models.database import Base
target_metadata = Base.metadata

def run_migrations_offline():
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

#### 2.4 Create database models

```python
# src/api/models/database.py
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Boolean, 
    ForeignKey, BigInteger, Numeric, create_engine
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

Base = declarative_base()

class Conversation(Base):
    __tablename__ = "conversations"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_archived = Column(Boolean, default=False)
    
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")


class Message(Base):
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id", ondelete="CASCADE"))
    role = Column(String(20))  # 'user', 'assistant', 'system'
    content = Column(Text)
    tool_calls = Column(Text)  # JSON
    tokens_used = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    conversation = relationship("Conversation", back_populates="messages")


class Dashboard(Base):
    __tablename__ = "dashboards"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    layout = Column(Text)  # JSON grid config
    is_default = Column(Boolean, default=False)
    share_token = Column(String(64), unique=True, nullable=True)
    share_expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    widgets = relationship("DashboardWidget", back_populates="dashboard", cascade="all, delete-orphan")


class DashboardWidget(Base):
    __tablename__ = "dashboard_widgets"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    dashboard_id = Column(Integer, ForeignKey("dashboards.id", ondelete="CASCADE"))
    widget_type = Column(String(50))  # 'bar_chart', 'line_chart', 'kpi_card', 'table'
    title = Column(String(255))
    query = Column(Text)
    chart_config = Column(Text)  # JSON
    position = Column(Text)  # JSON {x, y, w, h}
    refresh_interval = Column(Integer)  # seconds, NULL = manual
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    dashboard = relationship("Dashboard", back_populates="widgets")


class QueryHistory(Base):
    __tablename__ = "query_history"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id", ondelete="SET NULL"), nullable=True)
    natural_language = Column(Text)
    generated_sql = Column(Text)
    result_row_count = Column(Integer)
    execution_time_ms = Column(Integer)
    is_favorite = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class SavedQuery(Base):
    __tablename__ = "saved_queries"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255))
    description = Column(Text)
    query = Column(Text)
    tags = Column(Text)  # JSON array
    created_at = Column(DateTime, default=datetime.utcnow)


class Document(Base):
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    filename = Column(String(255))
    original_filename = Column(String(255))
    mime_type = Column(String(100))
    file_size = Column(BigInteger)
    chunk_count = Column(Integer)
    processing_status = Column(String(50))  # 'pending', 'processing', 'completed', 'failed'
    error_message = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    processed_at = Column(DateTime)


class DataAlert(Base):
    __tablename__ = "data_alerts"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255))
    query = Column(Text)
    condition = Column(String(50))  # 'greater_than', 'less_than', 'equals', 'changes'
    threshold = Column(Numeric(18, 4))
    is_active = Column(Boolean, default=True)
    last_checked_at = Column(DateTime)
    last_triggered_at = Column(DateTime)
    last_value = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)


class ScheduledQuery(Base):
    __tablename__ = "scheduled_queries"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255))
    query = Column(Text)
    cron_expression = Column(String(100))  # e.g., "0 8 * * *" for 8am daily
    is_active = Column(Boolean, default=True)
    last_run_at = Column(DateTime)
    next_run_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)


class MCPServerConfig(Base):
    __tablename__ = "mcp_server_configs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    server_id = Column(String(100), unique=True)
    name = Column(String(255))
    description = Column(Text)
    server_type = Column(String(20))  # 'stdio', 'http'
    command = Column(Text)
    args = Column(Text)  # JSON array
    url = Column(String(500))
    environment = Column(Text)  # JSON object
    is_enabled = Column(Boolean, default=True)
    is_built_in = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ThemeConfig(Base):
    __tablename__ = "theme_configs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), unique=True)
    display_name = Column(String(255))
    is_preset = Column(Boolean, default=False)
    is_active = Column(Boolean, default=False)
    config = Column(Text)  # JSON theme configuration
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

#### 2.5 Generate migration

```bash
uv run alembic revision --autogenerate -m "Add Phase 2 tables"
uv run alembic upgrade head
```

---

### Step 3: FastAPI Application

#### 3.1 Create main application

```python
# src/api/main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import structlog

from src.api.routes import (
    health,
    documents,
    conversations,
    queries,
    dashboards,
    mcp_servers,
    settings,
    agent,
)
from src.api.deps import init_services, shutdown_services

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    logger.info("Starting application...")
    await init_services()
    yield
    logger.info("Shutting down application...")
    await shutdown_services()


app = FastAPI(
    title="Local LLM Research Analytics API",
    description="API for local LLM-powered SQL Server analytics",
    version="2.1.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite dev server
        "http://localhost:3000",  # Alternative React port
        "http://localhost:8501",  # Streamlit
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, prefix="/api/health", tags=["Health"])
app.include_router(documents.router, prefix="/api/documents", tags=["Documents"])
app.include_router(conversations.router, prefix="/api/conversations", tags=["Conversations"])
app.include_router(queries.router, prefix="/api/queries", tags=["Queries"])
app.include_router(dashboards.router, prefix="/api/dashboards", tags=["Dashboards"])
app.include_router(mcp_servers.router, prefix="/api/mcp-servers", tags=["MCP Servers"])
app.include_router(settings.router, prefix="/api/settings", tags=["Settings"])
app.include_router(agent.router, prefix="/api/agent", tags=["Agent"])


@app.get("/")
async def root():
    return {"message": "Local LLM Research Analytics API", "version": "2.1.0"}
```

#### 3.2 Create dependencies

```python
# src/api/deps.py
from functools import lru_cache
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from redis.asyncio import Redis
import structlog

from src.utils.config import get_settings
from src.rag.redis_vector_store import RedisVectorStore
from src.rag.embedder import OllamaEmbedder
from src.mcp.dynamic_manager import DynamicMCPManager

logger = structlog.get_logger()

# Global instances
_engine = None
_session_factory = None
_redis_client = None
_vector_store = None
_embedder = None
_mcp_manager = None


async def init_services():
    """Initialize all services on startup."""
    global _engine, _session_factory, _redis_client, _vector_store, _embedder, _mcp_manager
    
    settings = get_settings()
    
    # Database
    _engine = create_async_engine(settings.database_url_async, echo=settings.debug)
    _session_factory = async_sessionmaker(_engine, expire_on_commit=False)
    logger.info("Database engine initialized")
    
    # Redis
    _redis_client = Redis.from_url(settings.redis_url, decode_responses=True)
    await _redis_client.ping()
    logger.info("Redis connection established")
    
    # Embedder
    _embedder = OllamaEmbedder(
        base_url=settings.ollama_host,
        model=settings.embedding_model,
    )
    logger.info("Ollama embedder initialized")
    
    # Vector store
    _vector_store = RedisVectorStore(
        redis_client=_redis_client,
        embedder=_embedder,
    )
    await _vector_store.create_index()
    logger.info("Redis vector store initialized")
    
    # MCP Manager
    _mcp_manager = DynamicMCPManager(config_path=settings.mcp_config_path)
    await _mcp_manager.load_config()
    logger.info("MCP manager initialized")


async def shutdown_services():
    """Cleanup services on shutdown."""
    global _engine, _redis_client, _mcp_manager
    
    if _mcp_manager:
        await _mcp_manager.shutdown()
    
    if _redis_client:
        await _redis_client.close()
    
    if _engine:
        await _engine.dispose()
    
    logger.info("All services shut down")


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Get database session."""
    async with _session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


def get_redis() -> Redis:
    """Get Redis client."""
    return _redis_client


def get_vector_store() -> RedisVectorStore:
    """Get vector store."""
    return _vector_store


def get_embedder() -> OllamaEmbedder:
    """Get embedder."""
    return _embedder


def get_mcp_manager() -> DynamicMCPManager:
    """Get MCP manager."""
    return _mcp_manager
```

#### 3.3 Update config

```python
# src/utils/config.py
from functools import lru_cache
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings."""
    
    # Ollama
    ollama_host: str = Field(default="http://localhost:11434", env="OLLAMA_HOST")
    ollama_model: str = Field(default="qwen3:30b", env="OLLAMA_MODEL")
    embedding_model: str = Field(default="nomic-embed-text", env="EMBEDDING_MODEL")
    
    # SQL Server
    sql_server_host: str = Field(default="localhost", env="SQL_SERVER_HOST")
    sql_server_port: int = Field(default=1433, env="SQL_SERVER_PORT")
    sql_database_name: str = Field(default="ResearchAnalytics", env="SQL_DATABASE_NAME")
    sql_username: str = Field(default="sa", env="SQL_USERNAME")
    sql_password: str = Field(default="LocalLLM@2024!", env="SQL_PASSWORD")
    
    # Redis
    redis_url: str = Field(default="redis://localhost:6379", env="REDIS_URL")
    
    # MCP
    mcp_config_path: str = Field(default="mcp_config.json", env="MCP_CONFIG_PATH")
    
    # API
    api_host: str = Field(default="0.0.0.0", env="API_HOST")
    api_port: int = Field(default=8000, env="API_PORT")
    
    # Storage
    upload_dir: str = Field(default="./data/uploads", env="UPLOAD_DIR")
    max_upload_size_mb: int = Field(default=100, env="MAX_UPLOAD_SIZE_MB")
    
    # RAG
    chunk_size: int = Field(default=500, env="CHUNK_SIZE")
    chunk_overlap: int = Field(default=50, env="CHUNK_OVERLAP")
    rag_top_k: int = Field(default=5, env="RAG_TOP_K")
    
    # App
    debug: bool = Field(default=False, env="DEBUG")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    
    @property
    def database_url(self) -> str:
        """Get sync database URL."""
        password = self.sql_password.replace("@", "%40")
        return (
            f"mssql+pyodbc://{self.sql_username}:{password}@"
            f"{self.sql_server_host}:{self.sql_server_port}/{self.sql_database_name}"
            f"?driver=ODBC+Driver+18+for+SQL+Server&TrustServerCertificate=yes"
        )
    
    @property
    def database_url_async(self) -> str:
        """Get async database URL."""
        password = self.sql_password.replace("@", "%40")
        return (
            f"mssql+aioodbc://{self.sql_username}:{password}@"
            f"{self.sql_server_host}:{self.sql_server_port}/{self.sql_database_name}"
            f"?driver=ODBC+Driver+18+for+SQL+Server&TrustServerCertificate=yes"
        )
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
```

---

### Step 4: Health Check Endpoints

```python
# src/api/routes/health.py
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import httpx
import structlog

from src.api.deps import get_db, get_redis, get_mcp_manager

router = APIRouter()
logger = structlog.get_logger()


class ServiceHealth(BaseModel):
    name: str
    status: str  # 'healthy', 'unhealthy', 'unknown'
    message: str | None = None
    latency_ms: float | None = None


class HealthResponse(BaseModel):
    status: str
    services: list[ServiceHealth]


@router.get("", response_model=HealthResponse)
async def health_check(
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    """Check health of all services."""
    services = []
    overall_status = "healthy"
    
    # SQL Server
    try:
        import time
        start = time.time()
        await db.execute(text("SELECT 1"))
        latency = (time.time() - start) * 1000
        services.append(ServiceHealth(
            name="sql_server",
            status="healthy",
            latency_ms=round(latency, 2),
        ))
    except Exception as e:
        overall_status = "unhealthy"
        services.append(ServiceHealth(
            name="sql_server",
            status="unhealthy",
            message=str(e),
        ))
    
    # Redis
    try:
        start = time.time()
        await redis.ping()
        latency = (time.time() - start) * 1000
        services.append(ServiceHealth(
            name="redis",
            status="healthy",
            latency_ms=round(latency, 2),
        ))
    except Exception as e:
        overall_status = "unhealthy"
        services.append(ServiceHealth(
            name="redis",
            status="unhealthy",
            message=str(e),
        ))
    
    # Ollama
    try:
        from src.utils.config import get_settings
        settings = get_settings()
        start = time.time()
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{settings.ollama_host}/api/tags", timeout=5.0)
            response.raise_for_status()
        latency = (time.time() - start) * 1000
        services.append(ServiceHealth(
            name="ollama",
            status="healthy",
            latency_ms=round(latency, 2),
        ))
    except Exception as e:
        overall_status = "unhealthy"
        services.append(ServiceHealth(
            name="ollama",
            status="unhealthy",
            message=str(e),
        ))
    
    return HealthResponse(status=overall_status, services=services)


@router.get("/ready")
async def readiness_check():
    """Simple readiness check."""
    return {"status": "ready"}


@router.get("/live")
async def liveness_check():
    """Simple liveness check."""
    return {"status": "alive"}
```

---

### Step 5: RAG Pipeline

#### 5.1 Ollama Embedder

```python
# src/rag/embedder.py
import httpx
import structlog
from typing import List

logger = structlog.get_logger()


class OllamaEmbedder:
    """Generate embeddings using Ollama."""
    
    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = "nomic-embed-text",
    ):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self._dimensions: int | None = None
    
    async def embed(self, text: str) -> List[float]:
        """Generate embedding for a single text."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/api/embeddings",
                json={"model": self.model, "prompt": text},
                timeout=30.0,
            )
            response.raise_for_status()
            data = response.json()
            embedding = data["embedding"]
            
            if self._dimensions is None:
                self._dimensions = len(embedding)
                logger.info("embedding_dimensions_detected", dimensions=self._dimensions)
            
            return embedding
    
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts."""
        embeddings = []
        for text in texts:
            embedding = await self.embed(text)
            embeddings.append(embedding)
        return embeddings
    
    @property
    def dimensions(self) -> int:
        """Get embedding dimensions."""
        if self._dimensions is None:
            raise ValueError("Dimensions unknown. Call embed() first.")
        return self._dimensions
```

#### 5.2 Redis Vector Store

```python
# src/rag/redis_vector_store.py
from typing import List, Dict, Any
from redis.asyncio import Redis
from redisvl.index import AsyncSearchIndex
from redisvl.query import VectorQuery
from redisvl.schema import IndexSchema
import structlog
import json
import hashlib

from src.rag.embedder import OllamaEmbedder

logger = structlog.get_logger()


class RedisVectorStore:
    """Vector store using Redis Stack."""
    
    INDEX_NAME = "documents"
    PREFIX = "doc"
    
    def __init__(
        self,
        redis_client: Redis,
        embedder: OllamaEmbedder,
        dimensions: int = 768,  # nomic-embed-text default
    ):
        self.redis = redis_client
        self.embedder = embedder
        self.dimensions = dimensions
        self._index: AsyncSearchIndex | None = None
    
    def _get_schema(self) -> dict:
        """Get index schema."""
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
    
    async def create_index(self, overwrite: bool = False):
        """Create the vector index."""
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
        chunks: List[str],
        source: str,
        source_type: str = "document",
        metadata: Dict[str, Any] | None = None,
    ):
        """Add document chunks to the vector store."""
        logger.info("adding_document", document_id=document_id, chunk_count=len(chunks))
        
        # Generate embeddings
        embeddings = await self.embedder.embed_batch(chunks)
        
        # Prepare records
        records = []
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            record = {
                "id": self._generate_id(document_id, i),
                "content": chunk,
                "source": source,
                "source_type": source_type,
                "document_id": document_id,
                "chunk_index": i,
                "metadata": json.dumps(metadata or {}),
                "embedding": embedding,
            }
            records.append(record)
        
        # Load into index
        await self._index.load(records)
        logger.info("document_added", document_id=document_id, chunks_added=len(records))
    
    async def search(
        self,
        query: str,
        top_k: int = 5,
        source_type: str | None = None,
    ) -> List[Dict[str, Any]]:
        """Search for similar documents."""
        # Generate query embedding
        query_embedding = await self.embedder.embed(query)
        
        # Build filter
        filter_expr = None
        if source_type:
            filter_expr = f"@source_type:{{{source_type}}}"
        
        # Create query
        vector_query = VectorQuery(
            vector=query_embedding,
            vector_field_name="embedding",
            return_fields=["content", "source", "source_type", "document_id", "chunk_index", "metadata"],
            num_results=top_k,
            filter_expression=filter_expr,
        )
        
        # Execute search
        results = await self._index.query(vector_query)
        
        # Format results
        formatted = []
        for result in results:
            formatted.append({
                "content": result.get("content"),
                "source": result.get("source"),
                "source_type": result.get("source_type"),
                "document_id": result.get("document_id"),
                "chunk_index": int(result.get("chunk_index", 0)),
                "metadata": json.loads(result.get("metadata", "{}")),
                "score": result.get("vector_distance", 0),
            })
        
        return formatted
    
    async def delete_document(self, document_id: str):
        """Delete all chunks for a document."""
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
            logger.info("document_deleted", document_id=document_id, chunks_deleted=len(keys_to_delete))
```

#### 5.3 Document Processor

```python
# src/rag/document_processor.py
from pathlib import Path
from typing import Dict, Any, List
from docling.document_converter import DocumentConverter
import structlog

logger = structlog.get_logger()


class DocumentProcessor:
    """Process documents using Docling."""
    
    SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".pptx", ".xlsx", ".html", ".md", ".txt"}
    
    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.converter = DocumentConverter()
    
    def _chunk_text(self, text: str) -> List[str]:
        """Split text into overlapping chunks."""
        if not text:
            return []
        
        chunks = []
        start = 0
        text_length = len(text)
        
        while start < text_length:
            end = start + self.chunk_size
            
            # Try to break at sentence boundary
            if end < text_length:
                # Look for sentence endings
                for boundary in [". ", ".\n", "! ", "!\n", "? ", "?\n"]:
                    last_boundary = text.rfind(boundary, start, end)
                    if last_boundary > start:
                        end = last_boundary + len(boundary)
                        break
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            start = end - self.chunk_overlap
            if start >= text_length:
                break
        
        return chunks
    
    async def process_file(self, file_path: Path) -> Dict[str, Any]:
        """Process a file and return chunks."""
        logger.info("processing_file", path=str(file_path))
        
        if file_path.suffix.lower() not in self.SUPPORTED_EXTENSIONS:
            raise ValueError(f"Unsupported file type: {file_path.suffix}")
        
        # Convert document
        result = self.converter.convert(str(file_path))
        
        # Extract text
        full_text = result.document.export_to_markdown()
        
        # Chunk text
        chunks = self._chunk_text(full_text)
        
        # Extract metadata
        metadata = {
            "filename": file_path.name,
            "extension": file_path.suffix.lower(),
            "page_count": len(result.document.pages) if hasattr(result.document, "pages") else None,
        }
        
        logger.info("file_processed", path=str(file_path), chunk_count=len(chunks))
        
        return {
            "chunks": chunks,
            "metadata": metadata,
            "full_text": full_text,
        }
    
    async def process_bytes(
        self,
        content: bytes,
        filename: str,
    ) -> Dict[str, Any]:
        """Process file content from bytes."""
        import tempfile
        
        suffix = Path(filename).suffix
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp.write(content)
            tmp_path = Path(tmp.name)
        
        try:
            result = await self.process_file(tmp_path)
            return result
        finally:
            tmp_path.unlink()
```

#### 5.4 Schema Indexer

```python
# src/rag/schema_indexer.py
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import structlog

from src.rag.redis_vector_store import RedisVectorStore

logger = structlog.get_logger()


class SchemaIndexer:
    """Index database schema into vector store for RAG-enhanced queries."""
    
    def __init__(self, vector_store: RedisVectorStore):
        self.vector_store = vector_store
    
    async def index_schema(self, db: AsyncSession):
        """Extract and index database schema information."""
        logger.info("indexing_database_schema")
        
        # Get all tables
        tables_query = text("""
            SELECT 
                t.TABLE_NAME,
                t.TABLE_TYPE
            FROM INFORMATION_SCHEMA.TABLES t
            WHERE t.TABLE_SCHEMA = 'dbo'
            AND t.TABLE_TYPE = 'BASE TABLE'
        """)
        
        result = await db.execute(tables_query)
        tables = result.fetchall()
        
        chunks = []
        for table in tables:
            table_name = table[0]
            
            # Get columns for this table
            columns_query = text("""
                SELECT 
                    c.COLUMN_NAME,
                    c.DATA_TYPE,
                    c.IS_NULLABLE,
                    c.CHARACTER_MAXIMUM_LENGTH,
                    ISNULL(ep.value, '') as DESCRIPTION
                FROM INFORMATION_SCHEMA.COLUMNS c
                LEFT JOIN sys.extended_properties ep 
                    ON ep.major_id = OBJECT_ID(c.TABLE_SCHEMA + '.' + c.TABLE_NAME)
                    AND ep.minor_id = COLUMNPROPERTY(OBJECT_ID(c.TABLE_SCHEMA + '.' + c.TABLE_NAME), c.COLUMN_NAME, 'ColumnId')
                    AND ep.name = 'MS_Description'
                WHERE c.TABLE_NAME = :table_name
                AND c.TABLE_SCHEMA = 'dbo'
                ORDER BY c.ORDINAL_POSITION
            """)
            
            cols_result = await db.execute(columns_query, {"table_name": table_name})
            columns = cols_result.fetchall()
            
            # Build schema description
            schema_text = f"Table: {table_name}\n"
            schema_text += "Columns:\n"
            for col in columns:
                col_name, data_type, nullable, max_len, desc = col
                schema_text += f"  - {col_name} ({data_type}"
                if max_len:
                    schema_text += f", max length: {max_len}"
                schema_text += f", nullable: {nullable})"
                if desc:
                    schema_text += f" - {desc}"
                schema_text += "\n"
            
            chunks.append(schema_text)
        
        # Get relationships
        fk_query = text("""
            SELECT 
                fk.name AS FK_NAME,
                tp.name AS PARENT_TABLE,
                cp.name AS PARENT_COLUMN,
                tr.name AS REFERENCED_TABLE,
                cr.name AS REFERENCED_COLUMN
            FROM sys.foreign_keys fk
            INNER JOIN sys.foreign_key_columns fkc ON fk.object_id = fkc.constraint_object_id
            INNER JOIN sys.tables tp ON fkc.parent_object_id = tp.object_id
            INNER JOIN sys.columns cp ON fkc.parent_object_id = cp.object_id AND fkc.parent_column_id = cp.column_id
            INNER JOIN sys.tables tr ON fkc.referenced_object_id = tr.object_id
            INNER JOIN sys.columns cr ON fkc.referenced_object_id = cr.object_id AND fkc.referenced_column_id = cr.column_id
        """)
        
        fk_result = await db.execute(fk_query)
        relationships = fk_result.fetchall()
        
        if relationships:
            rel_text = "Database Relationships:\n"
            for rel in relationships:
                fk_name, parent, parent_col, ref, ref_col = rel
                rel_text += f"  - {parent}.{parent_col} references {ref}.{ref_col}\n"
            chunks.append(rel_text)
        
        # Add to vector store
        await self.vector_store.add_document(
            document_id="schema",
            chunks=chunks,
            source="database_schema",
            source_type="schema",
            metadata={"table_count": len(tables), "relationship_count": len(relationships)},
        )
        
        logger.info("schema_indexed", tables=len(tables), relationships=len(relationships))
```

---

### Step 6: Dynamic MCP Server Management

```python
# src/mcp/dynamic_manager.py
import json
from pathlib import Path
from typing import Dict, List, Any
from pydantic import BaseModel
from pydantic_ai.mcp import MCPServerStdio, MCPServerStreamableHTTP
import structlog

logger = structlog.get_logger()


class MCPServerConfig(BaseModel):
    """Configuration for an MCP server."""
    id: str
    name: str
    description: str = ""
    type: str  # 'stdio' or 'http'
    command: str | None = None
    args: List[str] = []
    url: str | None = None
    env: Dict[str, str] = {}
    enabled: bool = True
    built_in: bool = False


class DynamicMCPManager:
    """Manage MCP servers dynamically from configuration."""
    
    DEFAULT_SERVERS = {
        "mssql": MCPServerConfig(
            id="mssql",
            name="MSSQL Server",
            description="SQL Server database access via MCP",
            type="stdio",
            command="node",
            args=["${MCP_MSSQL_PATH}"],
            env={
                "SERVER_NAME": "${SQL_SERVER_HOST}",
                "DATABASE_NAME": "${SQL_DATABASE_NAME}",
                "TRUST_SERVER_CERTIFICATE": "true",
            },
            enabled=True,
            built_in=True,
        ),
        "microsoft-learn": MCPServerConfig(
            id="microsoft-learn",
            name="Microsoft Learn Docs",
            description="Search and fetch Microsoft documentation",
            type="http",
            url="https://learn.microsoft.com/api/mcp",
            enabled=True,
            built_in=True,
        ),
        "powerbi-modeling": MCPServerConfig(
            id="powerbi-modeling",
            name="Power BI Modeling",
            description="Create and modify Power BI semantic models",
            type="stdio",
            command="${POWERBI_MCP_PATH}",
            args=["--start"],
            enabled=False,  # Disabled by default until user configures path
            built_in=True,
        ),
    }
    
    def __init__(self, config_path: str = "mcp_config.json"):
        self.config_path = Path(config_path)
        self.servers: Dict[str, MCPServerConfig] = {}
        self._active_servers: Dict[str, Any] = {}
    
    async def load_config(self):
        """Load configuration from file."""
        # Start with defaults
        self.servers = dict(self.DEFAULT_SERVERS)
        
        # Load user config if exists
        if self.config_path.exists():
            with open(self.config_path) as f:
                config = json.load(f)
            
            for server_id, server_config in config.get("mcpServers", {}).items():
                # Merge with defaults or add new
                self.servers[server_id] = MCPServerConfig(
                    id=server_id,
                    name=server_config.get("name", server_id),
                    description=server_config.get("description", ""),
                    type=server_config.get("type", "stdio"),
                    command=server_config.get("command"),
                    args=server_config.get("args", []),
                    url=server_config.get("url"),
                    env=server_config.get("env", {}),
                    enabled=server_config.get("enabled", True),
                    built_in=False,
                )
        
        logger.info("mcp_config_loaded", server_count=len(self.servers))
    
    async def save_config(self):
        """Save configuration to file."""
        config = {"mcpServers": {}}
        
        for server_id, server in self.servers.items():
            if not server.built_in:  # Only save user-added servers
                config["mcpServers"][server_id] = {
                    "name": server.name,
                    "description": server.description,
                    "type": server.type,
                    "command": server.command,
                    "args": server.args,
                    "url": server.url,
                    "env": server.env,
                    "enabled": server.enabled,
                }
        
        with open(self.config_path, "w") as f:
            json.dump(config, f, indent=2)
        
        logger.info("mcp_config_saved")
    
    def _expand_env_vars(self, value: str) -> str:
        """Expand environment variables in string."""
        import os
        import re
        
        def replace_var(match):
            var_name = match.group(1)
            return os.environ.get(var_name, match.group(0))
        
        return re.sub(r'\$\{([^}]+)\}', replace_var, value)
    
    def get_mcp_server(self, server_id: str) -> MCPServerStdio | MCPServerStreamableHTTP | None:
        """Get an MCP server instance."""
        if server_id not in self.servers:
            return None
        
        config = self.servers[server_id]
        if not config.enabled:
            return None
        
        if config.type == "stdio":
            # Expand environment variables
            command = self._expand_env_vars(config.command) if config.command else None
            args = [self._expand_env_vars(arg) for arg in config.args]
            env = {k: self._expand_env_vars(v) for k, v in config.env.items()}
            
            return MCPServerStdio(
                command=command,
                args=args,
                env=env,
                timeout=30,
            )
        
        elif config.type == "http":
            url = self._expand_env_vars(config.url) if config.url else None
            return MCPServerStreamableHTTP(url=url)
        
        return None
    
    def get_enabled_servers(self) -> List[MCPServerStdio | MCPServerStreamableHTTP]:
        """Get all enabled MCP servers."""
        servers = []
        for server_id in self.servers:
            server = self.get_mcp_server(server_id)
            if server:
                servers.append(server)
        return servers
    
    def get_servers_by_ids(self, server_ids: List[str]) -> List[MCPServerStdio | MCPServerStreamableHTTP]:
        """Get specific MCP servers by ID."""
        servers = []
        for server_id in server_ids:
            server = self.get_mcp_server(server_id)
            if server:
                servers.append(server)
        return servers
    
    def list_servers(self) -> List[MCPServerConfig]:
        """List all configured servers."""
        return list(self.servers.values())
    
    async def add_server(self, config: MCPServerConfig):
        """Add a new MCP server."""
        self.servers[config.id] = config
        await self.save_config()
        logger.info("mcp_server_added", server_id=config.id)
    
    async def update_server(self, server_id: str, updates: Dict[str, Any]):
        """Update an existing server."""
        if server_id not in self.servers:
            raise ValueError(f"Server not found: {server_id}")
        
        server = self.servers[server_id]
        for key, value in updates.items():
            if hasattr(server, key):
                setattr(server, key, value)
        
        await self.save_config()
        logger.info("mcp_server_updated", server_id=server_id)
    
    async def remove_server(self, server_id: str):
        """Remove an MCP server."""
        if server_id not in self.servers:
            raise ValueError(f"Server not found: {server_id}")
        
        if self.servers[server_id].built_in:
            raise ValueError("Cannot remove built-in server")
        
        del self.servers[server_id]
        await self.save_config()
        logger.info("mcp_server_removed", server_id=server_id)
    
    async def shutdown(self):
        """Shutdown all active servers."""
        for server in self._active_servers.values():
            try:
                await server.__aexit__(None, None, None)
            except Exception as e:
                logger.error("server_shutdown_error", error=str(e))
        self._active_servers.clear()
```

---

### Step 7: Document API Routes

```python
# src/api/routes/documents.py
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import List
from datetime import datetime
import aiofiles
from pathlib import Path
import uuid

from src.api.deps import get_db, get_vector_store
from src.api.models.database import Document
from src.rag.document_processor import DocumentProcessor
from src.rag.redis_vector_store import RedisVectorStore
from src.utils.config import get_settings

router = APIRouter()


class DocumentResponse(BaseModel):
    id: int
    filename: str
    original_filename: str
    mime_type: str | None
    file_size: int
    chunk_count: int | None
    processing_status: str
    error_message: str | None
    created_at: datetime
    processed_at: datetime | None
    
    class Config:
        from_attributes = True


class DocumentListResponse(BaseModel):
    documents: List[DocumentResponse]
    total: int


@router.get("", response_model=DocumentListResponse)
async def list_documents(
    skip: int = 0,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
):
    """List all documents."""
    # Get total count
    count_query = select(Document)
    result = await db.execute(count_query)
    total = len(result.scalars().all())
    
    # Get paginated results
    query = select(Document).offset(skip).limit(limit).order_by(Document.created_at.desc())
    result = await db.execute(query)
    documents = result.scalars().all()
    
    return DocumentListResponse(
        documents=[DocumentResponse.model_validate(doc) for doc in documents],
        total=total,
    )


@router.post("", response_model=DocumentResponse)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    vector_store: RedisVectorStore = Depends(get_vector_store),
):
    """Upload a new document."""
    settings = get_settings()
    
    # Validate file size
    content = await file.read()
    file_size = len(content)
    max_size = settings.max_upload_size_mb * 1024 * 1024
    
    if file_size > max_size:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size is {settings.max_upload_size_mb}MB",
        )
    
    # Validate file type
    processor = DocumentProcessor(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
    )
    suffix = Path(file.filename).suffix.lower()
    if suffix not in processor.SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type. Supported: {processor.SUPPORTED_EXTENSIONS}",
        )
    
    # Save file
    filename = f"{uuid.uuid4()}{suffix}"
    upload_path = Path(settings.upload_dir) / filename
    upload_path.parent.mkdir(parents=True, exist_ok=True)
    
    async with aiofiles.open(upload_path, "wb") as f:
        await f.write(content)
    
    # Create database record
    document = Document(
        filename=filename,
        original_filename=file.filename,
        mime_type=file.content_type,
        file_size=file_size,
        processing_status="pending",
    )
    db.add(document)
    await db.commit()
    await db.refresh(document)
    
    # Process in background
    background_tasks.add_task(
        process_document,
        document.id,
        upload_path,
        vector_store,
        processor,
    )
    
    return DocumentResponse.model_validate(document)


async def process_document(
    document_id: int,
    file_path: Path,
    vector_store: RedisVectorStore,
    processor: DocumentProcessor,
):
    """Background task to process document."""
    from src.api.deps import _session_factory
    
    async with _session_factory() as db:
        try:
            # Update status
            doc = await db.get(Document, document_id)
            doc.processing_status = "processing"
            await db.commit()
            
            # Process file
            result = await processor.process_file(file_path)
            
            # Add to vector store
            await vector_store.add_document(
                document_id=str(document_id),
                chunks=result["chunks"],
                source=doc.original_filename,
                source_type="document",
                metadata=result["metadata"],
            )
            
            # Update record
            doc.chunk_count = len(result["chunks"])
            doc.processing_status = "completed"
            doc.processed_at = datetime.utcnow()
            await db.commit()
            
        except Exception as e:
            doc = await db.get(Document, document_id)
            doc.processing_status = "failed"
            doc.error_message = str(e)
            await db.commit()


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get a specific document."""
    document = await db.get(Document, document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    return DocumentResponse.model_validate(document)


@router.delete("/{document_id}")
async def delete_document(
    document_id: int,
    db: AsyncSession = Depends(get_db),
    vector_store: RedisVectorStore = Depends(get_vector_store),
):
    """Delete a document."""
    document = await db.get(Document, document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Delete from vector store
    await vector_store.delete_document(str(document_id))
    
    # Delete file
    settings = get_settings()
    file_path = Path(settings.upload_dir) / document.filename
    if file_path.exists():
        file_path.unlink()
    
    # Delete from database
    await db.delete(document)
    await db.commit()
    
    return {"status": "deleted", "document_id": document_id}
```

---

## File Structure After Phase 2.1

```
local-llm-research-agent/
├── alembic/
│   ├── env.py
│   ├── versions/
│   │   └── 001_add_phase2_tables.py
│   └── alembic.ini
├── docker/
│   ├── docker-compose.yml       # Updated with Redis Stack
│   ├── Dockerfile.api           # New API container
│   └── init/
├── data/
│   ├── uploads/                 # Document storage
│   └── models/                  # Model cache
├── src/
│   ├── api/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI application
│   │   ├── deps.py              # Dependencies
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   └── database.py      # SQLAlchemy models
│   │   └── routes/
│   │       ├── __init__.py
│   │       ├── health.py
│   │       ├── documents.py
│   │       ├── conversations.py
│   │       ├── queries.py
│   │       ├── dashboards.py
│   │       ├── mcp_servers.py
│   │       ├── settings.py
│   │       └── agent.py
│   ├── rag/
│   │   ├── __init__.py
│   │   ├── embedder.py          # Ollama embeddings
│   │   ├── redis_vector_store.py
│   │   ├── document_processor.py
│   │   └── schema_indexer.py
│   ├── mcp/
│   │   ├── __init__.py
│   │   ├── client.py            # Existing
│   │   ├── mssql_config.py      # Existing
│   │   ├── server_manager.py    # Existing
│   │   └── dynamic_manager.py   # New dynamic MCP loader
│   └── utils/
│       └── config.py            # Updated with new settings
└── mcp_config.json              # MCP server configuration
```

---

## Environment Variables

Add to `.env`:

```bash
# Redis
REDIS_URL=redis://localhost:6379

# Embeddings
EMBEDDING_MODEL=nomic-embed-text

# Storage
UPLOAD_DIR=./data/uploads
MAX_UPLOAD_SIZE_MB=100

# RAG
CHUNK_SIZE=500
CHUNK_OVERLAP=50
RAG_TOP_K=5

# API
API_HOST=0.0.0.0
API_PORT=8000
```

---

## Validation Checkpoints

1. **Docker services start:**
   ```bash
   cd docker
   docker compose up -d
   docker compose ps  # All services healthy
   ```

2. **FastAPI starts:**
   ```bash
   uv run uvicorn src.api.main:app --reload
   # Visit http://localhost:8000/docs
   ```

3. **Health check passes:**
   ```bash
   curl http://localhost:8000/api/health
   # Should return all services healthy
   ```

4. **Document upload works:**
   ```bash
   curl -X POST http://localhost:8000/api/documents \
     -F "file=@test.pdf"
   ```

5. **Vectors in Redis:**
   ```bash
   # Visit http://localhost:8001 (RedisInsight)
   # Check for doc:* keys
   ```

6. **Existing interfaces work:**
   ```bash
   uv run python -m src.cli.chat
   uv run streamlit run src/ui/streamlit_app.py
   ```

---

## Notes for Implementation

- **DO NOT modify** existing files in `src/agent/`, `src/cli/`, `src/ui/`
- Create all new files in `src/api/`, `src/rag/`
- **Extend** `src/mcp/` with `dynamic_manager.py`, don't replace existing files
- **Extend** `src/utils/config.py` with new settings, keep existing
- Test existing CLI and Streamlit after each major change
- Use `uv run alembic upgrade head` to apply migrations
- Pull embedding model first: `ollama pull nomic-embed-text`
