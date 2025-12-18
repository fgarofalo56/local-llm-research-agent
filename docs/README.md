# Documentation

> **Complete documentation for the Local LLM Research Agent**

---

## Quick Links

| Document | Description |
|----------|-------------|
| [Getting Started](guides/getting-started.md) | Quick start guide for new users |
| [Configuration](guides/configuration.md) | Environment variables and settings |
| [Ollama Guide](guides/ollama.md) | Install and manage Ollama |
| [Foundry Local Guide](guides/foundry-local.md) | Install and manage Foundry Local |
| [Troubleshooting](guides/troubleshooting.md) | Comprehensive problem-solving guide |
| [API Reference](api/README.md) | Programmatic interface documentation |
| [FastAPI Backend](api/fastapi.md) | REST API documentation |
| [RAG Pipeline](api/rag.md) | Document retrieval and vector search |
| [Exports Guide](guides/exports.md) | Export functionality documentation |

---

## Documentation Structure

```
docs/
├── README.md                    # This file - documentation index
│
├── guides/                      # User guides and tutorials
│   ├── getting-started.md       # Quick start guide
│   ├── configuration.md         # Configuration reference
│   ├── ollama.md                # Ollama management guide
│   ├── foundry-local.md         # Foundry Local management guide
│   ├── troubleshooting.md       # Problem-solving guide
│   └── DOCUMENTATION-STANDARDS.md  # Doc style guide
│
├── api/                         # API documentation
│   ├── README.md                # API overview
│   ├── agent.md                 # ResearchAgent API
│   ├── providers.md             # LLM providers API
│   ├── mcp-client.md            # MCP client API
│   ├── models.md                # Data models API
│   ├── utilities.md             # Utilities API
│   ├── fastapi.md               # FastAPI REST API
│   └── rag.md                   # RAG Pipeline
│
├── reference/                   # Reference materials
│   ├── configuration.md         # Full configuration reference
│   ├── mssql_mcp_tools.md       # MSSQL MCP tool documentation
│   └── pydantic_ai_mcp.md       # Pydantic AI MCP integration
│
└── diagrams/                    # Architecture diagrams
    └── architecture.excalidraw  # System architecture diagram
```

---

## Getting Started

New to the project? Follow this path:

1. **[Getting Started Guide](guides/getting-started.md)** - Complete setup walkthrough
2. **[Ollama Guide](guides/ollama.md)** or **[Foundry Local Guide](guides/foundry-local.md)** - Set up your LLM provider
3. **[Docker Setup](../docker/README.md)** - Set up SQL Server with sample data
4. **[Configuration](guides/configuration.md)** - Configure your environment

---

## User Guides

| Guide | Purpose | Audience |
|-------|---------|----------|
| [Getting Started](guides/getting-started.md) | First-time setup and basic usage | New users |
| [Configuration](guides/configuration.md) | All environment variables explained | All users |
| [Ollama Guide](guides/ollama.md) | Install, configure, optimize Ollama | Ollama users |
| [Foundry Local Guide](guides/foundry-local.md) | Install, configure Foundry Local | Foundry users |
| [Troubleshooting](guides/troubleshooting.md) | Fix common issues | All users |
| [Documentation Standards](guides/DOCUMENTATION-STANDARDS.md) | How to write docs | Contributors |

---

## API Reference

For developers integrating or extending the agent:

| Reference | Purpose |
|-----------|---------|
| [API Overview](api/README.md) | API introduction and quick start |
| [Agent API](api/agent.md) | ResearchAgent class, factory functions |
| [Providers API](api/providers.md) | Ollama, Foundry Local providers |
| [MCP Client API](api/mcp-client.md) | MCP server integration |
| [Models API](api/models.md) | Data models and schemas |
| [Utilities API](api/utilities.md) | Config, logging, caching, health |
| [FastAPI Backend](api/fastapi.md) | REST API endpoints |
| [RAG Pipeline](api/rag.md) | Vector search and document processing |

---

## Technical Reference

| Reference | Purpose |
|-----------|---------|
| [Configuration Reference](reference/configuration.md) | Complete configuration options |
| [MSSQL MCP Tools](reference/mssql_mcp_tools.md) | SQL Server MCP tool documentation |
| [Pydantic AI MCP](reference/pydantic_ai_mcp.md) | Agent framework integration |

---

## Architecture

The system architecture is documented in the [architecture diagram](diagrams/architecture.excalidraw).

### High-Level Overview

```
┌────────────────────────────────────────────────────────────────────────────┐
│                           User Interfaces                                   │
│  ┌─────────────────┐  ┌─────────────────────┐  ┌────────────────────────┐  │
│  │   CLI (Typer)   │  │   Streamlit UI      │  │  FastAPI Backend       │  │
│  └────────┬────────┘  └──────────┬──────────┘  └───────────┬────────────┘  │
└───────────┼──────────────────────┼─────────────────────────┼───────────────┘
            │                      │                         │
            ▼                      ▼                         ▼
┌────────────────────────────────────────────────────────────────────────────┐
│                         Pydantic AI Agent                                   │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │  System Prompt + Tool Orchestration + Conversation + RAG Context     │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────┬──────────────────────────────────────────┘
                                  │
            ┌─────────────────────┼─────────────────────┐
            ▼                     ▼                     ▼
┌───────────────────────┐  ┌─────────────────┐  ┌─────────────────────────┐
│   LLM Provider        │  │   MCP Servers   │  │   RAG Pipeline          │
│  ┌─────────────────┐  │  │  ┌───────────┐  │  │  ┌───────────────────┐  │
│  │ Ollama          │  │  │  │ MSSQL MCP │  │  │  │ Docling Parser    │  │
│  ├─────────────────┤  │  │  └─────┬─────┘  │  │  ├───────────────────┤  │
│  │ Foundry Local   │  │  │        │        │  │  │ Ollama Embeddings │  │
│  └─────────────────┘  │  │        ▼        │  │  ├───────────────────┤  │
└───────────────────────┘  │  ┌───────────┐  │  │  │ Vector Search     │  │
                           │  │SQL Server │  │  │  └─────────┬─────────┘  │
                           │  └───────────┘  │  │            │            │
                           └─────────────────┘  │            ▼            │
                                                │  ┌───────────────────┐  │
                                                │  │  Redis Stack      │  │
                                                │  └───────────────────┘  │
                                                └─────────────────────────┘
```

### Key Components

| Component | Technology | Purpose |
|-----------|------------|---------|
| LLM Runtime | Ollama / Foundry Local | Local model inference |
| Agent Framework | Pydantic AI | Orchestration & tools |
| MCP Server | MSSQL MCP (Node.js) | SQL Server access |
| Web UI | Streamlit | Browser interface |
| CLI | Typer + Rich | Terminal interface |
| Sample Database | SQL Server 2022 | Demo data (ResearchAnalytics) |
| Backend Database | SQL Server 2025 | App state + native vectors (LLM_BackEnd) |
| **Backend API** | FastAPI + Uvicorn | REST API server |
| **ORM** | SQLAlchemy 2.0 + Alembic | Database models & migrations |
| **Vector Store (Primary)** | SQL Server 2025 VECTOR | Native vector similarity search |
| **Vector Store (Fallback)** | Redis Stack | Alternative similarity search |
| **Embeddings** | Ollama (nomic-embed-text) | 768-dimensional vectors |
| **Doc Processing** | pypdf, python-docx | PDF/DOCX parsing |

---

## Features

### Core Features

| Feature | Status | Description |
|---------|--------|-------------|
| Natural Language Queries | ✅ Stable | Ask questions in plain English |
| Multi-Provider Support | ✅ Stable | Ollama and Foundry Local |
| Streaming Responses | ✅ Stable | See answers as generated |
| Response Caching | ✅ Stable | Faster repeated queries |
| Rate Limiting | ✅ Stable | Control request throughput |
| Multi-Auth Support | ✅ Stable | SQL, Windows, Azure AD |
| Session History | ✅ Stable | Save and recall conversations |
| Read-Only Mode | ✅ Stable | Safe database exploration |

### Backend & API

| Feature | Status | Description |
|---------|--------|-------------|
| FastAPI Backend | ✅ Stable | REST API for all operations |
| SQLAlchemy ORM | ✅ Stable | Database models with Alembic migrations |
| WebSocket Chat | ✅ Stable | Real-time streaming responses |
| Dynamic MCP | ✅ Stable | Runtime MCP server configuration |
| Dashboard API | ✅ Stable | Dashboard and widget management |
| Query History | ✅ Stable | Saved queries and favorites |

### RAG Pipeline

| Feature | Status | Description |
|---------|--------|-------------|
| SQL Server 2025 Vector Store | ✅ Stable | Native VECTOR type similarity search (primary) |
| Redis Vector Store | ✅ Stable | Alternative vector search (fallback) |
| Document Upload | ✅ Stable | PDF/DOCX processing |
| RAG Search | ✅ Stable | Context-aware document retrieval |
| Schema Indexing | ✅ Stable | Database schema for RAG context |
| Ollama Embeddings | ✅ Stable | Local 768-dim embedding generation |

### Export System

| Feature | Status | Description |
|---------|--------|-------------|
| PNG Export | ✅ Stable | High-resolution chart images |
| PDF Export | ✅ Stable | Multi-page dashboard/chart reports |
| CSV Export | ✅ Stable | Standard data export format |
| Excel Export | ✅ Stable | Spreadsheets with auto-column widths |
| Dashboard JSON | ✅ Stable | Import/export dashboard configs |
| Chat Export | ✅ Stable | Conversation to Markdown/PDF |
| Power BI Dialog | ✅ Stable | PBIX file creation interface |

---

## Authentication Options

| Auth Type | Use Case |
|-----------|----------|
| SQL Authentication | Local SQL Server, Docker |
| Windows Authentication | On-premises domain environments |
| Azure AD Interactive | Development with Azure SQL |
| Azure AD Service Principal | Production automation |
| Azure AD Managed Identity | Azure-hosted applications |
| Azure AD Default | Auto-detect available credentials |

See [Configuration Guide](guides/configuration.md) for setup details.

---

## Security

- **100% Local** - All LLM processing on your machine
- **No Cloud APIs** - Data never leaves your network (unless using Azure SQL)
- **Read-only Mode** - Safe exploration option
- **Multi-Auth** - Secure authentication options

See [SECURITY.md](../SECURITY.md) for full security policy.

---

## Contributing

Documentation contributions are welcome! Please follow the [Documentation Standards](guides/DOCUMENTATION-STANDARDS.md).

### Reporting Issues

- **Bug Reports:** [GitHub Issues](https://github.com/yourusername/local-llm-research-agent/issues)
- **Questions:** [GitHub Discussions](https://github.com/yourusername/local-llm-research-agent/discussions)

---

*Last Updated: December 2025*
