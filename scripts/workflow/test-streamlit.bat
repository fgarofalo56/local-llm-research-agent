@echo off
REM Test script for Streamlit UI
echo ========================================
echo Testing Streamlit UI Setup
echo ========================================
echo.

echo [1/4] Checking Ollama...
curl -s http://localhost:11434/api/tags >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Ollama is running
) else (
    echo [WARNING] Ollama is not running
    echo Please start Ollama: ollama serve
)
echo.

echo [2/4] Checking Docker services...
docker ps --filter "name=local-agent-mssql" --format "{{.Names}}: {{.Status}}" 2>nul
if %errorlevel% equ 0 (
    echo [OK] Docker is available
) else (
    echo [WARNING] Docker is not running
)
echo.

echo [3/4] Starting Streamlit UI...
echo Press Ctrl+C to stop
echo.
uv run streamlit run src\ui\streamlit_app.py
