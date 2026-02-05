@echo off
REM =============================================================================
REM rebuild-deploy.bat
REM Fresh rebuild and deploy of ALL Docker services with data preservation
REM =============================================================================
REM
REM This script performs a complete rebuild and deployment:
REM   - Stops all running containers (gracefully)
REM   - Removes old container images (for fresh build)
REM   - Builds all images from scratch (no cache)
REM   - Starts all services in dependency order
REM   - Waits for health checks
REM
REM DATA PRESERVATION:
REM   - Database volumes are PRESERVED (SQL Server data, settings)
REM   - Redis data is PRESERVED
REM   - Superset configuration is PRESERVED
REM   - Only container images are rebuilt
REM
REM Usage:
REM   rebuild-deploy.bat              - Rebuild and deploy all services (full stack)
REM   rebuild-deploy.bat --quick      - Quick rebuild (use cached layers)
REM   rebuild-deploy.bat --no-superset - Skip Superset (faster startup)
REM   rebuild-deploy.bat --clean-data - WARNING: Also removes all data volumes
REM
REM =============================================================================

setlocal EnableDelayedExpansion

echo.
echo ============================================================
echo   Local LLM Research Agent - REBUILD AND DEPLOY
echo ============================================================
echo.

REM Parse command line arguments
set QUICK_BUILD=0
set NO_SUPERSET=0
set CLEAN_DATA=0

:parse_args
if "%~1"=="" goto :done_args
if /i "%~1"=="--quick" set QUICK_BUILD=1
if /i "%~1"=="--no-superset" set NO_SUPERSET=1
if /i "%~1"=="--clean-data" set CLEAN_DATA=1
shift
goto :parse_args
:done_args

REM Warn about clean-data mode
if %CLEAN_DATA%==1 (
    echo.
    echo   *** WARNING: --clean-data mode enabled ***
    echo   This will DELETE ALL DATABASE DATA including:
    echo     - SQL Server databases (ResearchAnalytics, LLM_BackEnd)
    echo     - Redis cache data
    echo     - Superset configuration
    echo.
    set /p CONFIRM="Are you sure? Type YES to continue: "
    if /i not "!CONFIRM!"=="YES" (
        echo Aborted.
        exit /b 0
    )
)

REM Check prerequisites
echo [PREREQ] Checking prerequisites...

REM Check .env file
if not exist ".env" (
    echo [ERROR] .env file not found!
    echo Please copy .env.example to .env and configure it.
    exit /b 1
)
echo   [OK] .env file found

REM Check Docker
docker info >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker is not running!
    echo Please start Docker Desktop and try again.
    exit /b 1
)
echo   [OK] Docker is running

REM Check Ollama
curl -s http://localhost:11434/api/tags >nul 2>&1
if errorlevel 1 (
    echo   [WARN] Ollama is not running - agent features will not work
    echo          Start Ollama before using the application.
) else (
    echo   [OK] Ollama is running
)

echo.

REM =============================================================================
REM PHASE 1: Stop and clean up
REM =============================================================================
echo ============================================================
echo  PHASE 1: Stopping existing services
echo ============================================================
echo.

echo [1/3] Stopping all containers gracefully...
docker-compose -f docker/docker-compose.yml --env-file .env --profile full down 2>nul
docker-compose -f docker/docker-compose.yml --env-file .env down 2>nul
echo   Containers stopped.

echo [2/3] Removing old container images...
REM Remove project-specific images (keeps base images like SQL Server, Redis)
docker rmi local-agent-ai-stack-agent-ui 2>nul
docker rmi local-agent-ai-stack-agent-cli 2>nul
docker rmi local-agent-ai-stack-api 2>nul
docker rmi local-agent-ai-stack-frontend 2>nul
docker rmi local-agent-ai-stack-superset 2>nul
echo   Old images removed.

echo [3/3] Cleaning up dangling images...
docker image prune -f >nul 2>&1
echo   Cleanup complete.

REM Handle clean-data if requested
if %CLEAN_DATA%==1 (
    echo.
    echo [CLEAN-DATA] Removing data volumes...
    docker volume rm local-llm-mssql-data 2>nul
    docker volume rm local-llm-backend-data 2>nul
    docker volume rm local-llm-redis-data 2>nul
    docker volume rm local-llm-superset-data 2>nul
    echo   Data volumes removed.
)

echo.

REM =============================================================================
REM PHASE 2: Ensure volumes exist (preserves data if not clean-data)
REM =============================================================================
echo ============================================================
echo  PHASE 2: Ensuring data volumes exist
echo ============================================================
echo.

echo Creating/verifying Docker volumes (data is preserved if exists)...
docker volume create local-llm-mssql-data >nul 2>&1
docker volume create local-llm-backend-data >nul 2>&1
docker volume create local-llm-redis-data >nul 2>&1
docker volume create local-llm-superset-data >nul 2>&1

echo   [OK] local-llm-mssql-data (SQL Server 2022)
echo   [OK] local-llm-backend-data (SQL Server 2025)
echo   [OK] local-llm-redis-data (Redis)
echo   [OK] local-llm-superset-data (Superset)
echo.

REM =============================================================================
REM PHASE 3: Build all images
REM =============================================================================
echo ============================================================
echo  PHASE 3: Building all Docker images
echo ============================================================
echo.

if %QUICK_BUILD%==1 (
    echo   Mode: QUICK BUILD (using cached layers where possible)
    echo.
    docker-compose -f docker/docker-compose.yml --env-file .env --profile full build
) else (
    echo   Mode: FRESH BUILD (no cache - this will take several minutes)
    echo.
    docker-compose -f docker/docker-compose.yml --env-file .env --profile full build --no-cache
)

if errorlevel 1 (
    echo [ERROR] Docker build failed!
    exit /b 1
)
echo.
echo   Build complete!
echo.

REM =============================================================================
REM PHASE 4: Start databases first
REM =============================================================================
echo ============================================================
echo  PHASE 4: Starting database services
echo ============================================================
echo.

echo [1/4] Starting SQL Server 2022 (Sample Database)...
docker-compose -f docker/docker-compose.yml --env-file .env up -d mssql

echo Waiting for SQL Server 2022 to be healthy...
:wait_sql
timeout /t 5 /nobreak >nul
docker inspect --format="{{.State.Health.Status}}" local-agent-mssql 2>nul | findstr "healthy" >nul
if errorlevel 1 (
    echo   Still waiting for SQL Server 2022...
    goto wait_sql
)
echo   [OK] SQL Server 2022 is healthy!

echo [2/4] Starting SQL Server 2025 (Backend Database)...
docker-compose -f docker/docker-compose.yml --env-file .env up -d mssql-backend

echo Waiting for SQL Server 2025 to be healthy...
:wait_backend
timeout /t 5 /nobreak >nul
docker inspect --format="{{.State.Health.Status}}" local-agent-mssql-backend 2>nul | findstr "healthy" >nul
if errorlevel 1 (
    echo   Still waiting for SQL Server 2025...
    goto wait_backend
)
echo   [OK] SQL Server 2025 is healthy!

echo [3/4] Starting Redis Stack...
docker-compose -f docker/docker-compose.yml --env-file .env up -d redis-stack

echo Waiting for Redis to be healthy...
:wait_redis
timeout /t 3 /nobreak >nul
docker inspect --format="{{.State.Health.Status}}" local-agent-redis 2>nul | findstr "healthy" >nul
if errorlevel 1 (
    echo   Still waiting for Redis...
    goto wait_redis
)
echo   [OK] Redis Stack is healthy!

echo [4/4] Running database initialization (if needed)...
REM These will only create tables/data if they don't exist
docker-compose -f docker/docker-compose.yml --env-file .env --profile init up mssql-tools 2>nul
docker-compose -f docker/docker-compose.yml --env-file .env --profile init up mssql-backend-tools 2>nul
echo   [OK] Database initialization complete!
echo.

REM =============================================================================
REM PHASE 5: Start application services
REM =============================================================================
echo ============================================================
echo  PHASE 5: Starting application services
echo ============================================================
echo.

echo [1/4] Starting FastAPI Backend...
docker-compose -f docker/docker-compose.yml --env-file .env --profile api up -d api

echo Waiting for FastAPI to be ready...
:wait_api
timeout /t 5 /nobreak >nul
curl -s http://localhost:8000/api/health >nul 2>&1
if errorlevel 1 (
    echo   Still waiting for FastAPI...
    goto wait_api
)
echo   [OK] FastAPI is ready!

echo [2/4] Starting React Frontend...
docker-compose -f docker/docker-compose.yml --env-file .env --profile frontend up -d frontend
timeout /t 5 /nobreak >nul
echo   [OK] React Frontend starting...

echo [3/4] Starting Streamlit UI...
docker-compose -f docker/docker-compose.yml --env-file .env up -d agent-ui
timeout /t 3 /nobreak >nul
echo   [OK] Streamlit UI starting...

if %NO_SUPERSET%==0 (
    echo [4/4] Starting Apache Superset...
    docker-compose -f docker/docker-compose.yml --env-file .env --profile superset up -d superset
    echo   [OK] Superset starting (may take 1-2 minutes to initialize)...
) else (
    echo [4/4] Skipping Superset (--no-superset flag)
)

echo.

REM =============================================================================
REM PHASE 6: Final verification
REM =============================================================================
echo ============================================================
echo  PHASE 6: Verifying deployment
echo ============================================================
echo.

echo Waiting for all services to stabilize...
timeout /t 10 /nobreak >nul

echo.
echo Checking service status...
echo.
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | findstr /v "mssql-tools backend-tools"
echo.

REM =============================================================================
REM Complete!
REM =============================================================================
echo.
echo ============================================================
echo   REBUILD AND DEPLOY COMPLETE!
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
echo     - Streamlit UI:    http://localhost:8501
if %NO_SUPERSET%==0 (
    echo     - Apache Superset: http://localhost:8088
)
echo.
echo   Data Preservation:
echo     - Database data: PRESERVED (volumes not deleted)
echo     - Redis cache:   PRESERVED
echo     - Superset config: PRESERVED
echo.
echo   Useful commands:
echo     View logs:    docker-compose -f docker/docker-compose.yml logs -f [service]
echo     Stop all:     docker-compose -f docker/docker-compose.yml --profile full down
echo     CLI access:   docker-compose -f docker/docker-compose.yml --profile cli run --rm agent-cli
echo.
echo   Press any key to open the React app in your browser...
pause >nul

start http://localhost:5173
