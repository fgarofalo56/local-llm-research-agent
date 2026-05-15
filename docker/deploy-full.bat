@echo off
REM =============================================================================
REM deploy-full.bat
REM Full-stack deployment for Local LLM Research Agent (Windows)
REM
REM Deploys ALL services in the correct order:
REM   1. Pre-flight checks (Docker, Ollama, port conflicts)
REM   2. Build all container images
REM   3. Start databases (SQL Server 2022, 2025, Redis)
REM   4. Initialize databases (first run only)
REM   5. Start application services (API, Streamlit, React, Superset)
REM   6. Print connection info
REM
REM Usage:
REM   docker\deploy-full.bat              - Full deploy
REM   docker\deploy-full.bat --no-init    - Skip DB init (already initialized)
REM   docker\deploy-full.bat --no-superset - Skip Superset
REM   docker\deploy-full.bat --build-only - Build images only
REM =============================================================================

setlocal enabledelayedexpansion

set "SCRIPT_DIR=%~dp0"
set "PROJECT_ROOT=%SCRIPT_DIR%.."
set "COMPOSE_FILE=%SCRIPT_DIR%docker-compose.yml"
set "ENV_FILE=%PROJECT_ROOT%\.env"
set "COMPOSE_CMD=docker compose -f %COMPOSE_FILE% --env-file %ENV_FILE%"

REM ---------------------------------------------------------------------------
REM Parse arguments
REM ---------------------------------------------------------------------------
set "SKIP_INIT=false"
set "SKIP_SUPERSET=false"
set "BUILD_ONLY=false"

:parse_args
if "%~1"=="" goto :args_done
if "%~1"=="--no-init" set "SKIP_INIT=true" & shift & goto :parse_args
if "%~1"=="--no-superset" set "SKIP_SUPERSET=true" & shift & goto :parse_args
if "%~1"=="--build-only" set "BUILD_ONLY=true" & shift & goto :parse_args
if "%~1"=="--help" goto :show_help
if "%~1"=="-h" goto :show_help
echo [ERROR] Unknown argument: %~1
echo Run with --help for usage.
exit /b 1

:show_help
echo Usage: docker\deploy-full.bat [OPTIONS]
echo.
echo Options:
echo   --no-init       Skip database initialization (if already done)
echo   --no-superset   Skip Apache Superset service
echo   --build-only    Build images only, don't start services
echo   --help, -h      Show this help
exit /b 0

:args_done

REM ---------------------------------------------------------------------------
REM Load .env for port variables
REM ---------------------------------------------------------------------------
set "MSSQL_PORT=1433"
set "BACKEND_DB_PORT=1434"
set "API_PORT=8000"
set "STREAMLIT_PORT=8501"
set "FRONTEND_PORT=5173"
set "REDIS_PORT=6379"
set "REDIS_INSIGHT_PORT=8001"
set "SUPERSET_PORT=8088"

if exist "%ENV_FILE%" (
    for /f "usebackq eol=# tokens=1,* delims==" %%a in ("%ENV_FILE%") do (
        if not "%%a"=="" if not "%%b"=="" (
            REM Strip inline comments and extract just the first token as value
            for /f "tokens=1 delims=#" %%h in ("%%b") do (
                for /f "tokens=1" %%v in ("%%h") do (
                    if "%%a"=="MSSQL_PORT" set "MSSQL_PORT=%%v"
                    if "%%a"=="BACKEND_DB_PORT" set "BACKEND_DB_PORT=%%v"
                    if "%%a"=="API_PORT" set "API_PORT=%%v"
                    if "%%a"=="STREAMLIT_PORT" set "STREAMLIT_PORT=%%v"
                    if "%%a"=="FRONTEND_PORT" set "FRONTEND_PORT=%%v"
                    if "%%a"=="REDIS_PORT" set "REDIS_PORT=%%v"
                    if "%%a"=="REDIS_INSIGHT_PORT" set "REDIS_INSIGHT_PORT=%%v"
                    if "%%a"=="SUPERSET_PORT" set "SUPERSET_PORT=%%v"
                )
            )
        )
    )
)

REM ---------------------------------------------------------------------------
REM PHASE 0: Pre-flight checks
REM ---------------------------------------------------------------------------
echo.
echo ============================================================
echo   Local LLM Research Agent - Full Stack Deployment
echo ============================================================
echo.

echo [Phase 0] Pre-flight checks...
echo.

REM Check Docker
docker info >nul 2>&1
if errorlevel 1 (
    echo   [FAIL] Docker is not running. Please start Docker Desktop and try again.
    exit /b 1
)
echo   [OK] Docker is running

REM Check .env
if not exist "%ENV_FILE%" (
    echo   [WARN] No .env file found at %ENV_FILE%
    echo          Creating from .env.example...
    if exist "%PROJECT_ROOT%\.env.example" (
        copy "%PROJECT_ROOT%\.env.example" "%ENV_FILE%" >nul
        echo   [OK] Created .env from .env.example ^(edit with your settings^)
    ) else (
        echo   [FAIL] No .env.example found either. Cannot continue.
        exit /b 1
    )
) else (
    echo   [OK] .env file found
)

REM Check Ollama
curl -sf http://localhost:11434/api/tags >nul 2>&1
if errorlevel 1 (
    echo   [WARN] Ollama not detected at localhost:11434
    echo          LLM features will not work until Ollama is started.
    echo          Run: ollama serve
) else (
    echo   [OK] Ollama is running on host
)

REM Port conflict check
echo.
echo [Phase 0.5] Port conflict check...
echo.
if exist "%SCRIPT_DIR%check-ports.bat" (
    call "%SCRIPT_DIR%check-ports.bat"
    if !errorlevel! neq 0 (
        echo.
        echo   Port conflicts detected! Options:
        echo     1. Auto-fix:  docker\check-ports.bat --fix
        echo     2. Manual:    Edit .env port variables
        echo     3. Continue:  Conflicts may cause startup failures
        echo.
        set /p "confirm=  Continue anyway? (y/N): "
        if /i not "!confirm!"=="y" (
            echo   Aborted. Resolve port conflicts first.
            exit /b 1
        )
    )
)

REM ---------------------------------------------------------------------------
REM PHASE 1: Build images
REM ---------------------------------------------------------------------------
echo.
echo ============================================================
echo [Phase 1] Building container images...
echo ============================================================
echo.

echo   Building Streamlit UI image...
%COMPOSE_CMD% build agent-ui
if errorlevel 1 (
    echo   [FAIL] Failed to build Streamlit UI image
    exit /b 1
)

echo.
echo   Building FastAPI API image...
%COMPOSE_CMD% build api
if errorlevel 1 (
    echo   [FAIL] Failed to build FastAPI API image
    exit /b 1
)

echo.
echo   Building React Frontend image...
%COMPOSE_CMD% build frontend
if errorlevel 1 (
    echo   [FAIL] Failed to build React Frontend image
    exit /b 1
)

if "%SKIP_SUPERSET%"=="false" (
    echo.
    echo   Building Superset image...
    %COMPOSE_CMD% build superset
    if errorlevel 1 (
        echo   [FAIL] Failed to build Superset image
        exit /b 1
    )
)

echo.
echo   [OK] All images built successfully

if "%BUILD_ONLY%"=="true" (
    echo.
    echo   --build-only flag set. Images built. Exiting.
    exit /b 0
)

REM ---------------------------------------------------------------------------
REM PHASE 2: Start database services
REM ---------------------------------------------------------------------------
echo.
echo ============================================================
echo [Phase 2] Starting database services...
echo ============================================================
echo.

echo   Starting SQL Server 2022 ^(sample data^)...
%COMPOSE_CMD% up -d mssql

echo   Starting SQL Server 2025 ^(backend + vectors^)...
%COMPOSE_CMD% up -d mssql-backend

echo   Starting Redis Stack...
%COMPOSE_CMD% up -d redis-stack

echo.
echo   Waiting for databases to be healthy...

call :wait_healthy "local-agent-mssql" "SQL Server 2022" 120
if errorlevel 1 exit /b 1

call :wait_healthy "local-agent-mssql-backend" "SQL Server 2025" 120
if errorlevel 1 exit /b 1

call :wait_healthy "local-agent-redis" "Redis Stack" 60
if errorlevel 1 exit /b 1

echo.
echo   [OK] All databases are healthy

REM ---------------------------------------------------------------------------
REM PHASE 3: Initialize databases
REM ---------------------------------------------------------------------------
if "%SKIP_INIT%"=="false" (
    echo.
    echo ============================================================
    echo [Phase 3] Initializing databases ^(safe to re-run^)...
    echo ============================================================
    echo.

    echo   Running ResearchAnalytics init scripts ^(SQL Server 2022^)...
    %COMPOSE_CMD% --profile init up mssql-tools
    echo.

    echo   Running LLM_BackEnd init scripts ^(SQL Server 2025^)...
    %COMPOSE_CMD% --profile init up mssql-backend-tools
    echo.

    echo   [OK] Database initialization complete
) else (
    echo.
    echo [Phase 3] Skipped database initialization ^(--no-init^)
)

REM ---------------------------------------------------------------------------
REM PHASE 4: Start application services
REM ---------------------------------------------------------------------------
echo.
echo ============================================================
echo [Phase 4] Starting application services...
echo ============================================================
echo.

if "%SKIP_SUPERSET%"=="false" (
    echo   Starting full stack ^(API + Streamlit + React + Superset^)...
    %COMPOSE_CMD% --profile full up -d
) else (
    echo   Starting stack without Superset ^(API + Streamlit + React^)...
    %COMPOSE_CMD% --profile frontend up -d
    %COMPOSE_CMD% up -d agent-ui
)

echo.
echo   Waiting for application services to start...
echo   ^(This may take 30-60 seconds^)
timeout /t 15 /nobreak >nul

echo.
echo   [OK] Application services started

REM ---------------------------------------------------------------------------
REM PHASE 5: Summary
REM ---------------------------------------------------------------------------
echo.
echo ============================================================
echo   Deployment Complete!
echo ============================================================
echo.
echo   Web Interfaces:
echo     React Frontend:  http://localhost:%FRONTEND_PORT%
echo     FastAPI Docs:    http://localhost:%API_PORT%/docs
echo     API Health:      http://localhost:%API_PORT%/api/health
echo     Streamlit UI:    http://localhost:%STREAMLIT_PORT%
if "%SKIP_SUPERSET%"=="false" (
echo     Superset BI:     http://localhost:%SUPERSET_PORT%
)
echo     RedisInsight:    http://localhost:%REDIS_INSIGHT_PORT%
echo.
echo   Databases:
echo     SQL Server 2022: localhost,%MSSQL_PORT%  ^(ResearchAnalytics^)
echo     SQL Server 2025: localhost,%BACKEND_DB_PORT%  ^(LLM_BackEnd^)
echo     Redis Stack:     localhost:%REDIS_PORT%
echo.
echo   Useful Commands:
echo     View logs:       docker compose -f docker/docker-compose.yml logs -f [service]
echo     Stop all:        docker compose -f docker/docker-compose.yml down
echo     Restart service: docker compose -f docker/docker-compose.yml restart [service]
echo     Run CLI:         docker compose -f docker/docker-compose.yml --profile cli run --rm agent-cli
echo.
echo   Container Status:
docker ps --filter "name=local-agent-" --format "    {{.Names}}   {{.Status}}"
echo.

goto :eof

REM ===========================================================================
REM Subroutine: wait_healthy container_name label timeout_seconds
REM ===========================================================================
:wait_healthy
set "wh_container=%~1"
set "wh_label=%~2"
set "wh_timeout=%~3"
set "wh_elapsed=0"

:wh_loop
if %wh_elapsed% GEQ %wh_timeout% (
    echo   [FAIL] %wh_label% did not become healthy after %wh_timeout%s
    echo          Check logs: docker logs %wh_container%
    exit /b 1
)

for /f "tokens=*" %%s in ('docker inspect --format "{{.State.Health.Status}}" %wh_container% 2^>nul') do (
    if "%%s"=="healthy" (
        echo   [OK] %wh_label% is healthy ^(%wh_elapsed%s^)
        exit /b 0
    )
)

timeout /t 3 /nobreak >nul
set /a wh_elapsed+=3
goto :wh_loop
