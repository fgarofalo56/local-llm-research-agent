@echo off
REM Test the git commit helper
cd /d "%~dp0"

echo Running smart commit helper...
echo.

REM First check git status
git status

echo.
echo ========================================
echo.

REM Run the commit helper
call git-commit.bat
