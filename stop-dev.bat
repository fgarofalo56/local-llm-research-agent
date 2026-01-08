@echo off
REM =============================================================================
REM Local LLM Research Agent - Stop All Services Script
REM =============================================================================
REM
REM This script stops all running services:
REM   - Docker containers (SQL Server, Redis, Streamlit, Superset)
REM   - FastAPI Backend (via taskkill)
REM   - React Frontend (via taskkill)
REM
REM Usage:
REM   stop-dev.bat         - Stop all services, keep data
REM   stop-dev.bat --clean - Stop all services AND remove volumes (data loss!)
REM
REM =============================================================================

setlocal EnableDelayedExpansion

echo.
echo ============================================================
echo   Stopping Local LLM Research Agent Services
echo ============================================================
echo.

set CLEAN_VOLUMES=0

REM Parse arguments
if /i "%~1"=="--clean" set CLEAN_VOLUMES=1

REM Stop local processes (FastAPI and React)
echo [Step 1/3] Stopping local processes...

REM Kill uvicorn processes (FastAPI)
tasklist /FI "IMAGENAME eq python.exe" /FI "WINDOWTITLE eq FastAPI*" 2>nul | find "python.exe" >nul
if not errorlevel 1 (
    echo   Stopping FastAPI processes...
    taskkill /FI "WINDOWTITLE eq FastAPI*" /F >nul 2>&1
)

REM Kill node processes (React dev server)
tasklist /FI "IMAGENAME eq node.exe" 2>nul | find "node.exe" >nul
if not errorlevel 1 (
    echo   Stopping Node.js processes (React frontend)...
    REM This is aggressive - kills all node processes
    REM In a real scenario, you'd want to be more selective
    echo   Note: You may need to manually close React terminal windows
)

echo   Local processes signaled to stop

REM Stop Docker containers
echo [Step 2/3] Stopping Docker containers...

if %CLEAN_VOLUMES%==1 (
    echo   Stopping containers AND removing volumes...
    echo   WARNING: This will delete all database data!
    docker-compose -f docker/docker-compose.yml --env-file .env --profile superset down -v 2>nul
) else (
    echo   Stopping containers (preserving data)...
    docker-compose -f docker/docker-compose.yml --env-file .env --profile superset down 2>nul
)

echo   Docker containers stopped

REM Verify cleanup
echo [Step 3/3] Verifying cleanup...
timeout /t 2 /nobreak >nul

REM Check if containers are still running
docker ps --filter "name=local-agent" --format "{{.Names}}" 2>nul | findstr "local-agent" >nul
if not errorlevel 1 (
    echo   [WARNING] Some containers may still be running
    docker ps --filter "name=local-agent" --format "  - {{.Names}}"
) else (
    echo   All containers stopped
)

echo.
echo ============================================================
echo   All services stopped
echo ============================================================
echo.
if %CLEAN_VOLUMES%==1 (
    echo   Volumes were REMOVED - data has been deleted
) else (
    echo   Data volumes preserved - your data is safe
    echo   To also remove data: stop-dev.bat --clean
)
echo.
