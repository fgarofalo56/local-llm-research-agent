# Contributing to Local LLM Research Agent

Thank you for your interest in contributing! This document outlines our contribution process and guidelines.

## Code of Conduct

By participating in this project, you agree to maintain a respectful and inclusive environment for everyone.

## How to Contribute

### For External Contributors

**All external contributions must be submitted via Pull Request.** Direct pushes to the `main` branch are not allowed.

1. **Fork the Repository**
   ```bash
   # Fork via GitHub UI, then clone your fork
   git clone https://github.com/YOUR_USERNAME/local-llm-research-agent.git
   cd local-llm-research-agent
   ```

2. **Create a Feature Branch**
   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b fix/your-bug-fix
   ```

3. **Make Your Changes**
   - Follow the code style guidelines below
   - Add tests for new functionality
   - Update documentation as needed

4. **Test Your Changes**
   ```bash
   # Install dependencies
   uv sync

   # Run tests
   uv run pytest tests/ -v

   # Run linter
   uv run ruff check .

   # Format code
   uv run ruff format .
   ```

5. **Commit Your Changes**
   ```bash
   git add .
   git commit -m "feat: add your feature description"
   ```

   Follow [Conventional Commits](https://www.conventionalcommits.org/):
   - `feat:` - New features
   - `fix:` - Bug fixes
   - `docs:` - Documentation changes
   - `test:` - Test additions/changes
   - `refactor:` - Code refactoring
   - `chore:` - Maintenance tasks

6. **Push and Create Pull Request**
   ```bash
   git push origin feature/your-feature-name
   ```
   Then create a Pull Request via GitHub UI.

### Pull Request Guidelines

Your PR should:

- [ ] Have a clear, descriptive title
- [ ] Reference any related issues (e.g., "Fixes #123")
- [ ] Include a description of what changed and why
- [ ] Pass all CI checks (tests, linting)
- [ ] Have appropriate test coverage
- [ ] Update documentation if needed
- [ ] Not include unrelated changes

### PR Review Process

1. A maintainer will review your PR within 3-5 business days
2. Address any requested changes
3. Once approved, a maintainer will merge your PR

## Development Setup

### Prerequisites

- Python 3.11+
- [uv](https://github.com/astral-sh/uv) (recommended) or pip
- Docker Desktop (for SQL Server)
- Node.js 18+ (for MSSQL MCP Server)
- Ollama installed locally

### Quick Setup

```bash
# Clone repo
git clone https://github.com/ORIGINAL_OWNER/local-llm-research-agent.git
cd local-llm-research-agent

# Install dependencies
uv sync

# Copy environment template
cp .env.example .env

# Start SQL Server (Docker)
cd docker
./setup-database.bat  # Windows
# or
docker compose up -d && docker compose --profile init up mssql-tools  # Linux/Mac

# Pull Ollama model
ollama pull qwen2.5:7b-instruct

# Run tests
uv run pytest tests/ -v
```

## Code Style Guidelines

### Python

- Use Python 3.11+ features
- Type hints for all function signatures
- Pydantic models for data structures
- Async/await for I/O operations
- Maximum line length: 100 characters

### Formatting

We use [Ruff](https://github.com/astral-sh/ruff) for linting and formatting:

```bash
# Check for issues
uv run ruff check .

# Auto-fix issues
uv run ruff check --fix .

# Format code
uv run ruff format .
```

### Documentation

- Docstrings for all public functions and classes
- Update README.md for user-facing changes
- Update CLAUDE.md for architectural changes
- Keep ai_docs/ updated for MCP tool changes

## Testing

### Running Tests

```bash
# All tests
uv run pytest tests/ -v

# Specific test file
uv run pytest tests/test_agent.py -v

# With coverage
uv run pytest tests/ --cov=src --cov-report=html
```

### Writing Tests

- Place tests in `tests/` directory
- Use pytest fixtures for common setup
- Mock external dependencies (Ollama, MCP servers)
- Test both success and error cases

## Reporting Issues

### Bug Reports

Include:
- Python version
- OS and version
- Steps to reproduce
- Expected vs actual behavior
- Error messages/logs

### Feature Requests

Include:
- Clear description of the feature
- Use case / motivation
- Proposed implementation (optional)

## Questions?

- Check existing issues and discussions
- Review the documentation in `ai_docs/`
- Open a new issue with the "question" label

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
