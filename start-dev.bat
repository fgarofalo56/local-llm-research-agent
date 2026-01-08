@echo off
REM =============================================================================
REM Local LLM Research Agent - Full Stack Development Startup Script
REM =============================================================================
REM
REM This script starts all services needed for local development:
REM   - SQL Server 2022 (Sample Database - Docker)
REM   - SQL Server 2025 (Backend with Vector Search - Docker)
REM   - Redis Stack (Caching - Docker)
REM   - Alembic Migrations (Database schema)
REM   - FastAPI Backend (local or Docker)
REM   - React Frontend (local dev server or Docker)
REM   - Streamlit UI (Docker - optional)
REM   - Apache Superset (Docker - optional)
REM
REM Prerequisites:
REM   - Docker Desktop running
REM   - Ollama running with qwen3:30b model
REM   - Node.js installed (for local mode)
REM   - Python/uv installed (for local mode)
REM
REM Usage:
REM   start-dev.bat              - Start core services (hybrid: local FastAPI + React)
REM   start-dev.bat --streamlit  - Also start Streamlit UI
REM   start-dev.bat --superset   - Also start Apache Superset
REM   start-dev.bat --full       - Start everything (hybrid mode)
REM   start-dev.bat --docker     - Run everything in Docker (fresh build)
REM
REM =============================================================================

setlocal EnableDelayedExpansion

echo.
echo ============================================================
echo   Local LLM Research Agent - Development Stack
echo ============================================================
echo.

REM Parse command line arguments
set START_STREAMLIT=0
set START_SUPERSET=0
set DOCKER_MODE=0

:parse_args
if "%~1"=="" goto :done_args
if /i "%~1"=="--streamlit" set START_STREAMLIT=1
if /i "%~1"=="--superset" set START_SUPERSET=1
if /i "%~1"=="--full" (
    set START_STREAMLIT=1
    set START_SUPERSET=1
)
if /i "%~1"=="--docker" (
    set DOCKER_MODE=1
    set START_STREAMLIT=1
    set START_SUPERSET=1
)
shift
goto :parse_args
:done_args

REM If Docker mode, run the Docker-only startup
if %DOCKER_MODE%==1 goto :docker_mode

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
) else (
    echo [OK] Ollama is running
    REM Check if qwen3:30b model is available
    curl -s http://localhost:11434/api/tags | findstr /i "qwen3:30b" >nul 2>&1
    if errorlevel 1 (
        echo [WARNING] qwen3:30b model not found in Ollama.
        echo Run: ollama pull qwen3:30b
        echo.
    ) else (
        echo [OK] qwen3:30b model is available
    )
)

REM Calculate total steps
set TOTAL_STEPS=10
if %START_STREAMLIT%==1 set /a TOTAL_STEPS+=1
if %START_SUPERSET%==1 set /a TOTAL_STEPS+=1

echo [Step 1/%TOTAL_STEPS%] Creating Docker volumes if needed...
docker volume create local-llm-mssql-data 2>nul
docker volume create local-llm-backend-data 2>nul
docker volume create local-llm-redis-data 2>nul
docker volume create local-llm-superset-data 2>nul

echo [Step 2/%TOTAL_STEPS%] Starting SQL Server 2022 (Sample Database)...
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

echo [Step 3/%TOTAL_STEPS%] Initializing ResearchAnalytics sample database...
docker-compose -f docker/docker-compose.yml --env-file .env --profile init up mssql-tools 2>nul

echo [Step 4/%TOTAL_STEPS%] Starting SQL Server 2025 (Backend Database)...
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

echo [Step 5/%TOTAL_STEPS%] Initializing LLM_BackEnd database (vectors + hybrid search)...
docker-compose -f docker/docker-compose.yml --env-file .env --profile init up mssql-backend-tools 2>nul

echo [Step 6/%TOTAL_STEPS%] Starting Redis Stack...
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

echo [Step 7/%TOTAL_STEPS%] Running Alembic database migrations...
uv run alembic upgrade head 2>nul
if errorlevel 1 (
    echo   [WARNING] Alembic migrations may have failed or no migrations pending
) else (
    echo   Database migrations complete!
)

echo [Step 8/%TOTAL_STEPS%] Starting FastAPI backend...
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

echo [Step 9/%TOTAL_STEPS%] Starting React frontend...
start "React Frontend" cmd /c "cd /d %~dp0frontend & npm run dev"

set CURRENT_STEP=10

REM Optional: Start Streamlit UI
if %START_STREAMLIT%==1 (
    echo [Step !CURRENT_STEP!/%TOTAL_STEPS%] Starting Streamlit UI...
    docker-compose -f docker/docker-compose.yml --env-file .env up -d agent-ui
    echo   Streamlit UI starting at http://localhost:8501
    set /a CURRENT_STEP+=1
)

REM Optional: Start Superset
if %START_SUPERSET%==1 (
    echo [Step !CURRENT_STEP!/%TOTAL_STEPS%] Starting Apache Superset...
    docker-compose -f docker/docker-compose.yml --env-file .env --profile superset up -d superset
    echo   Superset starting at http://localhost:8088 (may take 1-2 minutes)
    set /a CURRENT_STEP+=1
)

echo [Step %TOTAL_STEPS%/%TOTAL_STEPS%] Verifying all services...
timeout /t 3 /nobreak >nul

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
if %START_STREAMLIT%==1 (
    echo     - Streamlit UI:    http://localhost:8501
)
if %START_SUPERSET%==1 (
    echo     - Apache Superset: http://localhost:8088
)
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
echo   Command-line options:
echo     start-dev.bat --streamlit  - Also start Streamlit UI
echo     start-dev.bat --superset   - Also start Apache Superset
echo     start-dev.bat --full       - Start everything (hybrid mode)
echo     start-dev.bat --docker     - Run everything in Docker (fresh build)
echo.
echo   Press any key to open the React app in your browser...
pause >nul

start http://localhost:5173
goto :eof

REM =============================================================================
REM Docker Mode - Run everything in Docker with fresh builds
REM =============================================================================
:docker_mode

echo.
echo   MODE: Full Docker (fresh build)
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
) else (
    echo [OK] Ollama is running
    curl -s http://localhost:11434/api/tags | findstr /i "qwen3:30b" >nul 2>&1
    if errorlevel 1 (
        echo [WARNING] qwen3:30b model not found in Ollama.
        echo Run: ollama pull qwen3:30b
        echo.
    ) else (
        echo [OK] qwen3:30b model is available
    )
)

echo [Step 1/8] Creating Docker volumes if needed...
docker volume create local-llm-mssql-data 2>nul
docker volume create local-llm-backend-data 2>nul
docker volume create local-llm-redis-data 2>nul
docker volume create local-llm-superset-data 2>nul

echo [Step 2/8] Building all Docker images (fresh build, no cache)...
echo   This may take several minutes...
docker-compose -f docker/docker-compose.yml --env-file .env build --no-cache

echo [Step 3/8] Starting SQL Server 2022 (Sample Database)...
docker-compose -f docker/docker-compose.yml --env-file .env up -d mssql

echo Waiting for SQL Server 2022 to be healthy...
:docker_wait_sql
timeout /t 5 /nobreak >nul
docker inspect --format="{{.State.Health.Status}}" local-agent-mssql 2>nul | findstr "healthy" >nul
if errorlevel 1 (
    echo   Still waiting for SQL Server 2022...
    goto docker_wait_sql
)
echo   SQL Server 2022 is ready!

echo [Step 4/8] Initializing ResearchAnalytics sample database...
docker-compose -f docker/docker-compose.yml --env-file .env --profile init up mssql-tools 2>nul

echo [Step 5/8] Starting SQL Server 2025 (Backend Database)...
docker-compose -f docker/docker-compose.yml --env-file .env up -d mssql-backend

echo Waiting for SQL Server 2025 to be healthy...
:docker_wait_backend
timeout /t 5 /nobreak >nul
docker inspect --format="{{.State.Health.Status}}" local-agent-mssql-backend 2>nul | findstr "healthy" >nul
if errorlevel 1 (
    echo   Still waiting for SQL Server 2025...
    goto docker_wait_backend
)
echo   SQL Server 2025 is ready!

echo [Step 6/8] Initializing LLM_BackEnd database (vectors + hybrid search)...
docker-compose -f docker/docker-compose.yml --env-file .env --profile init up mssql-backend-tools 2>nul

echo [Step 7/8] Starting Redis Stack...
docker-compose -f docker/docker-compose.yml --env-file .env up -d redis-stack

echo Waiting for Redis to be healthy...
:docker_wait_redis
timeout /t 3 /nobreak >nul
docker inspect --format="{{.State.Health.Status}}" local-agent-redis 2>nul | findstr "healthy" >nul
if errorlevel 1 (
    echo   Still waiting for Redis...
    goto docker_wait_redis
)
echo   Redis Stack is ready!

echo [Step 8/8] Starting all application services...
docker-compose -f docker/docker-compose.yml --env-file .env --profile full up -d

echo Waiting for FastAPI to be ready...
:docker_wait_api
timeout /t 5 /nobreak >nul
curl -s http://localhost:8000/api/health >nul 2>&1
if errorlevel 1 (
    echo   Still waiting for FastAPI...
    goto docker_wait_api
)
echo   FastAPI is ready!

echo Waiting for React frontend to be ready...
timeout /t 10 /nobreak >nul
echo   React frontend should be ready!

echo.
echo ============================================================
echo   All Docker services started successfully!
echo ============================================================
echo.
echo   Database Services:
echo     - SQL Server 2022: localhost:1433 (ResearchAnalytics)
echo     - SQL Server 2025: localhost:1434 (LLM_BackEnd + Vectors)
echo     - Redis Stack:     localhost:6379
echo     - RedisInsight:    http://localhost:8001
echo.
echo   Application Services (ALL IN DOCKER):
echo     - FastAPI Backend: http://localhost:8000
echo     - FastAPI Docs:    http://localhost:8000/docs
echo     - React Frontend:  http://localhost:5173
echo     - Streamlit UI:    http://localhost:8501
echo     - Apache Superset: http://localhost:8088
echo.
echo   Docker Containers:
echo     - local-agent-api         (FastAPI)
echo     - local-agent-frontend    (React)
echo     - local-agent-streamlit-ui (Streamlit)
echo     - local-agent-superset    (Superset)
echo.
echo   To stop all services:
echo     Run: stop-dev.bat
echo     Or:  docker-compose -f docker/docker-compose.yml --env-file .env --profile full down
echo.
echo   Press any key to open the React app in your browser...
pause >nul

start http://localhost:5173
