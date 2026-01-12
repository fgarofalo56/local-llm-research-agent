# Quick Commit Instructions

## Just Run These Commands:

```bash
# Stage all changes
git add src/ui/streamlit_app.py docs/STREAMLIT_TESTING.md docs/STREAMLIT_FIX_SUMMARY.md README.md CLAUDE.md start-all.bat test-streamlit.bat GIT_COMMIT_GUIDE.md

# Commit
git commit -m "fix(streamlit): Add MCP session management to chat interface

Streamlit chat was failing due to missing MCP server session management.
Fixed by wrapping agent calls in 'async with agent:' context manager,
matching the CLI implementation pattern.

Changes:
- Fixed src/ui/streamlit_app.py (added async context managers)
- Added docs/STREAMLIT_TESTING.md (comprehensive testing guide)
- Added docs/STREAMLIT_FIX_SUMMARY.md (fix documentation)
- Updated README.md (added testing section)
- Updated CLAUDE.md (documented MCP session patterns)
- Added start-all.bat (service launcher)
- Added test-streamlit.bat (Streamlit launcher)

Task: 494cdf28-4e58-49ba-ad7a-4e9ed2cde284"

# Push
git push
```

Done! That's all you need.
