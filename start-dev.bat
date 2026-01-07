@echo off
REM =============================================================================
REM Local LLM Research Agent - Full Stack Development Startup Script
REM =============================================================================
REM
REM This script starts all services needed for local development:
REM   - SQL Server 2022 (Sample Database - Docker)
REM   - SQL Server 2025 (Backend with Vector Search - Docker)
REM   - Redis Stack (Caching - Docker)
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

echo [Step 1/8] Creating Docker volumes if needed...
docker volume create local-llm-mssql-data 2>nul
docker volume create local-llm-backend-data 2>nul
docker volume create local-llm-redis-data 2>nul

echo [Step 2/8] Starting SQL Server 2022 (Sample Database)...
docker-compose -f docker/docker-compose.yml --env-file .env up -d mssql

echo Waiting for SQL Server 2022 to be healthy...
:wait_sql
timeout /t 5 /nobreak >nul
docker inspect --format="{{.State.Health.Status}}" local-agent-mssql 2>nul | findstr "healthy" >nul
if errorlevel 1 (
    echo   Still waiting for SQL Server 2022...
    goto wait_sql
)
echo   SQL Server 2022 is ready!

echo [Step 3/8] Initializing ResearchAnalytics sample database...
docker-compose -f docker/docker-compose.yml --env-file .env --profile init up mssql-tools 2>nul

echo [Step 4/8] Starting SQL Server 2025 (Backend Database)...
docker-compose -f docker/docker-compose.yml --env-file .env up -d mssql-backend

echo Waiting for SQL Server 2025 to be healthy...
:wait_backend
timeout /t 5 /nobreak >nul
docker inspect --format="{{.State.Health.Status}}" local-agent-mssql-backend 2>nul | findstr "healthy" >nul
if errorlevel 1 (
    echo   Still waiting for SQL Server 2025...
    goto wait_backend
)
echo   SQL Server 2025 is ready!

echo [Step 5/8] Initializing LLM_BackEnd database (vectors + hybrid search)...
docker-compose -f docker/docker-compose.yml --env-file .env --profile init up mssql-backend-tools 2>nul

echo [Step 6/8] Starting Redis Stack...
docker-compose -f docker/docker-compose.yml --env-file .env up -d redis-stack

echo Waiting for Redis to be healthy...
:wait_redis
timeout /t 3 /nobreak >nul
docker inspect --format="{{.State.Health.Status}}" local-agent-redis 2>nul | findstr "healthy" >nul
if errorlevel 1 (
    echo   Still waiting for Redis...
    goto wait_redis
)
echo   Redis Stack is ready!

echo [Step 7/8] Starting FastAPI backend...
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

echo [Step 8/8] Starting React frontend...
start "React Frontend" cmd /c "cd /d %~dp0frontend & npm run dev"

echo.
echo ============================================================
echo   All services started successfully!
echo ============================================================
echo.
echo   Database Services:
echo     - SQL Server 2022: localhost:1433 (ResearchAnalytics)
echo     - SQL Server 2025: localhost:1434 (LLM_BackEnd + Vectors)
echo     - Redis Stack:     localhost:6379
echo     - RedisInsight:    http://localhost:8001
echo.
echo   Application Services:
echo     - FastAPI Backend: http://localhost:8000
echo     - FastAPI Docs:    http://localhost:8000/docs
echo     - React Frontend:  http://localhost:5173
echo.
echo   RAG Features:
echo     - Vector Store: SQL Server 2025 (native VECTOR type)
echo     - Embeddings:   nomic-embed-text (768 dimensions)
echo     - Hybrid Search: Enabled (semantic + full-text with RRF)
echo     - Documents:    PDF, DOCX, PPTX, XLSX, HTML, Markdown, Images
echo.
echo   To stop all services:
echo     - Close the terminal windows for FastAPI and React
echo     - Run: docker-compose -f docker/docker-compose.yml --env-file .env down
echo.
echo   Press any key to open the React app in your browser...
pause >nul

start http://localhost:5173
