#!/bin/bash
# Host Agent Sidecar Startup Script (Linux/Mac)
# Runs the host agent for Docker service management

echo "============================================"
echo "Host Agent Sidecar for Docker"
echo "============================================"
echo ""

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python3 not found in PATH"
    echo "Please install Python 3.10+"
    exit 1
fi

# Change to project root directory
cd "$(dirname "$0")/.."

# Check if required packages are installed
if ! python3 -c "import fastapi, uvicorn, pydantic, httpx" &> /dev/null; then
    echo "Installing required packages..."
    pip3 install fastapi uvicorn pydantic httpx
fi

# Run the host agent
echo "Starting Host Agent on port ${HOST_AGENT_PORT:-5280}"
echo ""
python3 scripts/host_agent.py
