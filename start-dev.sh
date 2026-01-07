#!/bin/bash
# =============================================================================
# Local LLM Research Agent - Full Stack Development Startup Script
# =============================================================================
#
# This script starts all services needed for local development:
#   - SQL Server 2022 (Sample Database - Docker)
#   - SQL Server 2025 (Backend with Vector Search - Docker)
#   - Redis Stack (Caching - Docker)
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

echo "[Step 1/8] Creating Docker volumes if needed..."
docker volume create local-llm-mssql-data 2>/dev/null || true
docker volume create local-llm-backend-data 2>/dev/null || true
docker volume create local-llm-redis-data 2>/dev/null || true

echo "[Step 2/8] Starting SQL Server 2022 (Sample Database)..."
docker-compose -f docker/docker-compose.yml --env-file .env up -d mssql

echo "Waiting for SQL Server 2022 to be healthy..."
until docker inspect --format='{{.State.Health.Status}}' local-agent-mssql 2>/dev/null | grep -q "healthy"; do
    echo "  Still waiting for SQL Server 2022..."
    sleep 5
done
echo "  SQL Server 2022 is ready!"

echo "[Step 3/8] Initializing ResearchAnalytics sample database..."
docker-compose -f docker/docker-compose.yml --env-file .env --profile init up mssql-tools 2>/dev/null || true

echo "[Step 4/8] Starting SQL Server 2025 (Backend Database)..."
docker-compose -f docker/docker-compose.yml --env-file .env up -d mssql-backend

echo "Waiting for SQL Server 2025 to be healthy..."
until docker inspect --format='{{.State.Health.Status}}' local-agent-mssql-backend 2>/dev/null | grep -q "healthy"; do
    echo "  Still waiting for SQL Server 2025..."
    sleep 5
done
echo "  SQL Server 2025 is ready!"

echo "[Step 5/8] Initializing LLM_BackEnd database (vectors + hybrid search)..."
docker-compose -f docker/docker-compose.yml --env-file .env --profile init up mssql-backend-tools 2>/dev/null || true

echo "[Step 6/8] Starting Redis Stack..."
docker-compose -f docker/docker-compose.yml --env-file .env up -d redis-stack

echo "Waiting for Redis to be healthy..."
until docker inspect --format='{{.State.Health.Status}}' local-agent-redis 2>/dev/null | grep -q "healthy"; do
    echo "  Still waiting for Redis..."
    sleep 3
done
echo "  Redis Stack is ready!"

echo "[Step 7/8] Starting FastAPI backend..."
# Start backend in background
uv run uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

echo "Waiting for API to be ready..."
sleep 5
until curl -s http://localhost:8000/api/health > /dev/null 2>&1; do
    sleep 2
done
echo "  FastAPI is ready!"

echo "[Step 8/8] Starting React frontend..."
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

echo ""
echo "============================================================"
echo "  All services started successfully!"
echo "============================================================"
echo ""
echo "  Database Services:"
echo "    - SQL Server 2022: localhost:1433 (ResearchAnalytics)"
echo "    - SQL Server 2025: localhost:1434 (LLM_BackEnd + Vectors)"
echo "    - Redis Stack:     localhost:6379"
echo "    - RedisInsight:    http://localhost:8001"
echo ""
echo "  Application Services:"
echo "    - FastAPI Backend: http://localhost:8000"
echo "    - FastAPI Docs:    http://localhost:8000/docs"
echo "    - React Frontend:  http://localhost:5173"
echo ""
echo "  RAG Features:"
echo "    - Vector Store: SQL Server 2025 (native VECTOR type)"
echo "    - Embeddings:   nomic-embed-text (768 dimensions)"
echo "    - Hybrid Search: Enabled (semantic + full-text with RRF)"
echo "    - Documents:    PDF, DOCX, PPTX, XLSX, HTML, Markdown, Images"
echo ""
echo "  Process IDs:"
echo "    - Backend PID:  $BACKEND_PID"
echo "    - Frontend PID: $FRONTEND_PID"
echo ""
echo "  To stop:"
echo "    - Press Ctrl+C"
echo "    - Run: docker-compose -f docker/docker-compose.yml --env-file .env down"
echo ""

# Wait for Ctrl+C
trap "echo 'Stopping services...'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit 0" INT TERM
wait
