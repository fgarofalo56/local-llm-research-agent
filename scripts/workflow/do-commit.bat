@echo off
REM Git commit automation script
cd /d "%~dp0"

echo ========================================
echo Creating Git Commit
echo ========================================
echo.

REM Stage the essential files
echo Staging files...
git add src\ui\streamlit_app.py
git add docs\STREAMLIT_TESTING.md
git add docs\STREAMLIT_FIX_SUMMARY.md
git add README.md
git add CLAUDE.md
git add start-all.bat
git add test-streamlit.bat
git add GIT_COMMIT_GUIDE.md
git add COMMIT_NOW.md

echo.
echo Files staged successfully!
echo.

REM Show what will be committed
echo Files to be committed:
git diff --cached --name-only

echo.
echo ========================================
echo Creating commit...
echo ========================================
echo.

REM Commit with message
git commit -m "fix(streamlit): Add MCP session management to chat interface" -m "Streamlit chat was failing due to missing MCP server session management." -m "Fixed by wrapping agent calls in 'async with agent:' context manager," -m "matching the CLI implementation pattern." -m "" -m "Changes:" -m "- Fixed src/ui/streamlit_app.py (added async context managers)" -m "- Added docs/STREAMLIT_TESTING.md (comprehensive testing guide)" -m "- Added docs/STREAMLIT_FIX_SUMMARY.md (fix documentation)" -m "- Updated README.md (added testing section)" -m "- Updated CLAUDE.md (documented MCP session patterns)" -m "- Added start-all.bat (service launcher)" -m "- Added test-streamlit.bat (Streamlit launcher)" -m "" -m "Task: 494cdf28-4e58-49ba-ad7a-4e9ed2cde284"

if %errorlevel% equ 0 (
    echo.
    echo ========================================
    echo Commit created successfully!
    echo ========================================
    echo.
    git log -1 --oneline
    echo.
    echo Next step: git push
) else (
    echo.
    echo ========================================
    echo Commit failed!
    echo ========================================
    exit /b 1
)

pause
