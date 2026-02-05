#!/bin/bash
# =============================================================================
# rebuild-deploy.sh
# Fresh rebuild and deploy of ALL Docker services with data preservation
# =============================================================================
#
# This script performs a complete rebuild and deployment:
#   - Stops all running containers (gracefully)
#   - Removes old container images (for fresh build)
#   - Builds all images from scratch (no cache)
#   - Starts all services in dependency order
#   - Waits for health checks
#
# DATA PRESERVATION:
#   - Database volumes are PRESERVED (SQL Server data, settings)
#   - Redis data is PRESERVED
#   - Superset configuration is PRESERVED
#   - Only container images are rebuilt
#
# Usage:
#   ./rebuild-deploy.sh              - Rebuild and deploy all services (full stack)
#   ./rebuild-deploy.sh --quick      - Quick rebuild (use cached layers)
#   ./rebuild-deploy.sh --no-superset - Skip Superset (faster startup)
#   ./rebuild-deploy.sh --clean-data - WARNING: Also removes all data volumes
#
# =============================================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Parse arguments
QUICK_BUILD=0
NO_SUPERSET=0
CLEAN_DATA=0

while [[ $# -gt 0 ]]; do
    case $1 in
        --quick)
            QUICK_BUILD=1
            shift
            ;;
        --no-superset)
            NO_SUPERSET=1
            shift
            ;;
        --clean-data)
            CLEAN_DATA=1
            shift
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--quick] [--no-superset] [--clean-data]"
            exit 1
            ;;
    esac
done

echo ""
echo -e "${CYAN}============================================================${NC}"
echo -e "${CYAN}  Local LLM Research Agent - REBUILD AND DEPLOY${NC}"
echo -e "${CYAN}============================================================${NC}"
echo ""

# Handle clean-data warning
if [ $CLEAN_DATA -eq 1 ]; then
    echo ""
    echo -e "${RED}  *** WARNING: --clean-data mode enabled ***${NC}"
    echo -e "${RED}  This will DELETE ALL DATABASE DATA including:${NC}"
    echo -e "${RED}    - SQL Server databases (ResearchAnalytics, LLM_BackEnd)${NC}"
    echo -e "${RED}    - Redis cache data${NC}"
    echo -e "${RED}    - Superset configuration${NC}"
    echo ""
    read -p "Are you sure? Type YES to continue: " CONFIRM
    if [ "$CONFIRM" != "YES" ]; then
        echo "Aborted."
        exit 0
    fi
fi

# =============================================================================
# Prerequisites Check
# =============================================================================
echo -e "${CYAN}[PREREQ] Checking prerequisites...${NC}"

# Check .env
if [ ! -f ".env" ]; then
    echo -e "${RED}  [ERROR] .env file not found!${NC}"
    echo "Please copy .env.example to .env and configure it."
    exit 1
fi
echo -e "${GREEN}  [OK] .env file found${NC}"

# Check Docker
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}  [ERROR] Docker is not running!${NC}"
    echo "Please start Docker and try again."
    exit 1
fi
echo -e "${GREEN}  [OK] Docker is running${NC}"

# Check Ollama
if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo -e "${GREEN}  [OK] Ollama is running${NC}"
else
    echo -e "${YELLOW}  [WARN] Ollama is not running - agent features will not work${NC}"
fi

echo ""

# =============================================================================
# PHASE 1: Stop and Clean
# =============================================================================
echo -e "${CYAN}============================================================${NC}"
echo -e "${CYAN} PHASE 1: Stopping existing services${NC}"
echo -e "${CYAN}============================================================${NC}"
echo ""

echo "[1/3] Stopping all containers gracefully..."
docker-compose -f docker/docker-compose.yml --env-file .env --profile full down 2>/dev/null || true
docker-compose -f docker/docker-compose.yml --env-file .env down 2>/dev/null || true
echo -e "${GREEN}  Containers stopped.${NC}"

echo "[2/3] Removing old container images..."
docker rmi local-agent-ai-stack-agent-ui 2>/dev/null || true
docker rmi local-agent-ai-stack-agent-cli 2>/dev/null || true
docker rmi local-agent-ai-stack-api 2>/dev/null || true
docker rmi local-agent-ai-stack-frontend 2>/dev/null || true
docker rmi local-agent-ai-stack-superset 2>/dev/null || true
echo -e "${GREEN}  Old images removed.${NC}"

echo "[3/3] Cleaning up dangling images..."
docker image prune -f > /dev/null 2>&1 || true
echo -e "${GREEN}  Cleanup complete.${NC}"

if [ $CLEAN_DATA -eq 1 ]; then
    echo ""
    echo -e "${YELLOW}[CLEAN-DATA] Removing data volumes...${NC}"
    docker volume rm local-llm-mssql-data 2>/dev/null || true
    docker volume rm local-llm-backend-data 2>/dev/null || true
    docker volume rm local-llm-redis-data 2>/dev/null || true
    docker volume rm local-llm-superset-data 2>/dev/null || true
    echo -e "${GREEN}  Data volumes removed.${NC}"
fi

echo ""

# =============================================================================
# PHASE 2: Ensure Volumes
# =============================================================================
echo -e "${CYAN}============================================================${NC}"
echo -e "${CYAN} PHASE 2: Ensuring data volumes exist${NC}"
echo -e "${CYAN}============================================================${NC}"
echo ""

echo "Creating/verifying Docker volumes (data preserved if exists)..."
docker volume create local-llm-mssql-data > /dev/null 2>&1 || true
docker volume create local-llm-backend-data > /dev/null 2>&1 || true
docker volume create local-llm-redis-data > /dev/null 2>&1 || true
docker volume create local-llm-superset-data > /dev/null 2>&1 || true

echo -e "${GREEN}  [OK] local-llm-mssql-data (SQL Server 2022)${NC}"
echo -e "${GREEN}  [OK] local-llm-backend-data (SQL Server 2025)${NC}"
echo -e "${GREEN}  [OK] local-llm-redis-data (Redis)${NC}"
echo -e "${GREEN}  [OK] local-llm-superset-data (Superset)${NC}"
echo ""

# =============================================================================
# PHASE 3: Build Images
# =============================================================================
echo -e "${CYAN}============================================================${NC}"
echo -e "${CYAN} PHASE 3: Building all Docker images${NC}"
echo -e "${CYAN}============================================================${NC}"
echo ""

if [ $QUICK_BUILD -eq 1 ]; then
    echo -e "${YELLOW}  Mode: QUICK BUILD (using cached layers)${NC}"
    echo ""
    docker-compose -f docker/docker-compose.yml --env-file .env --profile full build
else
    echo -e "${YELLOW}  Mode: FRESH BUILD (no cache - this will take several minutes)${NC}"
    echo ""
    docker-compose -f docker/docker-compose.yml --env-file .env --profile full build --no-cache
fi

echo -e "${GREEN}  Build complete!${NC}"
echo ""

# =============================================================================
# PHASE 4: Start Databases
# =============================================================================
echo -e "${CYAN}============================================================${NC}"
echo -e "${CYAN} PHASE 4: Starting database services${NC}"
echo -e "${CYAN}============================================================${NC}"
echo ""

# SQL Server 2022
echo "[1/4] Starting SQL Server 2022 (Sample Database)..."
docker-compose -f docker/docker-compose.yml --env-file .env up -d mssql

echo "Waiting for SQL Server 2022 to be healthy..."
while [ "$(docker inspect --format='{{.State.Health.Status}}' local-agent-mssql 2>/dev/null)" != "healthy" ]; do
    echo "  Still waiting for SQL Server 2022..."
    sleep 5
done
echo -e "${GREEN}  [OK] SQL Server 2022 is healthy!${NC}"

# SQL Server 2025
echo "[2/4] Starting SQL Server 2025 (Backend Database)..."
docker-compose -f docker/docker-compose.yml --env-file .env up -d mssql-backend

echo "Waiting for SQL Server 2025 to be healthy..."
while [ "$(docker inspect --format='{{.State.Health.Status}}' local-agent-mssql-backend 2>/dev/null)" != "healthy" ]; do
    echo "  Still waiting for SQL Server 2025..."
    sleep 5
done
echo -e "${GREEN}  [OK] SQL Server 2025 is healthy!${NC}"

# Redis
echo "[3/4] Starting Redis Stack..."
docker-compose -f docker/docker-compose.yml --env-file .env up -d redis-stack

echo "Waiting for Redis to be healthy..."
while [ "$(docker inspect --format='{{.State.Health.Status}}' local-agent-redis 2>/dev/null)" != "healthy" ]; do
    echo "  Still waiting for Redis..."
    sleep 3
done
echo -e "${GREEN}  [OK] Redis Stack is healthy!${NC}"

# Database init
echo "[4/4] Running database initialization (if needed)..."
docker-compose -f docker/docker-compose.yml --env-file .env --profile init up mssql-tools 2>/dev/null || true
docker-compose -f docker/docker-compose.yml --env-file .env --profile init up mssql-backend-tools 2>/dev/null || true
echo -e "${GREEN}  [OK] Database initialization complete!${NC}"
echo ""

# =============================================================================
# PHASE 5: Start Application Services
# =============================================================================
echo -e "${CYAN}============================================================${NC}"
echo -e "${CYAN} PHASE 5: Starting application services${NC}"
echo -e "${CYAN}============================================================${NC}"
echo ""

# FastAPI
echo "[1/4] Starting FastAPI Backend..."
docker-compose -f docker/docker-compose.yml --env-file .env --profile api up -d api

echo "Waiting for FastAPI to be ready..."
while ! curl -s http://localhost:8000/api/health > /dev/null 2>&1; do
    echo "  Still waiting for FastAPI..."
    sleep 5
done
echo -e "${GREEN}  [OK] FastAPI is ready!${NC}"

# React Frontend
echo "[2/4] Starting React Frontend..."
docker-compose -f docker/docker-compose.yml --env-file .env --profile frontend up -d frontend
sleep 5
echo -e "${GREEN}  [OK] React Frontend starting...${NC}"

# Streamlit
echo "[3/4] Starting Streamlit UI..."
docker-compose -f docker/docker-compose.yml --env-file .env up -d agent-ui
sleep 3
echo -e "${GREEN}  [OK] Streamlit UI starting...${NC}"

# Superset
if [ $NO_SUPERSET -eq 0 ]; then
    echo "[4/4] Starting Apache Superset..."
    docker-compose -f docker/docker-compose.yml --env-file .env --profile superset up -d superset
    echo -e "${GREEN}  [OK] Superset starting (may take 1-2 minutes)...${NC}"
else
    echo "[4/4] Skipping Superset (--no-superset flag)"
fi

echo ""

# =============================================================================
# PHASE 6: Verification
# =============================================================================
echo -e "${CYAN}============================================================${NC}"
echo -e "${CYAN} PHASE 6: Verifying deployment${NC}"
echo -e "${CYAN}============================================================${NC}"
echo ""

echo "Waiting for services to stabilize..."
sleep 10

echo ""
echo "Service Status:"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep -v "tools"
echo ""

# =============================================================================
# Complete
# =============================================================================
echo ""
echo -e "${GREEN}============================================================${NC}"
echo -e "${GREEN}  REBUILD AND DEPLOY COMPLETE!${NC}"
echo -e "${GREEN}============================================================${NC}"
echo ""
echo "  Database Services:"
echo "    - SQL Server 2022: localhost:1433 (ResearchAnalytics)"
echo "    - SQL Server 2025: localhost:1434 (LLM_BackEnd + Vectors)"
echo "    - Redis Stack:     localhost:\${REDIS_PORT:-6390}"
echo "    - RedisInsight:    http://localhost:\${REDIS_INSIGHT_PORT:-8008}"
echo ""
echo "  Application Services:"
echo "    - FastAPI Backend: http://localhost:\${API_PORT:-8200}"
echo "    - FastAPI Docs:    http://localhost:\${API_PORT:-8200}/docs"
echo "    - React Frontend:  http://localhost:5173"
echo "    - Streamlit UI:    http://localhost:8501"
if [ $NO_SUPERSET -eq 0 ]; then
    echo "    - Apache Superset: http://localhost:\${SUPERSET_PORT:-8288}"
fi
echo ""
echo "  Data Preservation:"
echo "    - Database data: PRESERVED (volumes not deleted)"
echo "    - Redis cache:   PRESERVED"
echo "    - Superset config: PRESERVED"
echo ""
echo "  Useful commands:"
echo "    View logs:    docker-compose -f docker/docker-compose.yml logs -f [service]"
echo "    Stop all:     docker-compose -f docker/docker-compose.yml --profile full down"
echo "    CLI access:   docker-compose -f docker/docker-compose.yml --profile cli run --rm agent-cli"
echo ""

# Open browser on Mac/Linux
if command -v xdg-open &> /dev/null; then
    read -p "Open React app in browser? (Y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Nn]$ ]]; then
        xdg-open http://localhost:5173
    fi
elif command -v open &> /dev/null; then
    read -p "Open React app in browser? (Y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Nn]$ ]]; then
        open http://localhost:5173
    fi
fi
