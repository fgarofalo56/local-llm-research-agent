@echo off
REM =============================================================================
REM Local LLM Research Agent - Full Stack Development Startup Script
REM =============================================================================
REM
REM This script starts all services needed for local development:
REM   - SQL Server (Docker)
REM   - Redis Stack (Docker)
REM   - FastAPI Backend (local)
REM   - React Frontend (local dev server)
REM
REM Prerequisites:
REM   - Docker Desktop running
REM   - Ollama running with qwen3:30b model
REM   - Node.js installed
REM   - Python/uv installed
REM
REM =============================================================================

setlocal EnableDelayedExpansion

echo.
echo ============================================================
echo   Local LLM Research Agent - Development Stack
echo ============================================================
echo.

REM Check if .env file exists
if not exist ".env" (
    echo [ERROR] .env file not found!
    echo Please copy .env.example to .env and configure it.
    exit /b 1
)

REM Check if Docker is running
docker info >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker is not running!
    echo Please start Docker Desktop first.
    exit /b 1
)

REM Check if Ollama is running
curl -s http://localhost:11434/api/tags >nul 2>&1
if errorlevel 1 (
    echo [WARNING] Ollama does not appear to be running.
    echo The agent will not work without Ollama.
    echo Start Ollama and ensure qwen3:30b model is available.
    echo.
)

echo [Step 1/5] Creating Docker volumes if needed...
docker volume create local-llm-mssql-data 2>nul
docker volume create local-llm-redis-data 2>nul

echo [Step 2/5] Starting Docker services (SQL Server + Redis)...
docker-compose -f docker/docker-compose.yml --env-file .env up -d mssql redis-stack

echo Waiting for SQL Server to be healthy...
:wait_sql
timeout /t 5 /nobreak >nul
docker-compose -f docker/docker-compose.yml ps mssql | findstr "healthy" >nul
if errorlevel 1 (
    echo   Still waiting for SQL Server...
    goto wait_sql
)
echo   SQL Server is ready!

echo [Step 3/5] Checking if database is initialized...
REM Run init scripts if database doesn't exist
docker-compose -f docker/docker-compose.yml --env-file .env --profile init up mssql-tools 2>nul

echo [Step 4/5] Starting FastAPI backend...
start "FastAPI Backend" cmd /c "cd /d %~dp0 & uv run uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000"

echo Waiting for API to be ready...
timeout /t 5 /nobreak >nul
:wait_api
curl -s http://localhost:8000/api/health >nul 2>&1
if errorlevel 1 (
    timeout /t 2 /nobreak >nul
    goto wait_api
)
echo   FastAPI is ready!

echo [Step 5/5] Starting React frontend...
start "React Frontend" cmd /c "cd /d %~dp0frontend & npm run dev"

echo.
echo ============================================================
echo   All services started successfully!
echo ============================================================
echo.
echo   Services:
echo     - SQL Server:      localhost:1433
echo     - Redis:           localhost:6379
echo     - RedisInsight:    http://localhost:8001
echo     - FastAPI Backend: http://localhost:8000
echo     - FastAPI Docs:    http://localhost:8000/docs
echo     - React Frontend:  http://localhost:5173
echo.
echo   To stop all services:
echo     - Close the terminal windows for FastAPI and React
echo     - Run: docker-compose -f docker/docker-compose.yml down
echo.
echo   Press any key to open the React app in your browser...
pause >nul

start http://localhost:5173
