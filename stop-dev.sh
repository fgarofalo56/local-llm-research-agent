#!/bin/bash
# =============================================================================
# Local LLM Research Agent - Stop All Services Script
# =============================================================================
#
# This script stops all running services:
#   - Docker containers (SQL Server, Redis, Streamlit, Superset)
#   - FastAPI Backend (via pkill)
#   - React Frontend (via pkill)
#
# Usage:
#   ./stop-dev.sh         - Stop all services, keep data
#   ./stop-dev.sh --clean - Stop all services AND remove volumes (data loss!)
#
# =============================================================================

echo ""
echo "============================================================"
echo "  Stopping Local LLM Research Agent Services"
echo "============================================================"
echo ""

CLEAN_VOLUMES=0

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --clean)
            CLEAN_VOLUMES=1
            shift
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--clean]"
            exit 1
            ;;
    esac
done

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Stop local processes
echo "[Step 1/3] Stopping local processes..."

# Kill uvicorn processes (FastAPI)
if pgrep -f "uvicorn src.api.main:app" > /dev/null 2>&1; then
    echo "  Stopping FastAPI processes..."
    pkill -f "uvicorn src.api.main:app" 2>/dev/null || true
fi

# Kill npm/vite processes (React dev server)
if pgrep -f "vite" > /dev/null 2>&1; then
    echo "  Stopping React frontend (vite)..."
    pkill -f "vite" 2>/dev/null || true
fi

echo "  Local processes stopped"

# Stop Docker containers
echo "[Step 2/3] Stopping Docker containers..."

if [ $CLEAN_VOLUMES -eq 1 ]; then
    echo "  Stopping containers AND removing volumes..."
    echo "  WARNING: This will delete all database data!"
    docker-compose -f docker/docker-compose.yml --env-file .env --profile superset down -v 2>/dev/null || true
else
    echo "  Stopping containers (preserving data)..."
    docker-compose -f docker/docker-compose.yml --env-file .env --profile superset down 2>/dev/null || true
fi

echo "  Docker containers stopped"

# Verify cleanup
echo "[Step 3/3] Verifying cleanup..."
sleep 2

# Check if containers are still running
RUNNING_CONTAINERS=$(docker ps --filter "name=local-agent" --format "{{.Names}}" 2>/dev/null)
if [ -n "$RUNNING_CONTAINERS" ]; then
    echo "  [WARNING] Some containers may still be running:"
    echo "$RUNNING_CONTAINERS" | sed 's/^/    - /'
else
    echo "  All containers stopped"
fi

echo ""
echo "============================================================"
echo "  All services stopped"
echo "============================================================"
echo ""
if [ $CLEAN_VOLUMES -eq 1 ]; then
    echo "  Volumes were REMOVED - data has been deleted"
else
    echo "  Data volumes preserved - your data is safe"
    echo "  To also remove data: ./stop-dev.sh --clean"
fi
echo ""
