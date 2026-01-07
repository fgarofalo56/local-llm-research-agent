@echo off
REM =============================================================================
REM setup-database.bat
REM Complete database setup for Local LLM Research Agent
REM Sets up both SQL Server 2022 (Sample) and SQL Server 2025 (Backend)
REM =============================================================================

setlocal enabledelayedexpansion

echo.
echo ============================================================
echo   Local LLM Research Agent - Complete Database Setup
echo ============================================================
echo.

REM Check if Docker is running
docker info >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker is not running. Please start Docker Desktop and try again.
    exit /b 1
)

REM Navigate to docker directory
cd /d "%~dp0"

REM Check for .env file in parent directory
if not exist "..\.env" (
    echo [WARNING] No .env file found in project root.
    echo Using default configuration from docker-compose.yml
    echo For custom settings, copy .env.example to .env in project root.
    echo.
)

echo ============================================================
echo  PHASE 1: SQL Server 2022 - Sample Database (ResearchAnalytics)
echo ============================================================
echo.

echo [Step 1/3] Starting SQL Server 2022 container...
docker compose --env-file ../.env up -d mssql
if errorlevel 1 (
    echo [ERROR] Failed to start SQL Server 2022 container.
    exit /b 1
)

echo.
echo [Step 2/3] Waiting for SQL Server 2022 to be healthy...
:wait_mssql
docker inspect --format="{{.State.Health.Status}}" local-agent-mssql 2>nul | findstr "healthy" >nul
if errorlevel 1 (
    echo   Still waiting for SQL Server 2022...
    timeout /t 5 /nobreak >nul
    goto wait_mssql
)
echo   SQL Server 2022 is healthy!

echo.
echo [Step 3/3] Running ResearchAnalytics initialization scripts...
docker compose --env-file ../.env --profile init up mssql-tools
if errorlevel 1 (
    echo [ERROR] Failed to run sample database initialization scripts.
    exit /b 1
)

echo.
echo ============================================================
echo  PHASE 2: SQL Server 2025 - Backend Database (LLM_BackEnd)
echo ============================================================
echo.

echo [Step 1/3] Starting SQL Server 2025 container...
docker compose --env-file ../.env up -d mssql-backend
if errorlevel 1 (
    echo [ERROR] Failed to start SQL Server 2025 container.
    exit /b 1
)

echo.
echo [Step 2/3] Waiting for SQL Server 2025 to be healthy...
:wait_backend
docker inspect --format="{{.State.Health.Status}}" local-agent-mssql-backend 2>nul | findstr "healthy" >nul
if errorlevel 1 (
    echo   Still waiting for SQL Server 2025...
    timeout /t 5 /nobreak >nul
    goto wait_backend
)
echo   SQL Server 2025 is healthy!

echo.
echo [Step 3/3] Running LLM_BackEnd initialization scripts...
echo   (includes app schema, vectors schema, and hybrid search setup)
docker compose --env-file ../.env --profile init up mssql-backend-tools
if errorlevel 1 (
    echo [ERROR] Failed to run backend database initialization scripts.
    exit /b 1
)

echo.
echo ============================================================
echo  PHASE 3: Redis Stack
echo ============================================================
echo.

echo Starting Redis Stack for caching and optional vector fallback...
docker compose --env-file ../.env up -d redis-stack
if errorlevel 1 (
    echo [ERROR] Failed to start Redis Stack container.
    exit /b 1
)

echo Waiting for Redis to be healthy...
:wait_redis
docker inspect --format="{{.State.Health.Status}}" local-agent-redis 2>nul | findstr "healthy" >nul
if errorlevel 1 (
    echo   Still waiting for Redis...
    timeout /t 3 /nobreak >nul
    goto wait_redis
)
echo   Redis Stack is healthy!

echo.
echo ============================================================
echo   Database Setup Complete!
echo ============================================================
echo.
echo   SQL Server 2022 (Sample Database):
echo     Server:   localhost,1433
echo     Database: ResearchAnalytics
echo     User:     sa
echo     Password: (see MSSQL_SA_PASSWORD in .env)
echo.
echo   SQL Server 2025 (Backend Database):
echo     Server:   localhost,1434
echo     Database: LLM_BackEnd
echo     User:     sa
echo     Password: (see MSSQL_SA_PASSWORD in .env)
echo     Features: Native VECTOR type, Full-Text Search, Hybrid Search
echo.
echo   Redis Stack:
echo     Server:   localhost:6379
echo     GUI:      http://localhost:8001 (RedisInsight)
echo.
echo   Backend Features Initialized:
echo     - app schema (conversations, messages, dashboards, settings)
echo     - vectors schema (document embeddings with native VECTOR type)
echo     - Hybrid Search (full-text + vector combined with RRF)
echo.
echo   To test connections:
echo     sqlcmd -S localhost,1433 -U sa -P "LocalLLM@2024!" -d ResearchAnalytics -Q "SELECT 1"
echo     sqlcmd -S localhost,1434 -U sa -P "LocalLLM@2024!" -d LLM_BackEnd -Q "SELECT 1"
echo.
echo   To stop all databases:
echo     docker compose --env-file ../.env down
echo.
echo   To stop and remove all data (DESTRUCTIVE):
echo     docker compose --env-file ../.env down -v
echo.

endlocal
