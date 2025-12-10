# PRPs - Product Requirement Prompts

This directory contains Product Requirement Prompts (PRPs) for the **Local LLM Research Analytics Tool** project.

## What is a PRP?

A **Product Requirement Prompt (PRP)** is a structured prompt methodology for AI-assisted development. Unlike traditional PRDs (Product Requirement Documents) that focus on *what* to build, PRPs include the *how* — providing AI coding assistants with everything they need to implement features in a single pass.

### PRP Structure

| Section | Purpose |
|---------|---------|
| **Overview** | Phase number, focus, estimated effort, prerequisites |
| **Goal** | What will be implemented |
| **Success Criteria** | Checkboxes for validation |
| **Technology Stack** | Dependencies, Docker services, configurations |
| **Implementation Plan** | Step-by-step with complete code examples |
| **File Structure** | Where files should be created |
| **Testing Checklist** | How to verify each component |
| **Troubleshooting** | Common issues and solutions |

---

## Project Overview

### Technology Stack

| Layer | Technology |
|-------|------------|
| **LLM** | Ollama (qwen3:30b, nomic-embed-text) |
| **Agent Framework** | Pydantic AI |
| **Database** | SQL Server 2022 (Docker) |
| **Vector Store** | Redis Stack (HNSW) |
| **Backend API** | FastAPI + WebSocket |
| **Frontend** | React + TypeScript + Tailwind + shadcn/ui |
| **Visualization** | Recharts |
| **BI Platform** | Apache Superset (optional) |
| **MCP Servers** | MSSQL, Microsoft Learn Docs, Power BI Modeling |

### Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              Docker Compose                             │
├─────────────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌─────────────┐  │
│  │  SQL Server  │  │ Redis Stack  │  │   Ollama     │  │   FastAPI   │  │
│  │    :1433     │  │  :6379/:8001 │  │   :11434     │  │    :8000    │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  └─────────────┘  │
│  ┌──────────────┐                                                       │
│  │   Superset   │  (Phase 3 - Optional)                                 │
│  │    :8088     │                                                       │
│  └──────────────┘                                                       │
└─────────────────────────────────────────────────────────────────────────┘
                    │                               │
              ┌─────┴─────┐                 ┌───────┴───────┐
              │  React UI │                 │  Streamlit    │
              │   :5173   │                 │    :8501      │
              └───────────┘                 └───────────────┘
```

---

## Project Phases

| Phase | PRP File | Focus | Est. Effort | Status |
|-------|----------|-------|-------------|--------|
| 1 | `local-llm-research-agent-prp.md` | CLI, Streamlit, SQL Agent, Docker | 3-4 days | ✅ Complete |
| 2.1 | `phase2.1-backend-rag-prp.md` | FastAPI, Database, RAG, Redis | 3-4 days | 🚧 Ready |
| 2.2 | `phase2.2-react-chat-prp.md` | React UI, WebSocket, Chat | 3-4 days | 🚧 Ready |
| 2.3 | `phase2.3-visualization-dashboard-prp.md` | Recharts, Dashboards, Widgets | 3-4 days | 🚧 Ready |
| 2.4 | `phase2.4-exports-powerbi-prp.md` | Exports, Power BI MCP | 2-3 days | 🚧 Ready |
| 2.5 | `phase2.5-advanced-polish-prp.md` | Alerts, Themes, Sharing | 3-4 days | 🚧 Ready |
| 3 | `phase3-apache-superset-prp.md` | Apache Superset BI | 2-3 days | 🚧 Ready |

**Total Estimated Effort:** 20-26 days

---

## Feature Summary by Phase

### Phase 1: Foundation ✅
- Pydantic AI agent with Ollama
- MSSQL MCP server integration
- CLI interface with Rich
- Streamlit chat UI
- Docker Compose (SQL Server)
- Research Analytics sample database

### Phase 2.1: Backend & RAG
- FastAPI application structure
- Alembic database migrations
- Redis Stack (vector store + cache)
- Docling document processing
- RAG pipeline with Ollama embeddings
- Dynamic MCP server configuration
- Health check endpoints
- Schema indexing for query enhancement

### Phase 2.2: React UI & Chat
- React + Vite + TypeScript setup
- Tailwind CSS + shadcn/ui components
- WebSocket streaming responses
- Chat interface with conversations
- Document upload and management
- MCP server selector
- Query history and saved queries
- Settings page (model selection)
- Dark/light theme toggle

### Phase 2.3: Visualization & Dashboards
- Recharts integration (Bar, Line, Area, Pie, Scatter)
- AI-driven chart type suggestions
- KPI cards for single metrics
- Dashboard CRUD operations
- Widget pinning from query results
- react-grid-layout (drag, drop, resize)
- Auto-refresh per widget
- Dashboard persistence to SQL Server

### Phase 2.4: Exports & Power BI
- PNG export (html2canvas)
- PDF export (jsPDF)
- CSV/Excel export (SheetJS)
- Dashboard JSON export/import
- Chat export to Markdown
- Chat export to PDF
- Power BI MCP integration
- PBIX file generation

### Phase 2.5: Advanced Features & Polish
- Data alerts with thresholds
- APScheduler for scheduled queries
- Toast + browser notifications
- Theme presets (Ocean, Forest, Sunset, Corporate)
- Custom theme builder
- Corporate branding (logo, colors)
- Dashboard sharing via public links
- Onboarding wizard (health checks)
- Keyboard shortcuts
- Responsive design (tablet-friendly)

### Phase 3: Apache Superset
- Docker container setup
- SQL Server datasource configuration
- Sample dashboard creation
- Embedded dashboards in React (iframe)
- Superset API integration
- User documentation

---

## Phase Dependencies

```
Phase 1 (Complete)
    │
    ▼
Phase 2.1 (Backend/RAG)
    │
    ▼
Phase 2.2 (React/Chat)
    │
    ▼
Phase 2.3 (Visualization)
    │
    ▼
Phase 2.4 (Exports)
    │
    ▼
Phase 2.5 (Polish)
    │
    ▼
Phase 3 (Superset) [Optional]
```

---

## Validation Checkpoints

| After Phase | Validation Criteria |
|-------------|---------------------|
| **2.1** | Health checks pass for SQL Server, Redis, Ollama |
| **2.1** | Documents upload via API and chunks appear in Redis |
| **2.1** | MCP servers load from `mcp_config.json` |
| **2.2** | Chat works end-to-end with streaming responses |
| **2.2** | Conversations persist and can be resumed |
| **2.2** | Documents can be uploaded via React UI |
| **2.3** | Query results render as appropriate chart type |
| **2.3** | Charts can be pinned to dashboard |
| **2.3** | Dashboard layout persists after refresh |
| **2.4** | All export formats download correctly |
| **2.4** | Power BI MCP creates valid PBIX files |
| **2.5** | Data alerts trigger notifications |
| **2.5** | Scheduled queries run on time |
| **2.5** | Custom themes persist correctly |
| **2.5** | Shared dashboard links work |
| **3** | Superset accessible at localhost:8088 |
| **3** | Superset dashboards embed in React app |

---

## Directory Structure

```
PRPs/
├── README.md                                 # This file
├── templates/
│   └── prp_base.md                           # Base template for new PRPs
├── local-llm-research-agent-prp.md           # Phase 1: Core implementation
├── phase2.1-backend-rag-prp.md               # Phase 2.1: Backend & RAG
├── phase2.2-react-chat-prp.md                # Phase 2.2: React UI & Chat
├── phase2.3-visualization-dashboard-prp.md   # Phase 2.3: Visualization
├── phase2.4-exports-powerbi-prp.md           # Phase 2.4: Exports & Power BI
├── phase2.5-advanced-polish-prp.md           # Phase 2.5: Advanced Features
└── phase3-apache-superset-prp.md             # Phase 3: Apache Superset
```

---

## Using PRPs

### Execute a PRP with Claude Code

```bash
# Execute phases in order
/execute-prp PRPs/phase2.1-backend-rag-prp.md
/execute-prp PRPs/phase2.2-react-chat-prp.md
/execute-prp PRPs/phase2.3-visualization-dashboard-prp.md
/execute-prp PRPs/phase2.4-exports-powerbi-prp.md
/execute-prp PRPs/phase2.5-advanced-polish-prp.md
/execute-prp PRPs/phase3-apache-superset-prp.md
```

> **Important:** Validate each phase's success criteria before starting the next phase.

### Generate a New PRP

```bash
/generate-prp "Add conversation history persistence"
/generate-prp INITIAL.md
```

### Manual PRP Creation

1. Copy `templates/prp_base.md` to a new file
2. Fill in all sections with specific details
3. Include actual code examples from the codebase
4. Define testable success criteria
5. Break implementation into logical steps

---

## Git Branch Strategy

```bash
# Recommended branch workflow
main
├── phase-2.1-backend-rag
├── phase-2.2-react-chat
├── phase-2.3-visualization
├── phase-2.4-exports
├── phase-2.5-polish
└── phase-3-superset

# After each phase completes and validates:
git checkout main
git merge phase-2.X-branch
git tag v2.X.0
git push origin main --tags
```

### Example Workflow

```bash
# Start Phase 2.1
git checkout -b phase-2.1-backend-rag
# ... implement using PRP ...
# ... validate success criteria ...

# Merge when complete
git checkout main
git merge phase-2.1-backend-rag
git tag v2.1.0

# Start Phase 2.2
git checkout -b phase-2.2-react-chat
# ... continue pattern ...
```

---

## Best Practices

### ✅ Good PRPs

- Include specific file paths and function names
- Reference existing code patterns to follow
- Have measurable success criteria (checkboxes)
- Break work into logical implementation steps
- Include complete code examples (not snippets)
- Include validation/testing checkpoints
- Document troubleshooting for common issues
- Specify environment variables and configurations

### ❌ Poor PRPs

- Vague descriptions ("make it better")
- No code examples or patterns
- Missing file paths
- Single monolithic implementation step
- No success criteria
- Assume knowledge not in context
- Missing dependency specifications
- No testing/validation guidance

---

## PRP Statistics

| PRP | Lines | Size |
|-----|-------|------|
| Phase 1 | 480 | 15 KB |
| Phase 2.1 | 1,816 | 55 KB |
| Phase 2.2 | 1,794 | 52 KB |
| Phase 2.3 | 1,530 | 43 KB |
| Phase 2.4 | 1,230 | 34 KB |
| Phase 2.5 | 1,894 | 55 KB |
| Phase 3 | 940 | 26 KB |
| **Total** | **9,684** | **280 KB** |

---

## Related Resources

- [CLAUDE.md](../CLAUDE.md) - Project context and conventions
- [Context Engineering Intro](https://github.com/coleam00/context-engineering-intro) - PRP methodology reference
- [PRPs Agentic Engineering](https://github.com/Wirasm/PRPs-agentic-eng) - Extended PRP examples
- [Pydantic AI Docs](https://ai.pydantic.dev/) - Agent framework documentation
- [MCP Specification](https://modelcontextprotocol.io/) - Model Context Protocol

---

## Quick Start

```bash
# 1. Ensure Phase 1 is complete and working
cd local-llm-research-agent
docker-compose -f docker/docker-compose.yml up -d
python -m src.main  # Verify CLI works

# 2. Start Phase 2.1
# Open PRP in Claude Code and execute:
/execute-prp PRPs/phase2.1-backend-rag-prp.md

# 3. Validate Phase 2.1
curl http://localhost:8000/health  # All services healthy

# 4. Continue with subsequent phases...
```
