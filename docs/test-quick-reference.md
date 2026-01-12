# Quick Test Reference - MCP Management

## Run All MCP Tests
```bash
uv run pytest tests/test_mcp_management.py -v
```

## Run Specific Test Classes
```bash
# CRUD operations
uv run pytest tests/test_mcp_management.py::TestMCPClientManagerCRUD -v

# Config persistence
uv run pytest tests/test_mcp_management.py::TestMCPConfigPersistence -v

# Multi-server support
uv run pytest tests/test_mcp_management.py::TestMCPMultiServerSupport -v

# Environment variables
uv run pytest tests/test_mcp_management.py::TestMCPEnvironmentVariables -v

# Server validation
uv run pytest tests/test_mcp_management.py::TestMCPServerValidation -v

# Agent integration
uv run pytest tests/test_mcp_management.py::TestMCPAgentIntegration -v

# CLI commands
uv run pytest tests/test_mcp_management.py::TestMCPCLICommands -v

# Error handling
uv run pytest tests/test_mcp_management.py::TestMCPErrorHandling -v
```

## Run Individual Tests
```bash
# Example: Test adding a server
uv run pytest tests/test_mcp_management.py::TestMCPClientManagerCRUD::test_add_server -v
```

## Coverage Analysis
```bash
# Generate coverage report
uv run pytest tests/test_mcp_management.py --cov=src.mcp --cov-report=term-missing

# HTML coverage report
uv run pytest tests/test_mcp_management.py --cov=src.mcp --cov-report=html
# Open htmlcov/index.html in browser
```

## Run Only Integration Tests
```bash
uv run pytest tests/test_mcp_management.py -m integration -v
```

## Quick Test Count
```bash
uv run pytest tests/test_mcp_management.py --collect-only
```

## Expected Output
```
tests/test_mcp_management.py::TestMCPClientManagerCRUD::test_load_config PASSED
tests/test_mcp_management.py::TestMCPClientManagerCRUD::test_list_servers PASSED
tests/test_mcp_management.py::TestMCPClientManagerCRUD::test_add_server PASSED
... (40+ tests)
====================== 40 passed in X.XXs ======================
```

## Troubleshooting

### ImportError
If you get import errors:
```bash
# Ensure dependencies installed
uv sync

# Add src to path
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

### Async Warnings
If you see asyncio warnings:
```bash
# Install pytest-asyncio
uv pip install pytest-asyncio
```

## Test Markers
Tests are marked with `@pytest.mark.integration` for filtering.
