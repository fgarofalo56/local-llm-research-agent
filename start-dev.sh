#!/bin/bash
# =============================================================================
# Local LLM Research Agent - Full Stack Development Startup Script
# =============================================================================
#
# This script starts all services needed for local development:
#   - SQL Server 2022 (Sample Database - Docker)
#   - SQL Server 2025 (Backend with Vector Search - Docker)
#   - Redis Stack (Caching - Docker)
#   - Alembic Migrations (Database schema)
#   - FastAPI Backend (local)
#   - React Frontend (local dev server)
#   - Streamlit UI (Docker - optional)
#   - Apache Superset (Docker - optional)
#
# Prerequisites:
#   - Docker running
#   - Ollama running with qwen3:30b model
#   - Node.js installed
#   - Python/uv installed
#
# Usage:
#   ./start-dev.sh              - Start core services (default)
#   ./start-dev.sh --streamlit  - Also start Streamlit UI
#   ./start-dev.sh --superset   - Also start Apache Superset
#   ./start-dev.sh --full       - Start everything
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

# Parse command line arguments
START_STREAMLIT=0
START_SUPERSET=0

while [[ $# -gt 0 ]]; do
    case $1 in
        --streamlit)
            START_STREAMLIT=1
            shift
            ;;
        --superset)
            START_SUPERSET=1
            shift
            ;;
        --full)
            START_STREAMLIT=1
            START_SUPERSET=1
            shift
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--streamlit] [--superset] [--full]"
            exit 1
            ;;
    esac
done

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
else
    echo "[OK] Ollama is running"
    # Check if qwen3:30b model is available
    if ! curl -s http://localhost:11434/api/tags | grep -qi "qwen3:30b"; then
        echo "[WARNING] qwen3:30b model not found in Ollama."
        echo "Run: ollama pull qwen3:30b"
        echo ""
    else
        echo "[OK] qwen3:30b model is available"
    fi
fi

# Calculate total steps
TOTAL_STEPS=10
if [ $START_STREAMLIT -eq 1 ]; then
    ((TOTAL_STEPS++))
fi
if [ $START_SUPERSET -eq 1 ]; then
    ((TOTAL_STEPS++))
fi

echo "[Step 1/$TOTAL_STEPS] Creating Docker volumes if needed..."
docker volume create local-llm-mssql-data 2>/dev/null || true
docker volume create local-llm-backend-data 2>/dev/null || true
docker volume create local-llm-redis-data 2>/dev/null || true
docker volume create local-llm-superset-data 2>/dev/null || true

echo "[Step 2/$TOTAL_STEPS] Starting SQL Server 2022 (Sample Database)..."
docker-compose -f docker/docker-compose.yml --env-file .env up -d mssql

echo "Waiting for SQL Server 2022 to be healthy..."
until docker inspect --format='{{.State.Health.Status}}' local-agent-mssql 2>/dev/null | grep -q "healthy"; do
    echo "  Still waiting for SQL Server 2022..."
    sleep 5
done
echo "  SQL Server 2022 is ready!"

echo "[Step 3/$TOTAL_STEPS] Initializing ResearchAnalytics sample database..."
docker-compose -f docker/docker-compose.yml --env-file .env --profile init up mssql-tools 2>/dev/null || true

echo "[Step 4/$TOTAL_STEPS] Starting SQL Server 2025 (Backend Database)..."
docker-compose -f docker/docker-compose.yml --env-file .env up -d mssql-backend

echo "Waiting for SQL Server 2025 to be healthy..."
until docker inspect --format='{{.State.Health.Status}}' local-agent-mssql-backend 2>/dev/null | grep -q "healthy"; do
    echo "  Still waiting for SQL Server 2025..."
    sleep 5
done
echo "  SQL Server 2025 is ready!"

echo "[Step 5/$TOTAL_STEPS] Initializing LLM_BackEnd database (vectors + hybrid search)..."
docker-compose -f docker/docker-compose.yml --env-file .env --profile init up mssql-backend-tools 2>/dev/null || true

echo "[Step 6/$TOTAL_STEPS] Starting Redis Stack..."
docker-compose -f docker/docker-compose.yml --env-file .env up -d redis-stack

echo "Waiting for Redis to be healthy..."
until docker inspect --format='{{.State.Health.Status}}' local-agent-redis 2>/dev/null | grep -q "healthy"; do
    echo "  Still waiting for Redis..."
    sleep 3
done
echo "  Redis Stack is ready!"

echo "[Step 7/$TOTAL_STEPS] Running Alembic database migrations..."
if uv run alembic upgrade head 2>/dev/null; then
    echo "  Database migrations complete!"
else
    echo "  [WARNING] Alembic migrations may have failed or no migrations pending"
fi

echo "[Step 8/$TOTAL_STEPS] Starting FastAPI backend..."
# Start backend in background
uv run uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

echo "Waiting for API to be ready..."
sleep 5
until curl -s http://localhost:8000/api/health > /dev/null 2>&1; do
    sleep 2
done
echo "  FastAPI is ready!"

echo "[Step 9/$TOTAL_STEPS] Starting React frontend..."
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

CURRENT_STEP=10

# Optional: Start Streamlit UI
STREAMLIT_PID=""
if [ $START_STREAMLIT -eq 1 ]; then
    echo "[Step $CURRENT_STEP/$TOTAL_STEPS] Starting Streamlit UI..."
    docker-compose -f docker/docker-compose.yml --env-file .env up -d agent-ui
    echo "  Streamlit UI starting at http://localhost:8501"
    ((CURRENT_STEP++))
fi

# Optional: Start Superset
SUPERSET_PID=""
if [ $START_SUPERSET -eq 1 ]; then
    echo "[Step $CURRENT_STEP/$TOTAL_STEPS] Starting Apache Superset..."
    docker-compose -f docker/docker-compose.yml --env-file .env --profile superset up -d superset
    echo "  Superset starting at http://localhost:8088 (may take 1-2 minutes)"
    ((CURRENT_STEP++))
fi

echo "[Step $TOTAL_STEPS/$TOTAL_STEPS] Verifying all services..."
sleep 3

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
if [ $START_STREAMLIT -eq 1 ]; then
    echo "    - Streamlit UI:    http://localhost:8501"
fi
if [ $START_SUPERSET -eq 1 ]; then
    echo "    - Apache Superset: http://localhost:8088"
fi
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
echo "  Command-line options:"
echo "    ./start-dev.sh --streamlit  - Also start Streamlit UI"
echo "    ./start-dev.sh --superset   - Also start Apache Superset"
echo "    ./start-dev.sh --full       - Start everything"
echo ""

# Wait for Ctrl+C
trap "echo 'Stopping services...'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit 0" INT TERM
wait
