@echo off
REM Stage all changes for commit
cd /d "%~dp0"

echo ========================================
echo Staging all changes...
echo ========================================
echo.

git add -A

echo.
echo Staged files:
git diff --name-only --cached

echo.
echo ========================================
echo Ready to commit!
echo ========================================
