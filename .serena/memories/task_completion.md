# Task Completion Checklist

When completing a task in this project, follow these steps:

## 1. Code Quality Checks
```bash
# Format code
uv run ruff format .

# Lint check (fix if needed)
uv run ruff check . --fix
```

## 2. Testing
```bash
# Run all tests
uv run pytest tests/ -v

# Ensure no regressions
```

## 3. Existing Interfaces Verification
```bash
# Verify CLI still works
uv run python -m src.cli.chat --help

# Verify Streamlit still works
uv run streamlit run src/ui/streamlit_app.py
```

## 4. Task Tracking (Archon)
- Update task status: `manage_task("update", task_id="...", status="review")`
- After verification: `manage_task("update", task_id="...", status="done")`

## 5. Git (if requested)
```bash
git add .
git commit -m "descriptive message"
```

## Critical Constraints
- DO NOT modify existing files in: `src/agent/`, `src/cli/`, `src/ui/`
- CREATE new files in appropriate directories
- EXTEND existing files, don't replace working code
- TEST existing interfaces after each major change
