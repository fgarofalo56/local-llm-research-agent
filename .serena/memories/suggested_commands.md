# Suggested Commands

## Development Setup
```bash
# Install dependencies
uv sync

# Activate virtual environment (if needed)
.venv\Scripts\activate
```

## Running the Application
```bash
# CLI Chat Interface
uv run python -m src.cli.chat

# Streamlit Web UI
uv run streamlit run src/ui/streamlit_app.py

# FastAPI (Phase 2.1+)
uv run uvicorn src.api.main:app --reload
```

## Testing
```bash
# Run all tests
uv run pytest tests/ -v

# Run specific test file
uv run pytest tests/test_agent.py -v

# With coverage
uv run pytest tests/ --cov=src --cov-report=html

# Unit tests only
uv run pytest tests/ -m unit

# Integration tests only
uv run pytest tests/ -m integration
```

## Code Quality
```bash
# Format code
uv run ruff format .

# Lint check
uv run ruff check .

# Lint fix
uv run ruff check . --fix

# Type checking
uv run mypy src/
```

## Docker
```bash
# Start SQL Server
cd docker && docker compose up -d mssql

# Initialize database (first time)
cd docker && docker compose --profile init up mssql-tools

# Stop SQL Server
cd docker && docker compose down

# Stop and remove data
cd docker && docker compose down -v
```

## Ollama
```bash
# Check Ollama is running
curl http://localhost:11434/api/tags

# List models
ollama list

# Pull a model
ollama pull qwen3:30b
```

## Git (Windows)
```bash
git status
git add .
git commit -m "message"
git push
git log --oneline -10
```
