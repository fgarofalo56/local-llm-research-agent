# Root Directory Structure

## ✅ Current Organization (After Cleanup)

### Essential Configuration Files
```
.
├── pyproject.toml          # Python project configuration
├── requirements.txt        # Pip dependencies fallback
├── uv.lock                 # UV dependency lock file
├── package-lock.json       # Frontend dependency lock
├── alembic.ini            # Database migrations config
├── mcp_config.json        # MCP server configuration
├── .env                   # Local environment (git-ignored)
├── .env.example           # Environment template
├── .gitignore             # Git ignore rules
├── .dockerignore          # Docker ignore rules
└── Dockerfile             # Container definition
```

### Development Scripts
```
├── start-dev.bat          # Windows dev startup
├── start-dev.sh           # Linux/Mac dev startup
├── stop-dev.bat           # Windows dev shutdown
└── stop-dev.sh            # Linux/Mac dev shutdown
```

### Documentation (Root Level)
```
├── README.md              # Main project documentation
├── CLAUDE.md              # AI assistant context
├── CONTRIBUTING.md        # Contribution guidelines
├── LICENSE                # Project license
└── SECURITY.md            # Security policy
```

### Key Directories
```
├── src/                   # Main application source code
├── tests/                 # Formal pytest unit/integration tests
├── examples/              # Usage examples and demos
├── scripts/               # Utility scripts
│   ├── debug/            # Quick debug/verify scripts
│   └── testing/          # Integration test scripts
├── docs/                  # Extended documentation
│   ├── sessions/         # Session summaries archive
│   ├── mcp/              # MCP documentation
│   ├── api/              # API documentation
│   └── guides/           # User guides
├── docker/               # Docker compose and init scripts
├── frontend/             # React application
├── alembic/              # Database migrations
├── data/                 # Data storage (uploads, models)
├── config/               # Additional configuration
└── PRPs/                 # Product Requirement Prompts
```

## 🧹 Cleanup Actions Taken

### 1. Moved Test Scripts
**From:** Root directory  
**To:** `scripts/testing/`

- test_agent_mcp_visibility.py
- test_agent_tools.py
- test_cli_quick.py
- test_cli_session_debug.py
- test_cli_transports.py
- test_http_sse_servers.py
- test_mcp_commands.py
- test_mcp_context.py
- test_session_fix.py
- test_tool_visibility.py
- test_transport_types.py
- test_universal_agent.py

### 2. Moved Debug Scripts
**From:** Root directory  
**To:** `scripts/debug/`

- debug_prompt.py
- quick_test.py
- quick_endpoint_test.py
- verify_prompt.py

### 3. Organized Documentation
**From:** Root directory  
**To:** `docs/sessions/`

- SESSION_COMPLETION_SUMMARY.md
- SESSION_SUMMARY.md

**To:** `docs/mcp/`

- MCP_SESSION_BUG_FIX.md
- MCP_CONFIG_FIX.md
- MCP_AWARENESS_SUMMARY.md
- MCP_CONFIGURATION_REFERENCE.md
- TRANSPORT_TYPES_IMPLEMENTATION.md
- EXTERNAL_MCP_INTEGRATION.md

**To:** `docs/`

- TESTING.md
- TESTING_TASKS.md

### 4. Deleted Temporary Files
- nul (empty file)
- pyproject.toml.bak (backup)
- apply_session_fix.py (one-time script)
- ROOT_ORGANIZATION.md (planning doc)

### 5. Updated .gitignore
Added patterns for:
- *.bak (backup files)
- *.tmp, *.swp, *~ (temporary files)
- nul (empty file)
- /SESSION_*.md (session summaries in root)

## 📁 Directory Purpose Guide

| Directory | Purpose | File Types |
|-----------|---------|------------|
| `src/` | Production code | `.py` modules |
| `tests/` | Formal test suite | `test_*.py` with pytest |
| `examples/` | Educational demos | Standalone `.py` scripts |
| `scripts/debug/` | Quick debug tools | `debug_*.py`, `quick_*.py`, `verify_*.py` |
| `scripts/testing/` | Integration tests | `test_*.py` full-stack scripts |
| `docs/` | Documentation | `.md` files |
| `docker/` | Docker configs | `docker-compose.yml`, `Dockerfile.*`, init scripts |

## 🎯 File Placement Rules

### ✅ Should Be in Root
- Essential config: `pyproject.toml`, `requirements.txt`, `.env`, `mcp_config.json`
- Docker: `Dockerfile`, `.dockerignore`
- Git: `.gitignore`, `.pre-commit-config.yaml`
- Docs: `README.md`, `CLAUDE.md`, `CONTRIBUTING.md`, `LICENSE`, `SECURITY.md`
- Dev scripts: `start-dev.*`, `stop-dev.*`
- Key directories: `src/`, `tests/`, `examples/`, `scripts/`, `docs/`, `docker/`

### ❌ Should NOT Be in Root
- Test scripts → `scripts/testing/` or `tests/`
- Debug scripts → `scripts/debug/`
- Session docs → `docs/sessions/`
- Implementation guides → `docs/mcp/`, `docs/guides/`
- Temporary files → Delete or ensure in `.gitignore`
- Backup files (*.bak) → Delete or ensure in `.gitignore`

## 🔍 Quick Checks

### Is Root Clean?
```bash
# List only files (not directories) in root
ls -la | grep "^-"

# Should see ~25-30 files (mostly config, docs, scripts)
# Should NOT see: test_*.py, debug_*.py, *.bak, SESSION_*.md
```

### Are Scripts Organized?
```bash
# Check script directories exist
ls scripts/debug/
ls scripts/testing/

# Should have README.md in each
```

### Is Documentation Organized?
```bash
# Check docs subdirectories
ls docs/sessions/
ls docs/mcp/

# Should have README.md in each
```

## 📚 Related Files

- **For developers:** `CONTRIBUTING.md`
- **For AI assistants:** `CLAUDE.md`
- **For users:** `README.md`
- **For scripts:** `scripts/debug/README.md`, `scripts/testing/README.md`
- **For MCP:** `docs/mcp/README.md`
