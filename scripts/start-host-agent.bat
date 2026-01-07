@echo off
REM Host Agent Sidecar Startup Script (Windows)
REM Runs the host agent for Docker service management

echo ============================================
echo Host Agent Sidecar for Docker
echo ============================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found in PATH
    echo Please install Python 3.10+ from https://python.org
    pause
    exit /b 1
)

REM Change to project root directory
cd /d "%~dp0\.."

REM Check if required packages are installed
python -c "import fastapi, uvicorn, pydantic, httpx" >nul 2>&1
if errorlevel 1 (
    echo Installing required packages...
    pip install fastapi uvicorn pydantic httpx
)

REM Run the host agent
echo Starting Host Agent on port %HOST_AGENT_PORT%
echo (default: 5280 if not set)
echo.
python scripts/host_agent.py

pause
