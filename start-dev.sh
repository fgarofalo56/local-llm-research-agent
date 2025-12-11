#!/bin/bash
# =============================================================================
# Local LLM Research Agent - Full Stack Development Startup Script
# =============================================================================
#
# This script starts all services needed for local development:
#   - SQL Server (Docker)
#   - Redis Stack (Docker)
#   - FastAPI Backend (local)
#   - React Frontend (local dev server)
#
# Prerequisites:
#   - Docker running
#   - Ollama running with qwen3:30b model
#   - Node.js installed
#   - Python/uv installed
#
# =============================================================================

set -e

echo ""
echo "============================================================"
echo "  Local LLM Research Agent - Development Stack"
echo "============================================================"
echo ""

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "[ERROR] .env file not found!"
    echo "Please copy .env.example to .env and configure it."
    exit 1
fi

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "[ERROR] Docker is not running!"
    echo "Please start Docker first."
    exit 1
fi

# Check if Ollama is running
if ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "[WARNING] Ollama does not appear to be running."
    echo "The agent will not work without Ollama."
    echo "Start Ollama and ensure qwen3:30b model is available."
    echo ""
fi

echo "[Step 1/5] Creating Docker volumes if needed..."
docker volume create local-llm-mssql-data 2>/dev/null || true
docker volume create local-llm-redis-data 2>/dev/null || true

echo "[Step 2/5] Starting Docker services (SQL Server + Redis)..."
docker-compose -f docker/docker-compose.yml --env-file .env up -d mssql redis-stack

echo "Waiting for SQL Server to be healthy..."
until docker-compose -f docker/docker-compose.yml ps mssql | grep -q "healthy"; do
    echo "  Still waiting for SQL Server..."
    sleep 5
done
echo "  SQL Server is ready!"

echo "[Step 3/5] Checking if database is initialized..."
docker-compose -f docker/docker-compose.yml --env-file .env --profile init up mssql-tools 2>/dev/null || true

echo "[Step 4/5] Starting FastAPI backend..."
# Start backend in background
uv run uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

echo "Waiting for API to be ready..."
sleep 5
until curl -s http://localhost:8000/api/health > /dev/null 2>&1; do
    sleep 2
done
echo "  FastAPI is ready!"

echo "[Step 5/5] Starting React frontend..."
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

echo ""
echo "============================================================"
echo "  All services started successfully!"
echo "============================================================"
echo ""
echo "  Services:"
echo "    - SQL Server:      localhost:1433"
echo "    - Redis:           localhost:6379"
echo "    - RedisInsight:    http://localhost:8001"
echo "    - FastAPI Backend: http://localhost:8000"
echo "    - FastAPI Docs:    http://localhost:8000/docs"
echo "    - React Frontend:  http://localhost:5173"
echo ""
echo "  Process IDs:"
echo "    - Backend PID:  $BACKEND_PID"
echo "    - Frontend PID: $FRONTEND_PID"
echo ""
echo "  To stop:"
echo "    - Press Ctrl+C"
echo "    - Run: docker-compose -f docker/docker-compose.yml down"
echo ""

# Wait for Ctrl+C
trap "echo 'Stopping services...'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit 0" INT TERM
wait
