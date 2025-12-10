# PRP: Phase 2 - RAG + React Full-Stack UI with Dynamic MCP Server Configuration

## Goal

Implement **Retrieval-Augmented Generation (RAG)** capabilities for searching project documentation and database schema descriptions, with a modern **React-based full-stack UI** as the third deployment option (alongside CLI and Streamlit). Enable dynamic configuration of MCP servers via the UI so users can add, remove, and switch between multiple MCP servers beyond the built-in SQL Server integration.

## Why

- **Enhanced Context**: RAG allows the agent to reference project documentation, coding examples, and schema descriptions for more accurate responses
- **Document Intelligence**: Docling enables processing of various document formats (PDF, DOCX, etc.) into the knowledge base
- **Modern UI**: React provides a production-ready, customizable interface with better UX than Streamlit
- **MCP Flexibility**: Dynamic MCP server configuration allows users to extend agent capabilities without code changes
- **Enterprise Ready**: Branding, theming, and configuration management make this suitable for organizational deployment
- **Local-First**: All components (vector store, document processing, inference) run locally for complete privacy

## What

A full-stack enhancement to the existing local LLM research agent with:

### Success Criteria

- [ ] SQL Server vector store running in Docker with configurable storage/volume mapping
- [ ] RAG search works for project documentation AND database schema descriptions
- [ ] Docling processes uploaded documents (PDF, DOCX, TXT, MD) into the knowledge base
- [ ] React UI includes all required pages (Document Management, Settings, KB Management, Agent Chat)
- [ ] Dynamic MCP server configuration via UI (add, edit, remove, enable/disable servers)
- [ ] Agent can use multiple MCP servers selected by user in the UI
- [ ] Dark/light theme toggle with customization options (colors, fonts)
- [ ] Corporate branding support (logos, color palettes)
- [ ] Playwright tests confirm UI functionality and visual appeal
- [ ] Unit, integration, and UI tests pass with no regression
- [ ] Existing CLI and Streamlit interfaces remain functional
- [ ] Documentation updated for all new features

### Core Features

1. **RAG Pipeline**
   - SQL Server as vector store (pgvector alternative for MSSQL)
   - Semantic search over documents and schema descriptions
   - Chunking and embedding pipeline
   - Hybrid search (semantic + keyword)

2. **Document Processing**
   - Docling integration for document ingestion
   - Support for PDF, DOCX, TXT, MD, HTML
   - Automatic chunking and metadata extraction
   - File upload via web interface

3. **Dynamic MCP Server Management**
   - Add/edit/remove MCP servers via UI
   - Enable/disable servers without removal
   - Server health checking and status display
   - Persist configuration to database/config file

4. **React Full-Stack UI**
   - Document Management page
   - Configuration & Settings page
   - Knowledge Base Management page
   - Agent Interaction page with MCP server selection
   - Admin dashboard

5. **Theming & Branding**
   - Dark theme (default) / Light theme toggle
   - Customizable colors, fonts, layouts
   - Corporate branding (logo upload, color palette)

## All Needed Context

### Documentation & References

- url: https://github.com/DS4SD/docling
  why: Docling documentation - document processing and conversion library

- url: https://github.com/Azure-Samples/SQL-AI-samples/tree/main/MssqlMcp
  why: MSSQL MCP Server reference - existing integration to extend

- url: https://modelcontextprotocol.io/docs/concepts/servers
  why: MCP Server specification - for dynamic server configuration

- url: https://ai.pydantic.dev/mcp/client/
  why: Pydantic AI MCP client - MCPServerStdio and server management

- url: https://react.dev/
  why: React documentation - UI framework

- url: https://tailwindcss.com/docs
  why: Tailwind CSS - styling framework for React UI

- url: https://tanstack.com/query/latest
  why: TanStack Query - data fetching and caching for React

- url: https://fastapi.tiangolo.com/
  why: FastAPI - backend API for React frontend

- url: https://playwright.dev/docs/intro
  why: Playwright - E2E testing and UI validation

- url: https://github.com/coleam00/archon
  why: Archon KB reference - coding examples lookup pattern

### Technology Versions

```toml
# Additional dependencies for Phase 2 (add to pyproject.toml)
[project.dependencies]
# Existing deps...
fastapi = ">=0.115.0"
uvicorn = { version = ">=0.32.0", extras = ["standard"] }
sqlalchemy = ">=2.0.0"
alembic = ">=1.14.0"
docling = ">=2.15.0"
sentence-transformers = ">=3.3.0"
numpy = ">=1.26.0"
faiss-cpu = ">=1.9.0"  # For local vector similarity (fallback)
python-multipart = ">=0.0.12"  # File uploads
aiofiles = ">=24.1.0"
websockets = ">=14.0"

[project.optional-dependencies]
test = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.23.0",
    "pytest-cov>=4.0.0",
    "httpx>=0.27.0",
    "playwright>=1.49.0",
]
```

```json
// package.json for React frontend
{
  "name": "local-llm-ui",
  "version": "0.1.0",
  "dependencies": {
    "react": "^18.3.0",
    "react-dom": "^18.3.0",
    "react-router-dom": "^7.0.0",
    "@tanstack/react-query": "^5.62.0",
    "tailwindcss": "^3.4.0",
    "lucide-react": "^0.468.0",
    "zustand": "^5.0.0",
    "react-dropzone": "^14.3.0",
    "react-hot-toast": "^2.4.0",
    "@radix-ui/react-dialog": "^1.1.0",
    "@radix-ui/react-dropdown-menu": "^2.1.0",
    "@radix-ui/react-switch": "^1.1.0",
    "@radix-ui/react-tabs": "^1.1.0"
  },
  "devDependencies": {
    "vite": "^6.0.0",
    "@vitejs/plugin-react": "^4.3.0",
    "typescript": "^5.7.0",
    "@types/react": "^18.3.0",
    "@playwright/test": "^1.49.0"
  }
}
```

### Key Patterns to Follow

#### 1. FastAPI Backend Structure

```python
# src/api/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.api.routes import documents, settings, knowledge_base, agent, mcp_servers

app = FastAPI(title="Local LLM Research Agent API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(documents.router, prefix="/api/documents", tags=["documents"])
app.include_router(settings.router, prefix="/api/settings", tags=["settings"])
app.include_router(knowledge_base.router, prefix="/api/kb", tags=["knowledge-base"])
app.include_router(agent.router, prefix="/api/agent", tags=["agent"])
app.include_router(mcp_servers.router, prefix="/api/mcp-servers", tags=["mcp-servers"])
```

#### 2. Dynamic MCP Server Configuration

```python
# src/mcp/dynamic_manager.py
from pydantic import BaseModel
from pydantic_ai.mcp import MCPServerStdio
from typing import Optional
import json

class MCPServerConfig(BaseModel):
    """Configuration for a dynamic MCP server."""
    id: str
    name: str
    description: str
    command: str
    args: list[str]
    env: dict[str, str] = {}
    enabled: bool = True
    timeout: int = 30

class DynamicMCPManager:
    """Manages multiple MCP servers with runtime configuration."""
    
    def __init__(self, config_path: str = "mcp_servers.json"):
        self.config_path = config_path
        self.servers: dict[str, MCPServerConfig] = {}
        self.active_servers: dict[str, MCPServerStdio] = {}
        self.load_config()
    
    def load_config(self) -> None:
        """Load MCP server configurations from file."""
        try:
            with open(self.config_path) as f:
                data = json.load(f)
                for server_data in data.get("servers", []):
                    config = MCPServerConfig(**server_data)
                    self.servers[config.id] = config
        except FileNotFoundError:
            self.servers = {}
    
    def save_config(self) -> None:
        """Persist MCP server configurations to file."""
        data = {"servers": [s.model_dump() for s in self.servers.values()]}
        with open(self.config_path, "w") as f:
            json.dump(data, f, indent=2)
    
    def add_server(self, config: MCPServerConfig) -> None:
        """Add a new MCP server configuration."""
        self.servers[config.id] = config
        self.save_config()
    
    def remove_server(self, server_id: str) -> None:
        """Remove an MCP server configuration."""
        if server_id in self.servers:
            del self.servers[server_id]
            self.save_config()
    
    def get_enabled_servers(self) -> list[MCPServerStdio]:
        """Get MCPServerStdio instances for all enabled servers."""
        result = []
        for config in self.servers.values():
            if config.enabled:
                server = MCPServerStdio(
                    command=config.command,
                    args=config.args,
                    env=config.env,
                    timeout=config.timeout
                )
                result.append(server)
        return result
    
    def get_server_by_ids(self, server_ids: list[str]) -> list[MCPServerStdio]:
        """Get MCPServerStdio instances for specific server IDs."""
        result = []
        for server_id in server_ids:
            if server_id in self.servers:
                config = self.servers[server_id]
                server = MCPServerStdio(
                    command=config.command,
                    args=config.args,
                    env=config.env,
                    timeout=config.timeout
                )
                result.append(server)
        return result
```

#### 3. RAG Pipeline with SQL Server Vector Store

```python
# src/rag/vector_store.py
from sentence_transformers import SentenceTransformer
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import numpy as np

class SQLServerVectorStore:
    """Vector store using SQL Server with vector similarity."""
    
    def __init__(self, connection_string: str, embedding_model: str = "all-MiniLM-L6-v2"):
        self.engine = create_engine(connection_string)
        self.Session = sessionmaker(bind=self.engine)
        self.embedder = SentenceTransformer(embedding_model)
        self._init_tables()
    
    def _init_tables(self) -> None:
        """Initialize vector store tables in SQL Server."""
        with self.engine.connect() as conn:
            conn.execute(text("""
                IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'document_chunks')
                CREATE TABLE document_chunks (
                    id INT IDENTITY(1,1) PRIMARY KEY,
                    document_id INT NOT NULL,
                    chunk_index INT NOT NULL,
                    content NVARCHAR(MAX) NOT NULL,
                    embedding VARBINARY(MAX) NOT NULL,
                    metadata NVARCHAR(MAX),
                    created_at DATETIME2 DEFAULT GETUTCDATE()
                )
            """))
            conn.commit()
    
    def add_document(self, document_id: int, chunks: list[str], metadata: dict = None) -> None:
        """Add document chunks with embeddings to the vector store."""
        embeddings = self.embedder.encode(chunks)
        
        with self.Session() as session:
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                embedding_bytes = embedding.astype(np.float32).tobytes()
                session.execute(text("""
                    INSERT INTO document_chunks (document_id, chunk_index, content, embedding, metadata)
                    VALUES (:doc_id, :idx, :content, :embedding, :metadata)
                """), {
                    "doc_id": document_id,
                    "idx": i,
                    "content": chunk,
                    "embedding": embedding_bytes,
                    "metadata": json.dumps(metadata) if metadata else None
                })
            session.commit()
    
    def search(self, query: str, top_k: int = 5) -> list[dict]:
        """Search for similar chunks using cosine similarity."""
        query_embedding = self.embedder.encode([query])[0]
        
        # Fetch all embeddings and compute similarity (for smaller datasets)
        # For production, consider SQL Server 2022+ vector features or external vector DB
        with self.Session() as session:
            results = session.execute(text("""
                SELECT id, document_id, chunk_index, content, embedding, metadata
                FROM document_chunks
            """)).fetchall()
        
        similarities = []
        for row in results:
            stored_embedding = np.frombuffer(row.embedding, dtype=np.float32)
            similarity = np.dot(query_embedding, stored_embedding) / (
                np.linalg.norm(query_embedding) * np.linalg.norm(stored_embedding)
            )
            similarities.append((similarity, row))
        
        similarities.sort(reverse=True, key=lambda x: x[0])
        
        return [
            {
                "id": row.id,
                "document_id": row.document_id,
                "content": row.content,
                "score": float(score),
                "metadata": json.loads(row.metadata) if row.metadata else {}
            }
            for score, row in similarities[:top_k]
        ]
```

#### 4. Docling Document Processing

```python
# src/rag/document_processor.py
from docling.document_converter import DocumentConverter
from docling.datamodel.base_models import DocumentStream
from pathlib import Path
import hashlib

class DocumentProcessor:
    """Process documents using Docling for RAG ingestion."""
    
    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50):
        self.converter = DocumentConverter()
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
    
    def process_file(self, file_path: Path) -> dict:
        """Process a document file and return chunks with metadata."""
        result = self.converter.convert(file_path)
        
        # Extract text content
        full_text = result.document.export_to_markdown()
        
        # Generate chunks
        chunks = self._chunk_text(full_text)
        
        # Extract metadata
        metadata = {
            "filename": file_path.name,
            "file_type": file_path.suffix,
            "file_hash": self._compute_hash(file_path),
            "num_pages": getattr(result.document, "num_pages", None),
            "title": getattr(result.document, "title", file_path.stem),
        }
        
        return {
            "chunks": chunks,
            "metadata": metadata,
            "full_text": full_text
        }
    
    def process_stream(self, file_stream: bytes, filename: str) -> dict:
        """Process a document from bytes stream."""
        stream = DocumentStream(name=filename, stream=file_stream)
        result = self.converter.convert(stream)
        
        full_text = result.document.export_to_markdown()
        chunks = self._chunk_text(full_text)
        
        metadata = {
            "filename": filename,
            "file_type": Path(filename).suffix,
            "title": Path(filename).stem,
        }
        
        return {
            "chunks": chunks,
            "metadata": metadata,
            "full_text": full_text
        }
    
    def _chunk_text(self, text: str) -> list[str]:
        """Split text into overlapping chunks."""
        chunks = []
        start = 0
        while start < len(text):
            end = start + self.chunk_size
            chunk = text[start:end]
            
            # Try to break at sentence boundary
            if end < len(text):
                last_period = chunk.rfind(". ")
                if last_period > self.chunk_size // 2:
                    end = start + last_period + 1
                    chunk = text[start:end]
            
            chunks.append(chunk.strip())
            start = end - self.chunk_overlap
        
        return [c for c in chunks if c]  # Filter empty chunks
    
    def _compute_hash(self, file_path: Path) -> str:
        """Compute SHA256 hash of file."""
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for block in iter(lambda: f.read(4096), b""):
                sha256.update(block)
        return sha256.hexdigest()
```

#### 5. React Component Pattern - MCP Server Manager

```tsx
// frontend/src/components/MCPServerManager.tsx
import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Plus, Trash2, Settings, Power, PowerOff } from 'lucide-react';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Switch } from '@/components/ui/switch';
import toast from 'react-hot-toast';

interface MCPServer {
  id: string;
  name: string;
  description: string;
  command: string;
  args: string[];
  env: Record<string, string>;
  enabled: boolean;
  timeout: number;
}

export function MCPServerManager() {
  const [isAddDialogOpen, setIsAddDialogOpen] = useState(false);
  const queryClient = useQueryClient();

  const { data: servers, isLoading } = useQuery<MCPServer[]>({
    queryKey: ['mcp-servers'],
    queryFn: () => fetch('/api/mcp-servers').then(r => r.json()),
  });

  const addServerMutation = useMutation({
    mutationFn: (server: Omit<MCPServer, 'id'>) =>
      fetch('/api/mcp-servers', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(server),
      }).then(r => r.json()),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['mcp-servers'] });
      toast.success('MCP Server added successfully');
      setIsAddDialogOpen(false);
    },
  });

  const toggleServerMutation = useMutation({
    mutationFn: ({ id, enabled }: { id: string; enabled: boolean }) =>
      fetch(`/api/mcp-servers/${id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ enabled }),
      }).then(r => r.json()),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['mcp-servers'] });
    },
  });

  const deleteServerMutation = useMutation({
    mutationFn: (id: string) =>
      fetch(`/api/mcp-servers/${id}`, { method: 'DELETE' }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['mcp-servers'] });
      toast.success('MCP Server removed');
    },
  });

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h2 className="text-xl font-semibold">MCP Servers</h2>
        <Button onClick={() => setIsAddDialogOpen(true)}>
          <Plus className="w-4 h-4 mr-2" /> Add Server
        </Button>
      </div>

      <div className="grid gap-4">
        {servers?.map((server) => (
          <div
            key={server.id}
            className="p-4 border rounded-lg bg-card flex items-center justify-between"
          >
            <div className="flex items-center gap-4">
              {server.enabled ? (
                <Power className="w-5 h-5 text-green-500" />
              ) : (
                <PowerOff className="w-5 h-5 text-gray-400" />
              )}
              <div>
                <h3 className="font-medium">{server.name}</h3>
                <p className="text-sm text-muted-foreground">{server.description}</p>
                <code className="text-xs text-muted-foreground">
                  {server.command} {server.args.join(' ')}
                </code>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Switch
                checked={server.enabled}
                onCheckedChange={(enabled) =>
                  toggleServerMutation.mutate({ id: server.id, enabled })
                }
              />
              <Button
                variant="ghost"
                size="icon"
                onClick={() => deleteServerMutation.mutate(server.id)}
              >
                <Trash2 className="w-4 h-4 text-destructive" />
              </Button>
            </div>
          </div>
        ))}
      </div>

      <AddServerDialog
        open={isAddDialogOpen}
        onOpenChange={setIsAddDialogOpen}
        onSubmit={(server) => addServerMutation.mutate(server)}
      />
    </div>
  );
}
```

#### 6. Theme System

```tsx
// frontend/src/contexts/ThemeContext.tsx
import { createContext, useContext, useEffect, useState } from 'react';

interface ThemeConfig {
  mode: 'dark' | 'light';
  primaryColor: string;
  accentColor: string;
  fontFamily: string;
  brandLogo?: string;
  brandName?: string;
}

const defaultTheme: ThemeConfig = {
  mode: 'dark',
  primaryColor: '#3b82f6',
  accentColor: '#8b5cf6',
  fontFamily: 'Inter, sans-serif',
};

const ThemeContext = createContext<{
  theme: ThemeConfig;
  setTheme: (theme: Partial<ThemeConfig>) => void;
  toggleMode: () => void;
}>({
  theme: defaultTheme,
  setTheme: () => {},
  toggleMode: () => {},
});

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const [theme, setThemeState] = useState<ThemeConfig>(() => {
    const saved = localStorage.getItem('theme');
    return saved ? JSON.parse(saved) : defaultTheme;
  });

  useEffect(() => {
    localStorage.setItem('theme', JSON.stringify(theme));
    document.documentElement.classList.toggle('dark', theme.mode === 'dark');
    document.documentElement.style.setProperty('--primary', theme.primaryColor);
    document.documentElement.style.setProperty('--accent', theme.accentColor);
    document.documentElement.style.setProperty('--font-family', theme.fontFamily);
  }, [theme]);

  const setTheme = (updates: Partial<ThemeConfig>) => {
    setThemeState((prev) => ({ ...prev, ...updates }));
  };

  const toggleMode = () => {
    setThemeState((prev) => ({
      ...prev,
      mode: prev.mode === 'dark' ? 'light' : 'dark',
    }));
  };

  return (
    <ThemeContext.Provider value={{ theme, setTheme, toggleMode }}>
      {children}
    </ThemeContext.Provider>
  );
}

export const useTheme = () => useContext(ThemeContext);
```

### MCP Server Presets

Common MCP servers users might want to add:

| Server | Command | Args | Purpose |
|--------|---------|------|---------|
| Playwright | `npx` | `["@anthropic/mcp-server-playwright"]` | Browser automation, UI testing |
| Filesystem | `npx` | `["@anthropic/mcp-server-filesystem", "/path"]` | File system access |
| GitHub | `npx` | `["@anthropic/mcp-server-github"]` | GitHub API access |
| Brave Search | `npx` | `["@anthropic/mcp-server-brave-search"]` | Web search |
| Memory | `npx` | `["@anthropic/mcp-server-memory"]` | Persistent memory |

## Implementation Plan

### Phase 2.1: Backend Infrastructure

**Files to create:**
- `src/api/__init__.py` - API package init
- `src/api/main.py` - FastAPI application
- `src/api/routes/documents.py` - Document upload/management endpoints
- `src/api/routes/settings.py` - Configuration endpoints
- `src/api/routes/knowledge_base.py` - KB management endpoints
- `src/api/routes/agent.py` - Agent interaction endpoints (WebSocket)
- `src/api/routes/mcp_servers.py` - MCP server CRUD endpoints
- `src/api/models/` - API request/response models
- `src/api/deps.py` - Dependency injection

**Database migrations:**
- `alembic/versions/001_create_documents_table.py`
- `alembic/versions/002_create_kb_tables.py`
- `alembic/versions/003_create_mcp_servers_table.py`
- `alembic/versions/004_create_settings_table.py`

### Phase 2.2: RAG Pipeline

**Files to create:**
- `src/rag/__init__.py` - RAG package init
- `src/rag/vector_store.py` - SQL Server vector store implementation
- `src/rag/document_processor.py` - Docling integration
- `src/rag/chunker.py` - Text chunking strategies
- `src/rag/embedder.py` - Embedding model wrapper
- `src/rag/retriever.py` - Hybrid retrieval (semantic + keyword)
- `src/rag/schema_indexer.py` - Database schema description indexer

**Docker updates:**
- `docker/docker-compose.yml` - Add volume mappings, embedding model cache

### Phase 2.3: Dynamic MCP Server Management

**Files to create:**
- `src/mcp/dynamic_manager.py` - Runtime MCP server management
- `src/mcp/server_registry.py` - Server persistence and lookup
- `src/mcp/health_checker.py` - Server health monitoring
- `src/mcp/presets.py` - Common MCP server presets
- `mcp_servers.json` - Default server configurations

**Files to update:**
- `src/agent/research_agent.py` - Support multiple/dynamic MCP servers

### Phase 2.4: React Frontend Setup

**Files to create:**
```
frontend/
├── package.json
├── vite.config.ts
├── tsconfig.json
├── tailwind.config.js
├── postcss.config.js
├── index.html
├── src/
│   ├── main.tsx
│   ├── App.tsx
│   ├── index.css
│   ├── api/
│   │   ├── client.ts
│   │   ├── documents.ts
│   │   ├── settings.ts
│   │   ├── kb.ts
│   │   ├── agent.ts
│   │   └── mcp-servers.ts
│   ├── components/
│   │   ├── ui/ (shadcn/ui components)
│   │   ├── layout/
│   │   │   ├── Sidebar.tsx
│   │   │   ├── Header.tsx
│   │   │   └── Layout.tsx
│   │   ├── documents/
│   │   │   ├── DocumentList.tsx
│   │   │   ├── DocumentUpload.tsx
│   │   │   └── DocumentViewer.tsx
│   │   ├── kb/
│   │   │   ├── KBEntryList.tsx
│   │   │   ├── KBEntryEditor.tsx
│   │   │   └── KBSearch.tsx
│   │   ├── agent/
│   │   │   ├── ChatInterface.tsx
│   │   │   ├── MessageList.tsx
│   │   │   ├── MCPServerSelector.tsx
│   │   │   └── AgentStatus.tsx
│   │   ├── settings/
│   │   │   ├── GeneralSettings.tsx
│   │   │   ├── StorageSettings.tsx
│   │   │   ├── ThemeSettings.tsx
│   │   │   └── BrandingSettings.tsx
│   │   └── mcp/
│   │       ├── MCPServerManager.tsx
│   │       ├── MCPServerForm.tsx
│   │       └── MCPServerPresets.tsx
│   ├── pages/
│   │   ├── Dashboard.tsx
│   │   ├── Documents.tsx
│   │   ├── KnowledgeBase.tsx
│   │   ├── Agent.tsx
│   │   └── Settings.tsx
│   ├── contexts/
│   │   ├── ThemeContext.tsx
│   │   └── AuthContext.tsx (future)
│   ├── hooks/
│   │   ├── useDocuments.ts
│   │   ├── useKB.ts
│   │   ├── useAgent.ts
│   │   ├── useMCPServers.ts
│   │   └── useSettings.ts
│   └── lib/
│       ├── utils.ts
│       └── constants.ts
```

### Phase 2.5: UI Implementation

**Pages to implement:**
1. Dashboard - Overview, quick actions, system status
2. Documents - Upload, list, view, delete documents
3. Knowledge Base - View, search, edit KB entries
4. Agent - Chat interface with MCP server selection
5. Settings - All configuration options

### Phase 2.6: Testing & Documentation

**Test files to create:**
- `tests/api/test_documents.py`
- `tests/api/test_mcp_servers.py`
- `tests/api/test_agent.py`
- `tests/rag/test_vector_store.py`
- `tests/rag/test_document_processor.py`
- `tests/mcp/test_dynamic_manager.py`
- `frontend/e2e/documents.spec.ts` (Playwright)
- `frontend/e2e/agent.spec.ts` (Playwright)
- `frontend/e2e/mcp-servers.spec.ts` (Playwright)
- `frontend/e2e/visual.spec.ts` (Playwright visual regression)

**Documentation updates:**
- `README.md` - Add Phase 2 features
- `docs/RAG.md` - RAG pipeline documentation
- `docs/MCP-SERVERS.md` - Dynamic MCP server guide
- `docs/REACT-UI.md` - Frontend documentation
- `docs/API.md` - API reference

## File-by-File Implementation Order

### Backend (Python)
1. `src/api/main.py` - FastAPI app setup
2. `src/api/deps.py` - Dependencies
3. `src/rag/embedder.py` - Embedding wrapper
4. `src/rag/vector_store.py` - Vector store
5. `src/rag/document_processor.py` - Docling integration
6. `src/rag/retriever.py` - RAG retrieval
7. `src/mcp/dynamic_manager.py` - MCP management
8. `src/api/routes/mcp_servers.py` - MCP CRUD API
9. `src/api/routes/documents.py` - Document API
10. `src/api/routes/knowledge_base.py` - KB API
11. `src/api/routes/agent.py` - Agent WebSocket API
12. `src/api/routes/settings.py` - Settings API
13. Database migrations

### Frontend (React)
14. `frontend/` - Vite + React setup
15. `src/api/client.ts` - API client
16. `src/contexts/ThemeContext.tsx` - Theme system
17. `src/components/layout/*` - Layout components
18. `src/components/ui/*` - UI primitives
19. `src/pages/Dashboard.tsx`
20. `src/pages/Documents.tsx` + components
21. `src/pages/KnowledgeBase.tsx` + components
22. `src/components/mcp/MCPServerManager.tsx`
23. `src/pages/Agent.tsx` + chat components
24. `src/pages/Settings.tsx` + setting components
25. Playwright E2E tests

### Docker & Config
26. Update `docker/docker-compose.yml`
27. `mcp_servers.json` - Default config
28. Documentation files

## Validation Checkpoints

After each sub-phase, verify:

1. **Phase 2.1**: `uvicorn src.api.main:app` starts, `/docs` shows Swagger UI
2. **Phase 2.2**: Can upload PDF, chunks stored in SQL Server, search returns results
3. **Phase 2.3**: Can add MCP server via API, agent uses newly added server
4. **Phase 2.4**: `npm run dev` starts React app, connects to backend
5. **Phase 2.5**: All pages render, dark/light theme works, branding applies
6. **Phase 2.6**: All tests pass, Playwright visual tests pass

## Out of Scope (Future Enhancements)

- User authentication and multi-tenancy
- Role-based access control (RBAC)
- Cloud deployment (Azure, AWS)
- Model fine-tuning interface
- Conversation history persistence
- Real-time collaboration
- Mobile-responsive design (stretch goal for this phase)
- Advanced caching layer (Redis)

## Notes for Implementation

1. **IMPORTANT**: Keep existing CLI and Streamlit interfaces working - test after each change
2. **IMPORTANT**: Use environment variable substitution for all paths and credentials
3. **MCP Server Safety**: Validate MCP server configs before saving (command exists, args valid)
4. **Vector Store Performance**: For large document sets, consider chunked batch inserts
5. **WebSocket**: Use WebSocket for agent chat to enable streaming responses
6. **File Upload**: Limit file sizes, validate file types, scan for security
7. **Theme Persistence**: Store theme settings in localStorage AND backend for sync
8. **Error Handling**: All API endpoints should return consistent error format
9. **Docling**: May require additional system dependencies - document in README
10. **Playwright**: Run in Docker for consistent CI/CD testing

## Docker Volume Configuration

```yaml
# docker/docker-compose.yml additions
services:
  mssql:
    volumes:
      - mssql_data:/var/opt/mssql
      - ${LOCAL_STORAGE_PATH:-./data}/uploads:/app/uploads
      - ${LOCAL_STORAGE_PATH:-./data}/models:/app/models

  api:
    build:
      context: ..
      dockerfile: docker/Dockerfile.api
    volumes:
      - ${LOCAL_STORAGE_PATH:-./data}/uploads:/app/uploads
      - ${LOCAL_STORAGE_PATH:-./data}/models:/app/models
    environment:
      - UPLOAD_DIR=/app/uploads
      - MODEL_CACHE_DIR=/app/models
```

## Environment Variables (Additional)

```bash
# Add to .env.example

# Storage Configuration
LOCAL_STORAGE_PATH=./data
UPLOAD_DIR=/app/uploads
MODEL_CACHE_DIR=/app/models
MAX_UPLOAD_SIZE_MB=100

# RAG Configuration
EMBEDDING_MODEL=all-MiniLM-L6-v2
CHUNK_SIZE=500
CHUNK_OVERLAP=50
RAG_TOP_K=5

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
CORS_ORIGINS=http://localhost:5173,http://localhost:3000

# Frontend Configuration
VITE_API_URL=http://localhost:8000
```
