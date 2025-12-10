# Code Style and Conventions

## Python Version
- Python 3.11+ (target 3.11)

## Formatting
- **Tool**: Ruff
- **Line length**: 100 characters
- **Quote style**: Double quotes
- **Indent style**: 4 spaces

## Linting Rules
- pycodestyle (E, W)
- Pyflakes (F)
- isort (I)
- flake8-bugbear (B)
- flake8-comprehensions (C4)
- pyupgrade (UP)
- flake8-simplify (SIM)

## Type Hints
- All function signatures must have type hints
- Use Pydantic models for data structures
- MyPy strict mode enabled

## Async Patterns
- Use `async/await` for all I/O operations
- MCP client operations are async
- Streamlit requires `asyncio.run()` helper

## Naming Conventions
- snake_case for functions, variables, modules
- PascalCase for classes
- UPPER_SNAKE_CASE for constants

## Documentation
- Docstrings for public functions and classes
- Google-style docstrings preferred
- Keep docstrings concise

## File Organization
- Keep files under 500 lines
- Group related functionality
- Separate concerns (models, routes, services)

## Import Order (isort)
1. Standard library
2. Third-party packages
3. Local imports (src.*)

## Pydantic Models
- Use `Field()` for descriptions and defaults
- Use `model_validate()` for ORM conversion
- Prefer `from_attributes = True` for ORM models
