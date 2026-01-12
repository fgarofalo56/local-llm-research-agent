# Git Commit Guide for Streamlit Fix

## Quick Commit (Copy & Paste)

### Step 1: Stage Changes
```bash
git add -A
```

### Step 2: Commit with Message
```bash
git commit -m "fix(streamlit): Add MCP session management to chat interface

Streamlit chat was failing due to missing MCP server session management.
Fixed by wrapping agent calls in 'async with agent:' context manager,
matching the CLI implementation pattern.

Modified:
- src/ui/streamlit_app.py

Documentation:
- docs/STREAMLIT_TESTING.md
- docs/STREAMLIT_FIX_SUMMARY.md
- README.md
- CLAUDE.md

Scripts:
- check-status.bat
- start-all.bat
- test-streamlit.bat
- git-commit.bat
- scripts/git-commit.py

Task: 494cdf28-4e58-49ba-ad7a-4e9ed2cde284"
```

### Step 3: Push (Optional)
```bash
git push origin main
```

---

## Alternative: Use Smart Commit Helper

### Windows
```bash
git-commit.bat
```

This will:
1. Check for staged changes (auto-stage if needed)
2. Generate smart commit message
3. Show preview and ask for confirmation
4. Commit with generated message

---

## Files Changed (Summary)

### Core Fix
- `src/ui/streamlit_app.py` - Added MCP session context managers

### Documentation
- `docs/STREAMLIT_TESTING.md` - Comprehensive testing guide
- `docs/STREAMLIT_FIX_SUMMARY.md` - Fix documentation
- `README.md` - Added testing section
- `CLAUDE.md` - Enhanced MCP patterns

### Testing Scripts
- `check-status.bat` - System status checker
- `start-all.bat` - Service startup script
- `test-streamlit.bat` - Streamlit launcher
- `git-status.bat` - Git status helper
- `git-add.bat` - Git staging helper
- `git-commit.bat` - Smart commit wrapper
- `scripts/git-commit.py` - Commit message generator

---

## Conventional Commits Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

### This Commit
- **Type:** `fix` (bug fix)
- **Scope:** `streamlit` (Streamlit UI)
- **Subject:** "Add MCP session management to chat interface"
- **Body:** Explanation of the fix
- **Footer:** Task ID reference

---

## Check Before Committing

```bash
# View staged changes
git diff --cached

# View file list
git diff --cached --name-only

# View stats
git diff --cached --stat
```

---

## Commit Message Best Practices

✅ **DO:**
- Use conventional commits format
- Keep subject under 50 characters
- Include task/issue references
- List modified files in body
- Explain WHY the change was made

❌ **DON'T:**
- Use vague subjects like "fix bug"
- Forget to stage new files
- Commit without testing
- Mix unrelated changes

---

## Current Status

Run this to see what will be committed:
```bash
git status
```

Expected output:
```
On branch main
Changes to be committed:
  (use "git restore --staged <file>..." to unstage)
        modified:   CLAUDE.md
        modified:   README.md
        new file:   check-status.bat
        new file:   docs/STREAMLIT_FIX_SUMMARY.md
        new file:   docs/STREAMLIT_TESTING.md
        new file:   git-add.bat
        new file:   git-commit.bat
        new file:   git-status.bat
        new file:   scripts/git-commit.py
        new file:   start-all.bat
        modified:   src/ui/streamlit_app.py
        new file:   test-streamlit.bat
```
