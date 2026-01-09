# Debug Scripts

Quick debugging and verification scripts for development.

## Scripts

- `debug_prompt.py` - Test prompt templates and agent responses
- `quick_test.py` - Quick smoke tests for core functionality
- `quick_endpoint_test.py` - Fast API endpoint testing
- `verify_prompt.py` - Verify system prompt generation

## Usage

```bash
# Run from project root
uv run python scripts/debug/quick_test.py

# Or with full path
cd scripts/debug
uv run python quick_test.py
```

## When to Use

- Quick sanity checks during development
- Debugging specific issues without full test suite
- Verifying changes work before committing
- Manual testing of new features

## Note

These are NOT formal tests. For proper testing, use:
- `tests/` - Unit and integration tests (pytest)
- `examples/` - Usage examples and demos
