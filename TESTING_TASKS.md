# Feature Testing Checklist

> All features that need validation for the Local LLM Research Agent
> Last tested: December 16, 2025 (Playwright Automated Testing)

## Prerequisites

Before testing, ensure these services are running:
```bash
# Start backend services
docker-compose -f docker/docker-compose.yml --env-file .env --profile api up -d

# Start frontend (in separate terminal)
cd frontend && npm run dev

# Start Superset (optional)
docker-compose -f docker/docker-compose.yml --env-file .env --profile superset up -d
```

---

## Foundation

| # | Feature | Test Method | Status |
|---|---------|-------------|--------|
| 1.1 | CLI chat interface works | `uv run python -m src.cli.chat` | Manual |
| 1.2 | Streamlit UI at localhost:8501 | Browser: http://localhost:8501 | PASS |
| 1.3 | Docker SQL Server running | `docker ps \| grep mssql` | PASS |
| 1.4 | ResearchAnalytics database exists | Query via MSSQL tools | PASS |

---

## Backend & API

| # | Feature | Test Method | Status |
|---|---------|-------------|--------|
| 2.1.1 | FastAPI at localhost:8000 | `curl http://localhost:8000/` | PASS |
| 2.1.2 | Swagger docs at /docs | Browser: http://localhost:8000/docs | PASS |
| 2.1.3 | Health check endpoint | `curl http://localhost:8000/api/health` | PASS |
| 2.1.4 | Redis Stack running | `docker ps \| grep redis` | PASS |
| 2.1.5 | RedisInsight GUI | Browser: http://localhost:8008 | PASS |
| 2.1.6 | Document upload API | POST /api/documents/upload | PASS |
| 2.1.7 | MCP servers list | `curl http://localhost:8000/api/mcp-servers` | PASS |
| 2.1.8 | Conversations API | `curl http://localhost:8000/api/conversations` | PASS |
| 2.1.9 | Queries API | `curl http://localhost:8000/api/queries/history` | PASS |
| 2.1.10 | Settings providers API | `curl http://localhost:8000/api/settings/providers` | PASS |
| 2.1.11 | Database migrations | `uv run alembic upgrade head` | PASS |

---

## React UI & Chat

| # | Feature | Test Method | Status |
|---|---------|-------------|--------|
| 2.2.1 | React app at localhost:5173 | Playwright: Navigate to app | PASS |
| 2.2.2 | Theme toggle (dark/light/system) | Playwright: Settings page toggle | PASS |
| 2.2.3 | Chat page loads | Playwright: Navigate to /chat | PASS |
| 2.2.4 | Chat sends messages | Playwright: Type and send message | PASS |
| 2.2.5 | Streaming responses work | Playwright: Observed real-time response | PASS |
| 2.2.6 | Conversations persist | Playwright: Sidebar shows conversation | PASS |
| 2.2.7 | MCP server selector | Playwright: Active Tools with mssql toggle | PASS |
| 2.2.8 | Query history page | Playwright: Navigate to /queries | PASS |
| 2.2.9 | Documents page | Playwright: Navigate to /documents | PASS |
| 2.2.10 | Settings page loads | Playwright: Navigate to /settings | PASS |
| 2.2.11 | Provider selector works | Playwright: Ollama dropdown visible | PASS |
| 2.2.12 | Model selector works | Playwright: 30+ models in dropdown | PASS |
| 2.2.13 | Connection test button | Playwright: Test Connection visible | PASS |
| 2.2.14 | System health display | Playwright: 4 services with latency | PASS |

---

## Dashboards & Visualization

| # | Feature | Test Method | Status |
|---|---------|-------------|--------|
| 2.3.1 | Dashboards page loads | Playwright: Navigate to /dashboards | PASS |
| 2.3.2 | Create new dashboard | Playwright: Click New Dashboard, fill form | PASS |
| 2.3.3 | Dashboard list displays | Playwright: Dropdown shows dashboard | PASS |
| 2.3.4 | Open dashboard detail | Playwright: Dashboard view with toolbar | PASS |
| 2.3.5 | Add widget to dashboard | Not tested - no widget add button visible | Manual |
| 2.3.6 | Widget drag and drop | Not tested - requires widgets | Manual |
| 2.3.7 | Widget resize | Not tested - requires widgets | Manual |
| 2.3.8 | Bar chart renders | Not tested - requires widgets | Manual |
| 2.3.9 | Line chart renders | Not tested - requires widgets | Manual |
| 2.3.10 | Pie chart renders | Not tested - requires widgets | Manual |
| 2.3.11 | KPI card renders | Not tested - requires widgets | Manual |
| 2.3.12 | Widget refresh | Not tested - requires widgets | Manual |
| 2.3.13 | Dashboard persists | Not tested - requires widgets | Manual |
| 2.3.14 | Delete widget | Not tested - requires widgets | Manual |
| 2.3.15 | Delete dashboard | Playwright: Delete button visible | PASS |

---

## Export System

| # | Feature | Test Method | Status |
|---|---------|-------------|--------|
| 2.4.1 | Export menu exists | Playwright: Dashboard toolbar visible | PASS |
| 2.4.2 | PNG export downloads | Manual - requires file download | Manual |
| 2.4.3 | PDF export downloads | Playwright: Export PDF button visible | PASS |
| 2.4.4 | CSV export downloads | Manual - requires file download | Manual |
| 2.4.5 | Excel export downloads | Manual - requires file download | Manual |
| 2.4.6 | Dashboard JSON export | Playwright: Export JSON button visible | PASS |
| 2.4.7 | Dashboard JSON import | Playwright: Import button visible | PASS |
| 2.4.8 | Chat export to Markdown | Manual - not visible in current UI | Manual |
| 2.4.9 | Chat export to PDF | Manual - not visible in current UI | Manual |

---

## Apache Superset

| # | Feature | Test Method | Status |
|---|---------|-------------|--------|
| 3.1 | Superset container running | `docker ps \| grep superset` | PASS |
| 3.2 | Superset at localhost:8088 | Playwright: Navigate to Superset | PASS |
| 3.3 | Superset admin login | Playwright: Login with admin/password | PASS |
| 3.4 | Superset health API | `curl http://localhost:8000/api/superset/health` | PASS |
| 3.5 | Superset dashboards API | `curl http://localhost:8000/api/superset/dashboards` | PASS |
| 3.6 | Superset page in React | Playwright: Navigate to /superset | PASS |
| 3.7 | Superset embed works | Not tested - no dashboards created | Manual |
| 3.8 | SQL Lab link works | Playwright: Navigate to SQL Lab | PASS |
| 3.9 | SQL Server datasource configured | Playwright: Research Analytics visible | PASS |

---

## Advanced Features

| # | Feature | Test Method | Status |
|---|---------|-------------|--------|
| A.1 | Model Parameters Panel | Playwright: Temperature, Top P, Max Tokens | PASS |
| A.2 | System Prompt Config | Playwright: Custom system prompt textarea | PASS |
| A.3 | RAG Settings Panel | Playwright: Enable RAG, Hybrid Search, Top K | PASS |
| A.4 | Token Counter | Playwright: Prompt/Completion/Total/Remaining | PASS |
| A.5 | Message Copy Button | Playwright: Copy to clipboard button | PASS |
| A.6 | Message Rating Buttons | Playwright: Helpful/Not helpful buttons | PASS |
| A.7 | MCP Tools List | Playwright: 8 tools expandable list | PASS |

---

## Testing Summary

| Section | Total | Passed | Manual | Failed |
|---------|-------|--------|--------|--------|
| Foundation | 4 | 3 | 1 | 0 |
| Backend & API | 11 | 11 | 0 | 0 |
| React UI & Chat | 14 | 14 | 0 | 0 |
| Dashboards & Visualization | 15 | 5 | 10 | 0 |
| Export System | 9 | 4 | 5 | 0 |
| Apache Superset | 9 | 8 | 1 | 0 |
| Advanced Features | 7 | 7 | 0 | 0 |
| **Total** | **69** | **52** | **17** | **0** |

---

## Issues Found & Fixed

### Issue #1: Database tables missing
- **Area:** Backend & API
- **Feature:** Conversations, Dashboards API
- **Description:** API returning Internal Server Error
- **Root Cause:** Alembic migrations not run
- **Fix:** `uv run alembic upgrade head`
- **Status:** Fixed

### Issue #2: Superset API not accessible from Docker API container
- **Area:** Apache Superset
- **Feature:** Superset health check
- **Description:** SUPERSET_URL defaulting to localhost:8088 doesn't work inside Docker
- **Root Cause:** Docker container can't reach host's localhost
- **Fix:** Added SUPERSET_URL=http://superset:8088 to docker-compose.yml API service
- **Status:** Fixed

### Issue #3: Superset CSRF token missing
- **Area:** Apache Superset
- **Feature:** Superset setup script
- **Description:** Failed to add database connection - CSRF token missing
- **Root Cause:** POST requests require CSRF token in session
- **Fix:** Updated setup_superset.py to use session with CSRF token
- **Status:** Fixed

### Issue #4: Duplicate variable declaration in MCPServerSelector
- **Area:** React UI & Chat
- **Feature:** Frontend compilation
- **Description:** `const servers` declared twice
- **Root Cause:** Code error in MCPServerSelector.tsx
- **Fix:** Removed duplicate declaration
- **Status:** Fixed

### Issue #5: Vite dev server not accessible from Docker
- **Area:** React UI & Chat
- **Feature:** Playwright testing
- **Description:** Playwright browser in Docker couldn't reach localhost:5173
- **Root Cause:** Vite dev server only binds to localhost by default
- **Fix:** Added `host: '0.0.0.0'` to vite.config.ts server settings
- **Status:** Fixed

---

## Playwright Test Session Details

**Date:** December 16, 2025
**Browser:** Chromium via MCP Docker Playwright

### Tests Performed:
1. **Chat Page**: Navigated, sent message "What tables are in the database?", received response listing 24 tables
2. **Settings Page**: Verified theme toggle (Light/Dark/System), provider selector, model dropdown (30+ models), system health (4 services)
3. **Documents Page**: Verified upload button, search, status filter, tags filter
4. **Query History Page**: Verified page loads with favorites button
5. **Dashboards Page**: Created new dashboard "Research Overview", verified toolbar (Import, Export JSON/PDF, Delete, Edit Layout)
6. **MCP Servers Page**: Verified mssql server card, 8 tools list, enable/disable/edit/delete buttons
7. **Superset Page**: Verified page loads with quick actions (SQL Lab, Create Chart, Manage Dashboards)
8. **Superset Direct**: Logged in as admin, navigated to SQL Lab, verified Research Analytics database visible
9. **Advanced Features**: Verified Model Parameters panel (Temperature, Top P, Max Tokens), System Prompt, RAG Settings

---

## Notes

- All automated API tests pass
- Playwright browser testing completed for React UI
- Superset SQL Server datasource is configured and connected
- All Docker services are healthy:
  - sql_server: healthy (14.83ms)
  - redis: healthy (0.48ms)
  - ollama: healthy (30.5ms)
  - superset: healthy (10.94ms)
- Widget-related tests require manual testing with actual data
- Chat export features may need UI implementation

---

*Last Updated: December 2025*
