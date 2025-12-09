# 🤝 Contributing to Local LLM Research Agent

> **Guidelines for contributing to the project**

---

## 📑 Table of Contents

- [Code of Conduct](#-code-of-conduct)
- [How to Contribute](#-how-to-contribute)
- [Development Setup](#-development-setup)
- [Code Style Guidelines](#-code-style-guidelines)
- [Testing](#-testing)
- [Reporting Issues](#-reporting-issues)

---

## 🎯 Code of Conduct

By participating in this project, you agree to maintain a respectful and inclusive environment for everyone.

---

## 🚀 How to Contribute

### For External Contributors

> ⚠️ **Important:** All external contributions must be submitted via Pull Request. Direct pushes to `main` are not allowed.

### Step-by-Step Process

| Step | Action | Command |
|------|--------|---------|
| 1 | Fork the repository | GitHub UI |
| 2 | Clone your fork | `git clone https://github.com/YOUR_USERNAME/local-llm-research-agent.git` |
| 3 | Create feature branch | `git checkout -b feature/your-feature-name` |
| 4 | Make changes | Follow guidelines below |
| 5 | Test changes | `uv run pytest tests/ -v` |
| 6 | Commit changes | `git commit -m "feat: description"` |
| 7 | Push branch | `git push origin feature/your-feature-name` |
| 8 | Create PR | GitHub UI |

### Branch Naming

| Type | Pattern | Example |
|------|---------|---------|
| Feature | `feature/description` | `feature/add-streaming` |
| Bug fix | `fix/description` | `fix/connection-timeout` |
| Docs | `docs/description` | `docs/update-readme` |

### Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

| Prefix | Use For | Example |
|--------|---------|---------|
| `feat:` | New features | `feat: add streaming responses` |
| `fix:` | Bug fixes | `fix: resolve connection timeout` |
| `docs:` | Documentation | `docs: update installation guide` |
| `test:` | Test changes | `test: add agent unit tests` |
| `refactor:` | Code refactoring | `refactor: simplify MCP client` |
| `chore:` | Maintenance | `chore: update dependencies` |

### Pull Request Checklist

Before submitting your PR:

- [ ] Clear, descriptive title
- [ ] References related issues (e.g., "Fixes #123")
- [ ] Description of changes and rationale
- [ ] All CI checks pass (tests, linting)
- [ ] Appropriate test coverage
- [ ] Documentation updated if needed
- [ ] No unrelated changes included

### Review Process

| Timeline | Action |
|----------|--------|
| 3-5 days | Initial review by maintainer |
| As needed | Address requested changes |
| After approval | Maintainer merges PR |

---

## 💻 Development Setup

### Prerequisites

| Requirement | Version | Purpose |
|-------------|---------|---------|
| Python | 3.11+ | Runtime |
| uv | Latest | Package manager |
| Docker Desktop | Latest | SQL Server |
| Node.js | 18+ | MSSQL MCP Server |
| Ollama | Latest | Local LLM |

### Quick Setup

```bash
# Clone repository
git clone https://github.com/fgarofalo56/local-llm-research-agent.git
cd local-llm-research-agent

# Install dependencies
uv sync

# Copy environment template
cp .env.example .env

# Start SQL Server (Docker)
cd docker
./setup-database.bat  # Windows
./setup-database.sh   # Linux/Mac

# Pull Ollama model
ollama pull qwen2.5:7b-instruct

# Run tests
uv run pytest tests/ -v
```

---

## 🎨 Code Style Guidelines

### Python Standards

| Standard | Requirement |
|----------|-------------|
| Python version | 3.11+ features |
| Type hints | All function signatures |
| Data models | Pydantic v2 |
| I/O operations | async/await |
| Line length | 100 characters max |

### Example Code

```python
# ✅ Good - typed, async, Pydantic
from pydantic import BaseModel

class QueryResult(BaseModel):
    query: str
    rows: list[dict]
    execution_time: float

async def execute_query(sql: str) -> QueryResult:
    """Execute a SQL query and return results."""
    # Implementation
    pass
```

### Formatting Tools

We use [Ruff](https://github.com/astral-sh/ruff) for linting and formatting:

```bash
# Check for issues
uv run ruff check .

# Auto-fix issues
uv run ruff check --fix .

# Format code
uv run ruff format .
```

### Documentation Standards

| File Type | Update When |
|-----------|-------------|
| `README.md` | User-facing changes |
| `CLAUDE.md` | Architectural changes |
| `docs/` | Feature additions |
| Docstrings | All public functions |

---

## 🧪 Testing

### Running Tests

```bash
# All tests
uv run pytest tests/ -v

# Specific test file
uv run pytest tests/test_agent.py -v

# With coverage report
uv run pytest tests/ --cov=src --cov-report=html
```

### Writing Tests

| Guideline | Description |
|-----------|-------------|
| Location | `tests/` directory |
| Fixtures | Use pytest fixtures for setup |
| Mocking | Mock external dependencies |
| Coverage | Test success and error cases |

### Example Test

```python
import pytest
from unittest.mock import AsyncMock

@pytest.mark.asyncio
async def test_agent_processes_query():
    """Test that agent correctly processes a query."""
    agent = create_test_agent()
    result = await agent.run("List all tables")

    assert result.output is not None
    assert "tables" in result.output.lower()
```

---

## 📝 Reporting Issues

### Bug Reports

Include the following information:

| Information | Example |
|-------------|---------|
| Python version | `python --version` output |
| OS and version | Windows 11, macOS 14, Ubuntu 22.04 |
| Steps to reproduce | Numbered steps |
| Expected behavior | What should happen |
| Actual behavior | What actually happens |
| Error messages | Full stack trace |

### Feature Requests

Include:

| Information | Description |
|-------------|-------------|
| Feature description | Clear explanation |
| Use case | Why it's needed |
| Proposed implementation | Optional but helpful |

### Getting Help

| Resource | Use For |
|----------|---------|
| Existing issues | Check if already reported |
| Documentation | `docs/` directory |
| New issue | Use "question" label |

---

## 📄 License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

*Last Updated: December 2024*
