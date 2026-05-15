# CRITICAL: MANDATORY PRE-TASK CHECKS - READ THIS FIRST

> **Note:** This project previously used Archon v1 for task tracking. Archon v1 was archived by its author in April 2026. Historical Archon task records were exported to `.claude/migrated-archon-tasks.md` at migration time. Use TodoWrite + GitHub Issues going forward (see Rule 0).

BEFORE doing ANYTHING else, ALWAYS perform these checks in order:

---

## Critical Rules (Override Everything)

### Rule 0: Task Tracking — Native-First

For tracking work in the current session and across sessions, use **native Claude Code tools**:

| Scope | Tool | When |
|-------|------|------|
| Within-turn / within-session checklist | `TodoWrite` | Multi-step task you'll finish soon |
| Cross-session work | **GitHub Issues** (`gh issue`) | Work that spans days or needs visibility |
| Long-form planning | `PRPs/plans/<name>.plan.md` (if PRP framework selected) | Multi-PR initiatives with phases |
| Recurring backlog item | GitHub Issue with a label | Anything you'll reference more than twice |

`TodoWrite` is the right default. Use it freely. Cross-session durability comes from the **filesystem** (`.claude/reference/`, plan files, this CLAUDE.md) and **GitHub** (Issues, PRs, commit messages) — not from a separate task database.

### Rule 1: Load Context First

At the start of EVERY session, before any code work:

1. Run the [Startup Protocol](#startup-protocol).
2. Read this `CLAUDE.md` and any relevant `.claude/reference/*.md`.
3. Check `git status` and `git log -10` for in-flight work.
4. Check open GitHub Issues / PRs if relevant: `gh pr list` / `gh issue list`.
5. Check `MEMORY.md` if there's per-project auto-memory at `~/.claude/projects/<slug>/memory/`.

Never start coding without orienting first.

### Rule 2: Preserve Context in the Filesystem

Project knowledge that survives context resets lives in **files**, not in your conversation:

| Document | Where | When to update |
|----------|-------|----------------|
| Architecture decisions | `.claude/reference/architecture.md` | After any architectural decision |
| Deployment runbook | `.claude/reference/deployment.md` | After deployment changes |
| Session handoff | `.claude/reference/session-context.md` | End of each significant session, before `/compact` or `/clear` |
| API surface | `.claude/reference/api.md` (or generated OpenAPI) | After API surface changes |
| Non-obvious facts / gotchas | `MEMORY.md` (auto-memory) | When you hit something a future session needs |

If the context window approaches 70%, update `session-context.md` BEFORE compacting. Load specific reference docs on demand with `@.claude/reference/<file>.md` syntax — don't preload everything.

### Rule 3: Skills Discovery

Before implementing anything non-trivial, check available skills (`.claude/skills/` and `~/.claude/skills/`). Skills are tested, opinionated workflows - prefer them over ad-hoc solutions.

### Rule 4: Temporary Files Go in `temp/`

All temp files MUST be created under `./temp/` (gitignored), never the repo root. Create the directory if it doesn't exist. Never commit temp files.

### Rule 5: Never Tamper with Security Software

This machine may be Intune-managed. Claude must NEVER attempt to disable, stop, or modify Windows Defender, antivirus, or any security software. If a task seems blocked by security, STOP and ask the user - do not work around it.

### Rule 6: Never Read Secrets

Forbidden paths: `.env`, `.env.*`, `secrets/**`, `~/.ssh/**`, `~/.aws/**`, `**/credentials.json`, `**/service-account.json`. Use `.env.example` as a template only.

### Rule 7: Automatic Behaviors Live in Hooks, Not Memory

If you want Claude to "always do X when Y happens" (e.g., run a linter after every edit, post to Slack on session end, validate env vars before deploy), that **must** be a hook in `.claude/settings.json` — not a memory entry or a CLAUDE.md instruction.

| Mechanism | Fires when | Best for |
|-----------|-----------|----------|
| **Hooks** (`settings.json`) | Deterministic events: PreToolUse, PostToolUse, UserPromptSubmit, Stop, etc. | "Always run X after Y" |
| **Memory** (`MEMORY.md`) | Recalled by Claude when relevant context appears | Facts, preferences, prior decisions |
| **CLAUDE.md** | Loaded into every session | Project-wide policies and conventions |
| **Skills** | Auto-invoked when description matches user intent | Reusable workflows |

If your rule says "from now on, when X, do Y" — write a hook. Memory cannot enforce; it only informs.

---

## Project Reference

| Field | Value |
|-------|-------|
| **Project Title** | [PROJECT_TITLE] |
| **GitHub Repo** | [GITHUB_REPO] |
| **Repository Path** | [REPOSITORY_PATH] |
| **Primary Stack** | [PRIMARY_STACK] |

```bash
gh repo view [GITHUB_REPO]              # current state
gh issue list --state open               # in-flight backlog
gh pr list --state open                  # in-flight changes
```

---

## Startup Protocol

Run at the start of EVERY session:

1. **Read this file** + any reference docs the task touches (`@.claude/reference/<topic>.md`).

2. **Check git state**:

   ```bash
   git status
   git log --oneline -10
   ```

3. **Check in-flight GitHub work** (if relevant):

   ```bash
   gh pr list --state open
   gh issue list --state open --assignee @me
   ```

4. **Check `.claude/reference/session-context.md`** if it exists — picks up where the prior session left off.

5. **Brief the user** with: what was being worked on, uncommitted changes, recommended next step.

---

## Project Type: Backend API

| Concern | Guidance |
|---------|----------|
| **Validate at boundaries** | Pydantic / DTO / Zod at request ingress. Trust internal code; don't re-validate between layers. |
| **Error responses** | Generic message to client + `logger.exception(...)` server-side. Never `return {"error": str(exc)}` — leaks stack traces (CodeQL `py/stack-trace-exposure`). |
| **Database access** | Parameterized queries only. Connection pooling at the app boundary, not per-request. |
| **Auth** | At middleware level, not per-route. Never trust client-provided user IDs. |
| **Integration tests** | Hit a real database (testcontainers or ephemeral instance). Mocking the DB hides migration breakage. |
| **API versioning** | URL-versioned (`/v1/`) or header-versioned. Never silently break clients. |

Long-running operations: return a job ID + status endpoint, not a hung connection.
---

## Code Style

| Principle | Apply to |
|-----------|----------|
| Single responsibility | Functions, classes, modules |
| Readable over clever | Default |
| DRY | Extract after the third repetition, not the second |
| Testable | Pure functions where possible |
| Minimal dependencies | Add only when truly needed |

[PRIMARY_LANGUAGE]-specific conventions: customize this section.

---

## Testing

| Type | Target | Location |
|------|--------|----------|
| Unit | 80%+ on changed code | `tests/unit/` |
| Integration | Critical paths | `tests/integration/` |
| E2E | Happy paths + critical flows | `tests/e2e/` |

AAA pattern: Arrange / Act / Assert. Run tests before marking a task `review`.

---

## Security

Never commit: API keys, passwords, private keys, connection strings, `.env` files.
Use environment variables. The `.env.example` in this repo lists required variables.

Validate user input. Parameterize queries. Sanitize output. Keep deps updated.

---

## Git Workflow

Branches: `feature/<ticket>-desc`, `bugfix/<ticket>-desc`, `hotfix/<ticket>-desc`.

Commit format: `<type>(<scope>): <short summary>` where type is `feat|fix|docs|style|refactor|test|chore|perf`.

PR requirements: clear description, linked issue, tests, CI green.

---

## End of Session Protocol

1. Update `.claude/reference/session-context.md` with: what was completed, decisions made, next steps, blockers.
2. Update or close any open `TodoWrite` items (mark completed as you go, don't batch).
3. Commit uncommitted work with a descriptive message.
4. If the work warrants a follow-up GitHub Issue (something you'll want to find later), open it now: `gh issue create`.
5. Brief the user with a session summary.

Always update `session-context.md` BEFORE `/clear` or `/compact` near 70%.

---

## Available Tools

> Generated by the project wizard from the deployed skills/commands/agents/MCP servers.

### Skills (`.claude/skills/`)

_No project-specific skills deployed. Check `~/.claude/skills/` for global skills._

### Commands (`.claude/commands/`)

| Command | Category |
|---------|----------|
| `/end` | base_commands |
| `/next` | base_commands |
| `/save` | base_commands |
| `/start` | base_commands |
| `/status` | base_commands |
| `/execute-prp` | general |
| `/generate-prp` | general |
| `/README` | general |
| `/refresh-statusline` | general |

### Agents (`.claude/agents/`)

| Agent | Type |
|-------|------|
| `ai-engineer` | Markdown |
| `api-documenter` | Markdown |
| `architect-review` | Markdown |
| `background-researcher` | Markdown |
| `code-simplifier` | Markdown |
| `data-engineer` | Markdown |
| `docs-architect` | Markdown |
| `documentation-manager copy` | Markdown |
| `documentation-manager` | Markdown |
| `mermaid-expert` | Markdown |
| `python-pro` | Markdown |
| `reference-builder` | Markdown |
| `search-specialist` | Markdown |
| `validation-gates` | Markdown |
| `verify-app` | Markdown |

### MCP Servers (`.vscode/mcp.json`)

_No project-specific MCP servers configured. See `.vscode/mcp.json` for active servers._

---

## Claude Code Capabilities Quick Reference

Pointers to features that meaningfully change how a task gets done. Use these when the situation matches — don't reach for them by default.

### Sub-agents and isolation

| When | Tool | Notes |
|------|------|-------|
| Need independent research that would bloat main context | `Agent` with `subagent_type: Explore` or `general-purpose` | Returns a single message; main thread stays clean |
| Need 2+ independent investigations | Multiple `Agent` calls in **one** message | Run in parallel |
| Risky refactor that might fail | `Agent` with `isolation: worktree` | Auto-cleanup if no changes made |
| Specialized work matches an agent | `Agent` with the right `subagent_type` | See agent registry in `.claude/agents/` |

### Background tasks

| When | How |
|------|-----|
| Command runs >5 min (CI watch, large build) | `Bash` with `run_in_background: true` |
| Want notification on completion | The harness notifies automatically — **don't poll** |
| Long agent run that doesn't block your next steps | `Agent` with `run_in_background: true` |

### Context management

| Action | Command / Syntax |
|--------|------------------|
| Check token usage | `/cost` |
| Compress conversation (preserves intent) | `/compact` — update Session Context first if near 70% |
| Hard reset | `/clear` — save context to disk first |
| Load a reference doc on demand | `@.claude/reference/<file>.md` in user prompt |
| Switch model mid-session | `/model opus` / `/model sonnet` / `/model haiku` |
| Faster Opus output | `/fast` (Opus 4.6 / 4.7 only — no quality drop) |

### Permission & settings

| Need | Where |
|------|-------|
| Allow specific commands without prompts | `permissions.allow` in `.claude/settings.json` |
| Per-tool restrictions for a skill/agent | `allowed-tools:` frontmatter |
| Auto-accept edits in current session | `/permissions` → accept edits mode |
| Plan-only mode (read, don't write) | `/permissions` → plan mode |

### Model selection heuristic

| Task type | Default model |
|-----------|---------------|
| Heavy reasoning, architecture, audits | Opus (Opus 4.7 has 1M context) |
| Day-to-day coding, refactors | Sonnet |
| Quick lookups, simple edits, batch ops | Haiku |

### Skill & command frontmatter (modern fields)

```yaml
---
name: my-skill
description: When to use it (matters for auto-invocation)
effort: high              # low|medium|high|max — reasoning depth
context: fork             # Run in isolated subagent
allowed-tools: Read, Grep # Restrict tool access
argument-hint: "[file]"   # Shown in autocomplete
hooks:                    # Skill-scoped hooks
  PostToolUse:
    - matcher: "Edit"
      hooks: [{type: command, command: "./format.sh"}]
---
```

### Memory system

Per-project auto-memory lives in `~/.claude/projects/<project-slug>/memory/`. Index is `MEMORY.md`. Save user/feedback/project/reference notes there — never duplicate facts already in code or git history.

---

## 1. SKILLS-FIRST RULE
**Check for relevant skills BEFORE attempting any task:**
- Location: `C:\Users\frgarofa\.claude\skills\`
- Read applicable SKILL.md files for expert guidance
- Available skills: pydantic-ai, mcp-development, ollama, mssql-mcp, azure-mcp, rag-patterns, react-typescript, streamlit-dashboards, vector-databases, pytest-advanced, and 160+ more
- **NEVER attempt implementation without checking if a skill exists for the technology**

## 3. TEMPORARY FILES RULE
**All temporary files must be placed in the `temp/` folder:**
- Location: `temp/` at project root (git-ignored)
- NEVER create temporary files at the project root level
- NEVER create `tmpclaude-*` or similar temp files in root
- Use `temp/` for: working directories, scratch files, session data, temporary outputs
- The `temp/` folder is local-only and excluded from git

**Examples:**
```bash
# CORRECT - Use temp folder

temp/working-file.txt
temp/session-data/
temp/scratch.py

# WRONG - Never at root

tmpclaude-abc123-cwd      # Bad
working-file.txt          # Bad (if temporary)
```

## 4. QUICK COMMANDS AVAILABLE

**Slash commands for common workflows:**
- `/start` - Session startup protocol (load context, check tasks, briefing)
- `/next` - What should I work on next? (prioritized options)
- `/status` - Current project status briefing
- `/save` - Save checkpoint to memory files
- `/end` - End session protocol (update memory, summary)
- `/lint` - Run code quality checks
- `/test` - Run test suite
- `/services` - Check all service statuses
- `/commit` - Smart commit helper

**Full reference:** `.claude/commands/README.md`

---

# CLAUDE.md - Local LLM Universal Research Agent

## Project Overview

This is a **100% local** universal research agent combining SQL Server analytics, RAG-powered knowledge retrieval, and multi-MCP tool integration. The system uses Ollama for local LLM inference, Pydantic AI for agent orchestration, and supports multiple MCP servers for extensible tool capabilities.

**IMPORTANT:** This project prioritizes privacy and local execution. All LLM inference runs locally via Ollama. No data leaves the local environment.

### Universal Agent Capabilities

| Capability | Description |
|------------|-------------|
| **SQL Analytics** | Query SQL Server databases via MSSQL MCP |
| **RAG Knowledge Base** | Hybrid vector + keyword search with SQL Server 2025 native vectors |
| **Multi-MCP Tools** | Connect multiple MCP servers simultaneously (MSSQL, Analytics, Docs, custom) |
| **Thinking Mode** | Enable detailed reasoning with `<think>` tags |
| **Document Processing** | Index 14+ document formats via Docling |
| **Conversation History** | Save/load sessions, export to JSON/CSV/Markdown |

---

## Hardware Configuration

| Component | Specification |
|-----------|---------------|
| **CPU** | AMD Ryzen 9 5950X (16-Core, 32 Threads) |
| **RAM** | 128 GB DDR4 |
| **GPU** | NVIDIA RTX 5090 (32GB VRAM) |
| **OS** | Windows 11 Enterprise |

---

## Tech Stack

### Core Components

| Component | Technology | Purpose |
|-----------|------------|---------|
| LLM Runtime | Ollama | Local LLM inference engine |
| LLM Model | `qwen3:30b` (primary) | Reasoning + tool calling |
| Agent Framework | Pydantic AI | Agent orchestration, tool management |
| MCP Integration | mcp, pydantic-ai[mcp] | Model Context Protocol for tools |
| SQL Server MCP | MSSQL MCP Server (Node.js) | SQL Server data access via MCP |
| Sample Database | SQL Server 2022 (Docker, port 1433) | ResearchAnalytics demo data |
| Backend Database | SQL Server 2025 (Docker, port 1434) | LLM_BackEnd app state + vectors |
| Data Validation | Pydantic v2 | Type-safe data models |
| Async Runtime | asyncio | Async operations |
| Environment | python-dotenv | Environment configuration |

### User Interfaces

| Component | Technology | Purpose |
|-----------|------------|---------|
| React Frontend | React 19 + Vite + TypeScript | Modern web UI |
| Web UI | Streamlit | User-friendly chat interface |
| CLI | Typer + Rich | Command-line chat interface |

### Backend & API

| Component | Technology | Purpose |
|-----------|------------|---------|
| Backend API | FastAPI + Uvicorn | REST API server |
| ORM | SQLAlchemy 2.0 + Alembic | Database models & migrations |
| Vector Store | SQL Server 2025 (primary) | Native VECTOR type for similarity search |
| Vector Store | Redis Stack (fallback) | Alternative vector store option |
| Embeddings | Ollama (nomic-embed-text) | Local document embeddings (768 dimensions) |
| Document Processing | pypdf, python-docx | PDF/DOCX parsing for RAG |

### BI & Visualization

| Component | Technology | Purpose |
|-----------|------------|---------|
| Charts | Recharts | React data visualization |
| BI Platform | Apache Superset | Enterprise analytics |

---

## Project Structure

```
local-llm-research-agent/
├── CLAUDE.md                    # This file - AI assistant context
├── README.md                    # Project documentation
├── pyproject.toml               # Python project configuration (uv/pip)
├── requirements.txt             # Pip requirements fallback
├── .env.example                 # Environment variables template
├── .env                         # Local environment config (git-ignored)
├── .gitignore                   # Git ignore rules
├── mcp_config.json              # MCP server configuration
├── alembic.ini                  # Alembic migrations config
│
├── alembic/                     # Database migrations
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
│
├── data/                        # Data storage
│   ├── uploads/                 # Uploaded documents for RAG
│   └── models/                  # Cached model files
│
├── docker/                      # Docker services setup
│   ├── docker-compose.yml       # SQL Server 2022/2025, Redis Stack, API, Superset
│   ├── Dockerfile.api           # FastAPI container
│   ├── setup-database.bat       # Windows setup helper
│   ├── setup-database.sh        # Linux/Mac setup helper
│   ├── init/                    # Sample database initialization (ResearchAnalytics)
│   │   ├── 01-create-database.sql
│   │   ├── 02-create-schema.sql
│   │   └── 03-seed-data.sql
│   └── init-backend/            # Backend database initialization (LLM_BackEnd)
│       ├── 01-create-llm-backend.sql    # Database + schemas
│       ├── 02-create-app-schema.sql     # App state tables
│       └── 03-create-vectors-schema.sql # Native vector tables
│
├── frontend/                    # React frontend
│   ├── src/
│   │   ├── api/                 # REST API client
│   │   ├── components/          # React components
│   │   │   ├── chat/            # Chat components
│   │   │   ├── charts/          # Recharts wrappers
│   │   │   ├── dashboard/       # Dashboard components
│   │   │   ├── export/          # Export components
│   │   │   ├── layout/          # Layout components
│   │   │   └── ui/              # Reusable UI components
│   │   ├── contexts/            # React contexts
│   │   ├── hooks/               # Custom hooks
│   │   ├── lib/exports/         # Export utilities
│   │   ├── pages/               # Route pages
│   │   ├── stores/              # Zustand state
│   │   └── types/               # TypeScript interfaces
│   ├── package.json
│   ├── vite.config.ts
│   └── tailwind.config.js
│
├── src/
│   ├── __init__.py
│   ├── main.py                  # Application entry point
│   │
│   ├── agent/
│   │   ├── __init__.py
│   │   ├── research_agent.py    # Main Pydantic AI agent
│   │   └── prompts.py           # System prompts and templates
│   │
│   ├── api/                     # FastAPI backend
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI app with lifespan
│   │   ├── deps.py              # Dependency injection
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   └── database.py      # SQLAlchemy ORM models
│   │   └── routes/
│   │       ├── __init__.py
│   │       ├── health.py        # Health checks + metrics
│   │       ├── documents.py     # Document upload/RAG
│   │       ├── conversations.py # Chat history
│   │       ├── queries.py       # Query history/saved
│   │       ├── dashboards.py    # Dashboard widgets
│   │       ├── mcp_servers.py   # Dynamic MCP management
│   │       ├── settings.py      # App settings/themes
│   │       ├── superset.py      # Superset integration
│   │       └── agent.py         # Agent chat endpoint
│   │
│   ├── rag/                     # RAG pipeline
│   │   ├── __init__.py
│   │   ├── embedder.py          # Ollama embeddings
│   │   ├── mssql_vector_store.py # SQL Server 2025 native vector store
│   │   ├── redis_vector_store.py # Redis vector search (fallback)
│   │   ├── document_processor.py # PDF/DOCX parsing
│   │   └── schema_indexer.py    # Database schema indexing
│   │
│   ├── providers/
│   │   ├── __init__.py
│   │   ├── base.py              # LLM provider base class
│   │   ├── factory.py           # Provider factory
│   │   ├── ollama.py            # Ollama provider
│   │   └── foundry.py           # Microsoft Foundry Local provider
│   │
│   ├── mcp/
│   │   ├── __init__.py
│   │   ├── client.py            # MCP client wrapper
│   │   ├── mssql_config.py      # MSSQL MCP server configuration
│   │   ├── server_manager.py    # MCP server lifecycle management
│   │   └── dynamic_manager.py   # Runtime MCP config
│   │
│   ├── cli/
│   │   ├── __init__.py
│   │   └── chat.py              # CLI chat interface
│   │
│   ├── ui/
│   │   ├── __init__.py
│   │   ├── streamlit_app.py     # Streamlit main chat interface
│   │   └── pages/               # Streamlit multi-page app
│   │       ├── __init__.py
│   │       ├── 1_Documents.py   # Document upload & RAG management
│   │       ├── 2_MCP_Servers.py # MCP server configuration
│   │       └── 3_Settings.py    # Provider & app settings
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── chat.py              # Chat message models
│   │   └── sql_results.py       # SQL result models
│   │
│   └── utils/
│       ├── __init__.py
│       ├── config.py            # Configuration management
│       ├── logger.py            # Logging configuration
│       ├── history.py           # Conversation history persistence
│       ├── export.py            # Export conversations
│       ├── health.py            # Health check utilities
│       ├── cache.py             # Caching utilities
│       └── rate_limiter.py      # Rate limiting
│
├── tests/                       # Test suite
│   ├── conftest.py              # Pytest fixtures
│   ├── test_agent.py
│   ├── test_providers.py
│   ├── test_mcp_client.py
│   ├── test_models.py
│   ├── test_config.py
│   └── test_history.py
│
├── examples/
│   ├── basic_chat.py            # Basic chat example
│   ├── sql_query_example.py     # SQL query via MCP
│   ├── multi_tool_example.py    # Multiple MCP tools
│   └── streaming_example.py     # Streaming responses
│
├── ai_docs/                     # AI context documentation
│   ├── pydantic_ai_mcp.md       # Pydantic AI MCP reference
│   └── mssql_mcp_tools.md       # MSSQL MCP tools reference
│
├── docs/                        # Extended documentation
│   ├── README.md                # Documentation index
│   ├── superset-guide.md        # Superset usage guide
│   ├── api/                     # API documentation
│   ├── guides/                  # User guides
│   └── reference/               # Technical reference
│
└── PRPs/                        # Product Requirement Prompts
    ├── README.md
    └── templates/
```

---

## Quick Reference

| Phrase | Action |
|--------|--------|
| `/start` | Run startup protocol |
| `/status` | Project status (git + open issues + recent commits) |
| `/end` | End-of-session protocol (update session-context, commit, summarize) |
| `@.claude/reference/<file>.md` | Load a specific reference doc into context on demand |

---

> **Template Version**: 4.0.0 | **Generated**: [CREATION_DATE]
> **Source**: claude-code-tools project wizard

## Ollama Model Configuration

### Available Models (Your System)

| Model | Size | Tool Calling | Recommended Use |
|-------|------|--------------|-----------------|
| **qwen3:30b** ⭐ | 18 GB | ✅ Native | PRIMARY - Best tool calling, MoE architecture |
| qwen3:32b | 20 GB | ✅ Native | Dense alternative, slightly better quality |
| qwen3:14b | 9.3 GB | ✅ Native | Faster responses, good quality |
| qwen3:8b | 5.2 GB | ✅ Native | Quick responses |
| deepseek-r1:8b | 5.2 GB | ✅ Supported | Reasoning + tools (may need custom template) |
| deepseek-r1:32b | 19 GB | ✅ Supported | Advanced reasoning with tools |
| command-r:35b | 18 GB | ✅ Native | Optimized for RAG + tool calling |
| phi4:14b | 9.1 GB | ✅ Native | Efficient reasoning with tools |
| gemma3:latest | 3.3 GB | ✅ Native | Lightweight with tool support |
| llama4:scout | 67 GB | ⚠️ Unknown | ❌ Too large - CPU spillover |
| qwq:latest | 19 GB | ❌ No Tools | Pure reasoning only - no MCP tools |

### Recommended Configuration (.env)

```bash
# Primary model - Best balance for RTX 5090

OLLAMA_MODEL=qwen3:30b

# Alternative for RAG + tools

# OLLAMA_MODEL=command-r:35b

# Alternative for faster responses

# OLLAMA_MODEL=qwen3:14b

# For reasoning WITHOUT tools (no MCP access)

# OLLAMA_MODEL=qwq:latest

```

### Why qwen3:30b?

| Feature | Benefit |
|---------|---------|
| MoE Architecture | 30B params, only 3B active = fast inference |
| Tool Calling | ✅ Native support, excellent accuracy |
| Thinking Tags | ✅ Native `<think>` tags for reasoning |
| VRAM Usage | ~18GB fits comfortably in 32GB |
| Speed | Faster than dense 32B models |

### Tool Calling Support Matrix

**✅ Full Tool Calling Support:**
- Qwen3 (all sizes: 4b, 8b, 14b, 30b, 32b)
- Qwen2.5 (all sizes)
- Llama 3.1, 3.2, 3.3, 4 (most variants)
- Mistral, Mixtral, Mistral-Nemo
- Command-R, Command-R-Plus
- Phi-3, Phi-3.5, Phi-4
- Gemma2, Gemma3
- DeepSeek-R1, DeepSeek-Coder-v2
- Firefunction, Hermes, Nous-Hermes

**❌ No Tool Calling:**
- QwQ (reasoning only - cannot use MCP tools)
- Embedding models (bge, nomic-embed)
- Vision-only models

---

## Core Development Principles

### 1. Simplicity First
- Choose straightforward solutions over complex ones
- Avoid over-engineering; implement features only when needed
- Keep files under 500 lines; refactor when approaching this limit

### 2. Type Safety
- Use Pydantic models for all data structures
- Type hint all function signatures
- Validate inputs at boundaries

### 3. Async by Default
- Use `async/await` for all I/O operations
- MCP client operations are inherently async
- Streamlit requires `asyncio.run()` helper

### 4. Local-First Privacy
- All LLM inference via local Ollama instance
- No external API calls for inference
- SQL Server runs in local Docker container

### 5. Preserve Existing Functionality
- New additions must NOT break existing features
- CLI, Streamlit, and React interfaces must remain functional
- Add new files, don't replace working implementations

---

## Configuration

### Environment Variables (.env)

```bash
# Ollama Configuration

# IMPORTANT: For Docker containers, keep this as localhost:11434

# Docker Compose automatically overrides it to http://host.docker.internal:11434

# For local development outside Docker, this value is used directly

OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=qwen3:30b

# Foundry Local Configuration (alternative)

FOUNDRY_ENDPOINT=http://127.0.0.1:53760
FOUNDRY_MODEL=phi-4
FOUNDRY_AUTO_START=true

# SQL Server 2022 - Sample Database (ResearchAnalytics)

SQL_SERVER_HOST=localhost
SQL_SERVER_PORT=1433
SQL_DATABASE_NAME=ResearchAnalytics
SQL_TRUST_SERVER_CERTIFICATE=true
SQL_USERNAME=sa
SQL_PASSWORD=LocalLLM@2024!

# SQL Server 2025 - Backend Database (LLM_BackEnd)

BACKEND_DB_HOST=localhost
BACKEND_DB_PORT=1434
BACKEND_DB_NAME=LLM_BackEnd
BACKEND_DB_USERNAME=        # Defaults to SQL_USERNAME
BACKEND_DB_PASSWORD=        # Defaults to SQL_PASSWORD
BACKEND_DB_TRUST_CERT=true

# Vector Store Configuration

VECTOR_STORE_TYPE=mssql     # mssql (SQL Server 2025) or redis
VECTOR_DIMENSIONS=768       # nomic-embed-text dimensions

# MSSQL MCP Server

MCP_MSSQL_PATH=E:/path/to/SQL-AI-samples/MssqlMcp/Node/dist/index.js
MCP_MSSQL_READONLY=false

# Application Settings

LOG_LEVEL=INFO
STREAMLIT_PORT=8501
DEBUG=false

# Redis Stack (caching + fallback vector store)

REDIS_URL=redis://localhost:6379

# Embeddings

EMBEDDING_MODEL=nomic-embed-text

# RAG Pipeline

CHUNK_SIZE=512
CHUNK_OVERLAP=50
RAG_TOP_K=5

# Document Storage

UPLOAD_DIR=data/uploads
MAX_UPLOAD_SIZE_MB=50

# FastAPI Backend

API_HOST=0.0.0.0
API_PORT=8000

# Superset (Optional)

SUPERSET_URL=http://localhost:8088
SUPERSET_SECRET_KEY=your_secure_key
SUPERSET_ADMIN_USER=admin
SUPERSET_ADMIN_PASSWORD=LocalLLM@2024!
SUPERSET_PORT=8088
```

### MCP Configuration (mcp_config.json)

```json
{
  "mcpServers": {
    "mssql": {
      "command": "node",
      "args": ["${MCP_MSSQL_PATH}"],
      "env": {
        "SERVER_NAME": "${SQL_SERVER_HOST}",
        "DATABASE_NAME": "${SQL_DATABASE_NAME}",
        "TRUST_SERVER_CERTIFICATE": "${SQL_TRUST_SERVER_CERTIFICATE}",
        "READONLY": "${MCP_MSSQL_READONLY}"
      }
    }
  }
}
```

---

## MSSQL MCP Server Tools Reference

| Tool | Description | Example Prompt |
|------|-------------|----------------|
| `list_tables` | Lists all tables in database | "What tables are available?" |
| `describe_table` | Get table schema | "Describe the Researchers table" |
| `read_data` | Query data with conditions | "Show top 10 active projects" |
| `insert_data` | Add new records | "Add a new researcher" |
| `update_data` | Modify existing data | "Update project status to complete" |
| `create_table` | Create new tables | "Create a logs table" |
| `drop_table` | Delete tables | "Remove temp_data table" |
| `create_index` | Add indexes | "Create index on email column" |

---

## Sample Database: ResearchAnalytics

The Docker setup creates a research analytics database with:

| Table | Records | Description |
|-------|---------|-------------|
| Departments | 8 | AI, Data Science, ML, NLP, CV, Robotics, Security, Cloud |
| Researchers | 23 | Staff with titles, salaries, specializations |
| Projects | 14 | Active, completed, planning research projects |
| Publications | 10 | Journal articles, conference papers |
| Datasets | 10 | Training data, sensor data, medical images |
| Experiments | 11 | ML experiments with metrics and results |
| Funding | 12 | NSF, NIH, DARPA, industry grants |
| Equipment | 10 | GPU clusters, drones, workstations |

### Example Queries

```
"What tables are in the database?"
"Show me all active projects with their budgets"
"Who are the top researchers by publication count?"
"What experiments are currently in progress?"
"How much total funding has the ML department received?"
```

---

## Development Patterns

### Pydantic AI Agent with Ollama

```python
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel

# Configure Ollama as OpenAI-compatible provider

model = OpenAIModel(
    model_name="qwen3:30b",
    base_url="http://localhost:11434/v1",
    api_key="ollama"  # Ollama doesn't require real API key
)

# Create agent with MCP toolsets

agent = Agent(
    model=model,
    system_prompt="You are a helpful SQL data analyst...",
    toolsets=[mssql_mcp_server]
)
```

### MCP Server Integration

```python
from pydantic_ai.mcp import MCPServerStdio

mssql_server = MCPServerStdio(
    command="node",
    args=[mcp_path],
    env={
        "SERVER_NAME": "localhost",
        "DATABASE_NAME": "ResearchAnalytics",
        "TRUST_SERVER_CERTIFICATE": "true"
    },
    timeout=30
)
```

### Async Agent Execution

```python
async def run_query(agent: Agent, message: str) -> str:
    async with agent:  # Manages MCP server lifecycle
        result = await agent.run(message)
        return result.output
```

**CRITICAL:** Always use `async with agent:` context manager to establish MCP server connections before calling agent methods.

### Streamlit MCP Session Management

**IMPORTANT:** Streamlit requires wrapping agent calls with the context manager for proper MCP session handling.

```python
# ❌ WRONG - Missing context manager (breaks MCP tools)

async def stream_response():
    async for chunk in agent.chat_stream(prompt):
        full_response += chunk

# ✅ CORRECT - Wrapped in context manager

async def stream_response():
    async with agent:  # Establish MCP session
        async for chunk in agent.chat_stream(prompt):
            full_response += chunk

# ✅ CORRECT - Non-streaming mode

async def chat_with_session():
    async with agent:
        return await agent.chat_with_details(prompt)
```

### Streamlit Async Helper

```python
import asyncio

def run_async(coro):
    """Run async code in Streamlit's sync context."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()
```

**Pattern Differences:**

| Interface | Session Management | Pattern |
|-----------|-------------------|---------|
| **CLI** | Session-level (once per chat session) | `async with agent:` wraps entire while loop |
| **Streamlit** | Message-level (per user message) | `async with agent:` wraps each chat call |
| **FastAPI WebSocket** | Connection-level (per WebSocket) | `async with agent:` wraps connection handler |

---

## MCP Server Management

The project supports **multiple simultaneous MCP servers** with dynamic management via CLI commands. All enabled servers provide their tools to the agent at once.

### Available MCP Servers (Default Configuration)

| Server Name | Type | Transport | Description |
|-------------|------|-----------|-------------|
| **mssql** | MSSQL | stdio | SQL Server 2022 (ResearchAnalytics database) |
| **microsoft.docs.mcp** | Custom | streamable_http | Microsoft Learn documentation search |
| **analytics-management** | Custom | stdio | Dashboard, widget, query management for LLM_BackEnd |
| **data-analytics** | Custom | stdio | Advanced analytics: stats, time series, anomaly detection |
| **archon** | Custom | streamable_http | Project management and knowledge base |

### CLI MCP Commands

**List all servers:**
```bash
/mcp list
# or just

/mcp
```

Shows table with: Name, Type, Transport, Status (enabled/disabled), Description

**Show server details:**
```bash
/mcp status <server-name>
```

Displays:
- Server type and transport
- Command/URL configuration
- Environment variables
- Enabled state
- Timeout settings

**Enable/Disable servers:**
```bash
/mcp enable <server-name>    # Enable server (restart required)
/mcp disable <server-name>   # Disable without removing config
```

**Note:** Changes persist to `mcp_config.json` but require **restarting the chat** to take effect. Hot-reload within a session is not yet supported.

**Add new server interactively:**
```bash
/mcp add
```

Interactive wizard prompts for:
1. Server type (MSSQL, PostgreSQL, MongoDB, Brave Search, Custom)
2. Transport type (stdio, streamable_http, sse)
3. Server name (unique identifier)
4. Connection details:
   - **stdio:** command, args, environment variables
   - **HTTP/SSE:** URL, headers
5. Read-only mode (optional)
6. Description (optional)

**Remove server:**
```bash
/mcp remove <server-name>
```

Prompts for confirmation before removing from config.

**Reconnect failed server:**
```bash
/mcp reconnect <server-name>
```

Attempts to restart a server that failed to connect.

**List available tools (future):**
```bash
/mcp tools [server-name]
```

*Note: Full tool listing requires agent hot-reload implementation.*

### Multi-Server Architecture

**How it works:**
1. `MCPClientManager` loads all server configs from `mcp_config.json`
2. Only **enabled** servers are loaded into agent toolsets
3. Agent receives **combined toolsets** from all enabled servers
4. Agent intelligently selects appropriate tools based on query
5. Server failures are isolated - one failure doesn't break others

**Configuration file:** `mcp_config.json`
- JSON format with Pydantic validation
- Supports environment variable expansion: `${VAR_NAME}` or `${VAR_NAME:-default}`
- Nested variable expansion supported: `${VAR1:-${VAR2}}`

**Transport types:**
- **stdio:** Local subprocess (command + args) - for local MCP servers
- **streamable_http:** HTTP endpoint - for production/remote servers
- **sse:** Server-Sent Events - legacy support

### Example: Adding a Custom MCP Server

```bash
/mcp add

# Interactive prompts:

Server type: custom
Transport: stdio
Name: my-custom-server
Command: node
Args: /path/to/server/index.js
Environment variables (KEY=value, blank to finish):
  MY_VAR=value
  ANOTHER_VAR=value2
  <blank>
Read-only? n
Description: My custom MCP server

✓ Added stdio server: my-custom-server
ℹ Restart chat to activate
```

### Environment Variable Examples

In `mcp_config.json`:
```json
{
  "mcpServers": {
    "mssql": {
      "env": {
        "SERVER_NAME": "${SQL_SERVER_HOST}",
        "DATABASE_NAME": "${SQL_DATABASE_NAME}",
        "USERNAME": "${SQL_USERNAME}",
        "READONLY": "${MCP_MSSQL_READONLY:-false}"
      }
    }
  }
}
```

Variables are resolved from `.env` file at startup.

---

## Workflow Commands

### Development

```bash
# Install dependencies

uv sync

# Run CLI chat

uv run python -m src.cli.chat

# Run Streamlit UI

uv run streamlit run src/ui/streamlit_app.py

# Run FastAPI backend

uv run uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000

# Run tests

uv run pytest tests/ -v

# Format code

uv run ruff format .

# Lint

uv run ruff check .
```

### React Frontend

```bash
# Install frontend dependencies

cd frontend && npm install

# Run development server (port 5173)

npm run dev

# Build for production

npm run build

# Preview production build

npm run preview

# Lint frontend code

npm run lint
```

**Frontend URLs:**
- Development: http://localhost:5173
- API Proxy: Requests to `/api/*` and `/ws/*` are proxied to FastAPI backend

### Docker Services

**⚠️ CRITICAL: When running from project root, ALWAYS include `--env-file .env`:**

```bash
# From project root - Start all services (SQL Server 2022/2025 + Redis Stack)

docker-compose -f docker/docker-compose.yml --env-file .env up -d

# Initialize sample database - ResearchAnalytics (first time)

docker-compose -f docker/docker-compose.yml --env-file .env --profile init up mssql-tools

# Initialize backend database - LLM_BackEnd with native vectors (first time)

docker-compose -f docker/docker-compose.yml --env-file .env --profile init up mssql-backend-tools

# Start with FastAPI backend

docker-compose -f docker/docker-compose.yml --env-file .env --profile api up -d

# Start with Superset

docker-compose -f docker/docker-compose.yml --env-file .env --profile superset up -d

# Start full stack

docker-compose -f docker/docker-compose.yml --env-file .env --profile full up -d

# Stop all services

docker-compose -f docker/docker-compose.yml down

# Stop and remove data

docker-compose -f docker/docker-compose.yml down -v
```

**Why `--env-file .env`?** Docker Compose looks for `.env` in the same directory as the compose file. Since `docker-compose.yml` is in `docker/` but `.env` is in project root, you must explicitly specify it.

### Database Migrations (Alembic)

```bash
# Generate new migration

uv run alembic revision --autogenerate -m "description"

# Apply migrations

uv run alembic upgrade head

# Rollback one migration

uv run alembic downgrade -1

# View migration history

uv run alembic history
```

### MSSQL MCP Server Setup

```bash
# Clone MSSQL MCP Server

git clone https://github.com/Azure-Samples/SQL-AI-samples.git
cd SQL-AI-samples/MssqlMcp/Node
npm install

# Note path to dist/index.js for .env

```

---

## Service Ports

| Service | Port | URL | Notes |
|---------|------|-----|-------|
| React UI | 5173 | http://localhost:5173 | |
| FastAPI | 8200 | http://localhost:8200 | Changed from 8000 to avoid conflicts |
| Streamlit | 8501 | http://localhost:8501 | |
| Redis Stack | 6390 | localhost:6390 | Changed from 6379 to avoid conflicts |
| RedisInsight | 8008 | http://localhost:8008 | Changed from 8001 to avoid conflicts |
| Superset | 8288 | http://localhost:8288 | Changed from 8088 to avoid conflicts |
| SQL Server 2022 (Sample) | 1433 | localhost:1433 | |
| SQL Server 2025 (Backend) | 1434 | localhost:1434 | |

**Note:** Ports can be customized in `.env` file using `API_PORT`, `REDIS_PORT`, `REDIS_INSIGHT_PORT`, and `SUPERSET_PORT` variables.

---

## API Endpoints

| Route | Description |
|-------|-------------|
| `/api/health` | Health checks, metrics, service status |
| `/api/documents` | Document upload, listing, delete |
| `/api/documents/{id}/reprocess` | Reprocess failed/completed documents |
| `/api/documents/search` | RAG vector search |
| `/api/conversations` | Chat history CRUD |
| `/api/queries` | Query history, saved queries, favorites |
| `/api/dashboards` | Dashboard and widget management |
| `/api/mcp` | MCP server status, tool listing |
| `/api/mcp/{id}/enable` | Enable MCP server |
| `/api/mcp/{id}/disable` | Disable MCP server |
| `/api/settings` | Theme config, app settings |
| `/api/settings/providers` | List available LLM providers |
| `/api/agent` | Agent chat endpoint |
| `/ws/agent/{conversation_id}` | Real-time WebSocket chat |
| `/api/superset/health` | Superset status |
| `/api/superset/dashboards` | List Superset dashboards |
| `/api/superset/embed/{id}` | Get embed URL with guest token |
| `/api/auth/register` | User registration (POST) |
| `/api/auth/login` | User authentication, returns JWT tokens (POST) |
| `/api/auth/refresh` | Refresh access token using refresh token (POST) |
| `/api/auth/logout` | Invalidate refresh token (POST) |
| `/api/auth/me` | Get current user profile (GET) |
| `/api/auth/change-password` | Change user password (POST) |
| `/api/analytics/*` | Analytics and metrics endpoints |
| `/api/database-connections` | Database connection management |

---

## Testing Guidelines

### Run Tests

```bash
# All tests

uv run pytest tests/ -v

# Specific test file

uv run pytest tests/test_agent.py -v

# With coverage

uv run pytest tests/ --cov=src --cov-report=html
```

### Test Patterns

```python
import pytest
from unittest.mock import AsyncMock

@pytest.mark.asyncio
async def test_agent_responds():
    agent = create_test_agent()
    result = await agent.run("Hello")
    assert result.output is not None

@pytest.mark.integration
@pytest.mark.asyncio
async def test_mssql_connection():
    async with mssql_server:
        tools = await mssql_server.list_tools()
        assert any(t.name == "list_tables" for t in tools)
```

---

## Security Considerations

1. **Never commit .env files** - Use .env.example as template
2. **SQL Server credentials** - Store in environment variables only
3. **Docker secrets** - Use MSSQL_SA_PASSWORD from .env
4. **Input validation** - Always validate user inputs before SQL operations
5. **Read-only mode** - Use `MCP_MSSQL_READONLY=true` for safe exploration

---

## Troubleshooting

### Docker Connectivity to Host Ollama

**Problem:** Docker containers cannot reach Ollama running on the host machine.

**Solution:** The docker-compose.yml is now configured to automatically use `http://host.docker.internal:11434` for all containers, regardless of what's in your `.env` file. This ensures Docker containers always connect to the host correctly.

**Verification:**
```bash
# 1. Check Ollama is running on host

curl http://localhost:11434/api/tags

# 2. Test from inside a container

docker compose -f docker/docker-compose.yml --env-file .env exec agent-ui \
  curl http://host.docker.internal:11434/api/tags

# 3. Or use the test script

docker compose -f docker/docker-compose.yml --env-file .env exec agent-ui \
  bash /app/docker/test-ollama-connection.sh
```

**Windows Firewall:** If still not working, ensure Windows Firewall allows Docker containers to access port 11434:
```powershell
# Allow Ollama through Windows Firewall

New-NetFirewallRule -DisplayName "Ollama API" -Direction Inbound -LocalPort 11434 -Protocol TCP -Action Allow
```

### Ollama Issues

```bash
# Check Ollama is running

curl http://localhost:11434/api/tags

# List models

ollama list

# Pull model if missing

ollama pull qwen3:30b

# Check model supports tools

curl http://localhost:11434/api/show -d '{"name":"qwen3:30b"}' | jq '.template'
```

### Foundry Local Issues

```bash
# Check Foundry Local is running

curl http://127.0.0.1:53760/v1/models

# Start a model

foundry model run phi-4

# Check model status

foundry service status
```

### Docker SQL Server Issues

```bash
# Check container status

docker ps -a | grep mssql

# View logs

docker logs local-agent-mssql

# Restart container

docker compose restart mssql
```

### Redis Stack Issues

```bash
# Check container status

docker ps -a | grep redis

# View logs

docker logs local-agent-redis

# Test Redis connection

redis-cli ping

# View RedisInsight GUI

# Open http://localhost:8001

# Restart Redis

docker compose restart redis-stack
```

### FastAPI Issues

```bash
# Test API is running

curl http://localhost:8000/api/health

# View API docs

# Open http://localhost:8000/docs (Swagger)

# Open http://localhost:8000/redoc (ReDoc)

# Check import errors

uv run python -c "from src.api.main import app; print('OK')"
```

### MCP Server Issues

```bash
# Test MSSQL MCP directly

node E:/path/to/SQL-AI-samples/MssqlMcp/Node/dist/index.js

# Check Node.js version

node --version  # Should be 18+
```

### Connection Issues

- Ensure SQL Server containers are running: `docker ps | grep mssql`
- Check ports 1433 (sample) and 1434 (backend) are not blocked
- Verify credentials match docker-compose.yml
- Test sample database: `sqlcmd -S localhost,1433 -U sa -P "LocalLLM@2024!" -d ResearchAnalytics`
- Test backend database: `sqlcmd -S localhost,1434 -U sa -P "LocalLLM@2024!" -d LLM_BackEnd`

---

## Remember

- **ALWAYS** use Archon for task management before coding
- **ALWAYS** use `async with agent:` to manage MCP server lifecycle
- **VERIFY** Ollama is running before starting the application
- **TEST** existing interfaces after any changes
- Use `qwen3:30b` as primary model for your RTX 5090
- Keep conversation history for context in multi-turn interactions

---

## Optional: Archon RAG

> **Skip this section unless you have a substantial private/internal corpus** that genuinely needs vector search. For library docs (FastAPI, React, Pydantic, etc.), use the `project-kb` skill — it wraps Context7 MCP, which already indexes 1000+ libraries with fresher content than any local corpus.

For projects with extracted internal documentation:

1. Drop markdown files in `.claude/kb/` (gitignored if confidential, committed if public).
2. The `project-kb` skill will grep them automatically.
3. No vector store, no MCP server, no background indexing — just filesystem search with `Grep`.

If you genuinely need vector retrieval (semantic similarity, fuzzy concept matching across a large private corpus), evaluate options like LanceDB-on-disk or a self-hosted Qdrant — but that's a deliberate, scoped infrastructure decision, not a default.

---

