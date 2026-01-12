@echo off
REM Smart commit helper wrapper
cd /d "%~dp0.."

echo ========================================
echo Smart Git Commit Helper
echo ========================================
echo.

REM Check if any changes are staged
git diff --cached --quiet
if %errorlevel% neq 0 (
    REM Staged changes exist, run commit helper
    python scripts\git-commit.py
) else (
    REM No staged changes, show status and offer to stage
    echo No staged changes found.
    echo.
    git status --short
    echo.
    set /p STAGE="Stage all changes? [Y/n]: "
    if /i "%STAGE%"=="n" (
        echo Cancelled.
        exit /b 0
    )
    git add -A
    echo.
    echo Files staged. Running commit helper...
    echo.
    python scripts\git-commit.py
)
