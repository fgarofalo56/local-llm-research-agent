# Session Memory & Context
**Project:** Local LLM Research Analytics Tool
**Project ID (Archon):** 16394505-e6c5-4e24-8ab4-97bd6a650cfb
**Archon Memory Document ID:** cc0eead5-1738-45d4-bd66-623cde0dafb3
**Last Updated:** 2026-01-08T04:14:54Z
**Session Started:** 2026-01-08T04:14:34Z

---

## ✅ Memory System Active

**Primary:** Archon MCP Server (Document ID: cc0eead5-1738-45d4-bd66-623cde0dafb3)
**Fallback:** Local .context/SESSION_MEMORY.md (this file)

Both systems are synced. Archon provides structured query access, local file provides human-readable backup.

---

## Current State Summary

### Working Tree Status
- **Branch:** main
- **Uncommitted Changes:** 62 modified files
- **Last Commit:** c41d53e - "feat(startup): Add --docker flag for full Docker deployment"

### Recent Work (Last 5 Commits)
1. `c41d53e` - feat(startup): Add --docker flag for full Docker deployment
2. `cbb7116` - feat(startup): Add comprehensive startup/stop scripts and UI improvements
3. `14db0bb` - fix(ui): Fix dropdown transparency and enable Attach button
4. `047fc1b` - fix(security): Replace vulnerable xlsx with exceljs and update jspdf
5. `05bfad1` - chore: Add host agent scripts and update dependencies

---

## Modified Files by Category

### Database & Migrations (10 files)
- `alembic/env.py`
- `alembic/versions/20251212_021031_7634261e3e9e_initial_phase2_tables.py`
- `alembic/versions/20251212_add_tags_to_documents.py`
- `alembic/versions/20251218_210131_b239d72597ab_add_performance_indexes.py`
- `alembic/versions/20251218_214611_805336405b97_add_database_connections_table.py`
- `alembic/versions/20251218_220325_cc0879b502ec_add_users_and_refresh_tokens.py`
- `alembic/versions/20260102_234639_a42a71aaaead_add_account_lockout_fields.py`
- `docker/superset/superset_config.py`

### Frontend (8 files)
- `frontend/src/components/charts/KPICard.tsx`
- `frontend/src/components/chat/AgentStatusIndicator.tsx`
- `frontend/src/components/chat/ChatInput.tsx`
- `frontend/src/components/ui/Skeleton.tsx`
- `frontend/src/contexts/AuthContext.tsx`
- `frontend/src/pages/ChatPage.tsx`
- `frontend/src/pages/DocumentsPage.tsx`
- `frontend/src/pages/SettingsPage.tsx`

### Backend API (8 files)
- `src/api/deps.py`
- `src/api/routes/agent.py`
- `src/api/routes/analytics.py`
- `src/api/routes/auth.py`
- `src/api/routes/mcp_servers.py`
- `src/api/routes/settings.py`
- `src/api/websocket/connection.py`
- `src/api/websocket/manager.py`

### Agent & MCP (5 files)
- `src/agent/context.py`
- `src/agent/research_agent.py`
- `src/mcp/analytics_mcp_server.py`
- `src/mcp/data_analytics_mcp_server.py`
- `src/mcp/dynamic_manager.py`

### RAG & Vector Store (7 files)
- `src/rag/docling_processor.py`
- `src/rag/document_processor.py`
- `src/rag/embedder.py`
- `src/rag/mssql_vector_store.py`
- `src/rag/redis_vector_store.py`
- `src/rag/vector_store_base.py`
- `src/rag/vector_store_factory.py`

### Services (4 files)
- `src/services/alert_scheduler.py`
- `src/services/document_service.py`
- `src/services/query_scheduler.py`
- `src/services/query_service.py`

### Providers & Auth (3 files)
- `src/providers/base.py`
- `src/providers/foundry.py`
- `src/auth/jwt.py`

### Utils (5 files)
- `src/utils/cache.py`
- `src/utils/config.py`
- `src/utils/query_profiler.py`
- `src/utils/retry.py`

### Streamlit UI (3 files)
- `src/ui/pages/1_Documents.py`
- `src/ui/pages/2_MCP_Servers.py`
- `src/ui/pages/3_Settings.py`

### Examples (5 files)
- `examples/basic_chat.py`
- `examples/query_profiler_example.py`
- `examples/redis_cache_example.py`
- `examples/retry_example.py`
- `examples/websocket_manager_example.py`

### Scripts & Tests (9 files)
- `scripts/host_agent.py`
- `tests/performance/locustfile.py`
- `tests/test_document_processor_errors.py`
- `tests/test_query_profiler.py`
- `tests/test_rag_integration.py`
- `tests/test_redis_cache.py`
- `tests/test_retry.py`
- `tests/test_settings_database.py`
- `tests/test_vector_store_refactor.py`
- `tests/test_websocket.py`

### Configuration (1 file)
- `CLAUDE.md`

---

## Active Tasks (To Be Synced with Archon)

### Status: UNKNOWN
Need to query Archon server for current task status once connectivity is established.

**Project ID:** 16394505-e6c5-4e24-8ab4-97bd6a650cfb

---

## Key Context for Next Session

### What Was Being Worked On?
Based on file modifications, recent work appears to focus on:
1. **Authentication System** - JWT tokens, user accounts, lockout fields
2. **Database Migrations** - Multiple Alembic migrations for new tables
3. **Frontend Components** - React components for chat, documents, settings
4. **RAG Pipeline** - Vector store refactoring, document processing
5. **MCP Integration** - Analytics MCP servers, dynamic manager
6. **Performance** - Query profiling, caching, retry logic
7. **WebSocket** - Real-time chat connections

### Likely Next Steps
- **Commit Strategy:** 62 files suggest this might need to be broken into multiple logical commits
- **Testing:** Changes should be tested before committing
- **Documentation:** Updates may be needed for new features

---

## MCP Servers Configuration

### Available in .mcp.json
1. **Archon** - http://localhost:8051/mcp (Task & Knowledge Management)
2. **Serena** - IDE Assistant context
3. **Microsoft Docs** - https://learn.microsoft.com/api/mcp
4. **Brave Search** - Web search (requires BRAVE_API_KEY)
5. **Playwright** - Browser automation

### Status
- Archon server appears to be running (returns 406 error - may need proper MCP client)
- Other servers not tested yet

---

## Environment Information

### Hardware
- CPU: AMD Ryzen 9 5950X (16-Core, 32 Threads)
- RAM: 128 GB DDR4
- GPU: NVIDIA RTX 5090 (32GB VRAM)
- OS: Windows 11 Enterprise

### Primary Model
- **Current:** qwen3:30b (MoE, 18GB VRAM, excellent tool calling)

### Services Ports
- React UI: 5173
- FastAPI: 8000
- Streamlit: 8501
- SQL Server 2022 (Sample): 1433
- SQL Server 2025 (Backend): 1434
- Redis Stack: 6379
- RedisInsight: 8001
- Superset: 8088
- Archon: 8051

---

## Session Notes

### Session 2026-01-08
- User requested to resume last session
- Identified 62 uncommitted files from previous work
- User wants to use Archon for memory/context management
- Created this SESSION_MEMORY.md file as fallback memory system
- Archon server running and fully operational
- **✅ Created comprehensive quick commands system** (10 slash commands)
- **✅ Commands location:** `.claude/commands/base_commands/`
- **✅ Available commands:** /start, /next, /status, /save, /end, /lint, /test, /services, /commit, /refresh-statusline

### Action Items
1. ✅ Created local memory document
2. ⏳ Need to establish Archon connectivity for task management
3. ⏳ Need to analyze uncommitted changes in detail
4. ⏳ Need to determine commit strategy
5. ⏳ Need to run tests on changes

---

## Quick Reference Commands

### Resume Context
```bash
# Check git status
git status

# View recent commits
git log --oneline -10

# Check what changed
git diff --stat
```

### Start Services
```bash
# Docker services
docker-compose -f docker/docker-compose.yml --env-file .env up -d

# FastAPI
uv run uvicorn src.api.main:app --reload

# React Frontend
cd frontend && npm run dev

# Streamlit
uv run streamlit run src/ui/streamlit_app.py
```

### Task Management (Once Archon is connected)
```bash
# Find project tasks
find_tasks(filter_by="project", filter_value="16394505-e6c5-4e24-8ab4-97bd6a650cfb")

# Get task details
find_tasks(task_id="...")

# Update task status
manage_task("update", task_id="...", status="doing")
```

---

## Memory System Instructions

**For Future Sessions:** Read this file first to understand:
- What was being worked on
- Current state of the repository
- Active tasks and priorities
- Key context and decisions

**⚠️ CRITICAL: SKILLS-FIRST RULE**
**BEFORE implementing ANY feature or solution:**
1. Check `C:\Users\frgarofa\.claude\skills\` for relevant expertise
2. Read the SKILL.md file for that technology/pattern
3. Apply the patterns and best practices from the skill
4. **NEVER skip this step** - 169 skills available covering everything from pydantic-ai to react-typescript to context-engineering

**Available Skills Include:**
- pydantic-ai, mcp-development, ollama, mssql-mcp, azure-mcp
- rag-patterns, react-typescript, streamlit-dashboards, vector-databases
- pytest-advanced, context-engineering, prompt-engineering
- docker-kubernetes, github-actions, terraform-iac
- And 150+ more covering nearly every technology in this project

**Update This File When:**
- Starting significant new work
- Completing major features
- Making architectural decisions
- Switching focus areas
- Before ending a session

---

*This file serves as persistent memory across Copilot CLI sessions. Always read and update it to maintain context.*
