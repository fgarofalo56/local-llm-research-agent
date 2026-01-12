@echo off
REM Git status and commit helper
cd /d "%~dp0"

echo ========================================
echo Git Status and Staging
echo ========================================
echo.

git status

echo.
echo ========================================
echo Files to commit:
echo ========================================
git diff --name-only --cached
echo.

pause
