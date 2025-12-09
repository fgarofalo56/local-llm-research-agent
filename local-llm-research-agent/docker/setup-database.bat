@echo off
REM =============================================================================
REM setup-database.bat
REM Helper script to set up SQL Server Docker container and initialize database
REM =============================================================================

setlocal enabledelayedexpansion

echo.
echo ============================================
echo  Local LLM Research Agent - Database Setup
echo ============================================
echo.

REM Check if Docker is running
docker info >nul 2>&1
if errorlevel 1 (
    echo ERROR: Docker is not running. Please start Docker Desktop and try again.
    exit /b 1
)

REM Navigate to docker directory
cd /d "%~dp0"

echo Step 1: Starting SQL Server container...
docker compose up -d mssql
if errorlevel 1 (
    echo ERROR: Failed to start SQL Server container.
    exit /b 1
)

echo.
echo Step 2: Waiting for SQL Server to be healthy...
:wait_loop
docker inspect --format="{{.State.Health.Status}}" local-llm-mssql 2>nul | findstr "healthy" >nul
if errorlevel 1 (
    echo   Still waiting...
    timeout /t 5 /nobreak >nul
    goto wait_loop
)
echo   SQL Server is healthy!

echo.
echo Step 3: Running database initialization scripts...
docker compose --profile init up mssql-tools
if errorlevel 1 (
    echo ERROR: Failed to run initialization scripts.
    exit /b 1
)

echo.
echo ============================================
echo  Database Setup Complete!
echo ============================================
echo.
echo Connection Details:
echo   Server:   localhost,1433
echo   Database: ResearchAnalytics
echo   User:     sa
echo   Password: LocalLLM@2024! (or your MSSQL_SA_PASSWORD)
echo.
echo To connect with sqlcmd:
echo   sqlcmd -S localhost,1433 -U sa -P "LocalLLM@2024!" -d ResearchAnalytics
echo.
echo To stop the database:
echo   docker compose down
echo.
echo To stop and remove data:
echo   docker compose down -v
echo.

endlocal
