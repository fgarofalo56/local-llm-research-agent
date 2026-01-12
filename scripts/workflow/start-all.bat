@echo off
setlocal enabledelayedexpansion

echo ========================================
echo Starting All Services for Streamlit UI
echo ========================================
echo.

REM Step 1: Check Ollama
echo [1/3] Checking Ollama...
curl -s http://localhost:11434/api/tags >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Ollama is already running
) else (
    echo [WARNING] Ollama is not running
    echo Please start Ollama in a separate window: ollama serve
    pause
)
echo.

REM Step 2: Start Docker services
echo [2/3] Starting Docker services...
docker-compose -f docker\docker-compose.yml --env-file .env up -d
if %errorlevel% equ 0 (
    echo [OK] Docker services started
    echo Waiting 10 seconds for SQL Server to initialize...
    timeout /t 10 /nobreak >nul
) else (
    echo [ERROR] Failed to start Docker services
    pause
    exit /b 1
)
echo.

REM Step 3: Show status
echo [3/3] Checking service status...
docker ps --filter "name=local-agent" --format "table {{.Names}}\t{{.Status}}"
echo.

echo ========================================
echo All services ready!
echo ========================================
echo.
echo Now run: test-streamlit.bat
echo Or manually: uv run streamlit run src\ui\streamlit_app.py
echo.
pause
