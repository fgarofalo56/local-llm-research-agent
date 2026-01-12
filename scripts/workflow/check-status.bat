@echo off
REM Check system status script
echo ========================================
echo System Status Check
echo ========================================
echo.

echo [1] Checking Ollama...
curl -s http://localhost:11434/api/tags >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Ollama is running
    curl -s http://localhost:11434/api/tags | findstr "name"
) else (
    echo [X] Ollama is NOT running
    echo    Start with: ollama serve
)
echo.

echo [2] Checking Docker containers...
docker ps --filter "name=local-agent" --format "table {{.Names}}\t{{.Status}}" 2>nul
if %errorlevel% neq 0 (
    echo [X] Docker is NOT running
) else (
    echo.
)
echo.

echo [3] Checking ports...
netstat -an | findstr "11434 1433 1434 8501" 2>nul
echo.

echo ========================================
echo Status check complete
echo ========================================
