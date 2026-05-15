#!/bin/bash
# =============================================================================
# deploy-full.sh
# Full-stack deployment for Local LLM Research Agent
#
# Deploys ALL services in the correct order:
#   1. Pre-flight checks (Docker, Ollama, port conflicts)
#   2. Build all container images
#   3. Start databases (SQL Server 2022, 2025, Redis)
#   4. Initialize databases (first run only)
#   5. Start application services (API, Streamlit, React, Superset)
#   6. Print connection info
#
# Usage:
#   ./docker/deploy-full.sh              # Full deploy
#   ./docker/deploy-full.sh --no-init    # Skip DB init (already initialized)
#   ./docker/deploy-full.sh --no-superset # Skip Superset
#   ./docker/deploy-full.sh --build-only # Build images only, don't start
# =============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
COMPOSE_FILE="$SCRIPT_DIR/docker-compose.yml"
ENV_FILE="$PROJECT_ROOT/.env"
COMPOSE_CMD="docker compose -f $COMPOSE_FILE --env-file $ENV_FILE"

# ---------------------------------------------------------------------------
# Parse arguments
# ---------------------------------------------------------------------------
SKIP_INIT=false
SKIP_SUPERSET=false
BUILD_ONLY=false

for arg in "$@"; do
    case $arg in
        --no-init)      SKIP_INIT=true ;;
        --no-superset)  SKIP_SUPERSET=true ;;
        --build-only)   BUILD_ONLY=true ;;
        --help|-h)
            echo "Usage: ./docker/deploy-full.sh [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --no-init       Skip database initialization (if already done)"
            echo "  --no-superset   Skip Apache Superset service"
            echo "  --build-only    Build images only, don't start services"
            echo "  --help, -h      Show this help"
            exit 0
            ;;
        *)
            echo "[ERROR] Unknown argument: $arg"
            echo "Run with --help for usage."
            exit 1
            ;;
    esac
done

# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

wait_healthy() {
    local container=$1
    local label=$2
    local timeout=${3:-120}
    local elapsed=0

    echo -n "  Waiting for $label..."
    while [ "$elapsed" -lt "$timeout" ]; do
        local status
        status=$(docker inspect --format='{{.State.Health.Status}}' "$container" 2>/dev/null || echo "not_found")
        if [ "$status" = "healthy" ]; then
            echo " ready! (${elapsed}s)"
            return 0
        elif [ "$status" = "not_found" ]; then
            echo " container not found!"
            return 1
        fi
        sleep 3
        elapsed=$((elapsed + 3))
        echo -n "."
    done
    echo " TIMEOUT after ${timeout}s (status: $status)"
    return 1
}

# Load .env for port display
load_env_ports() {
    if [ -f "$ENV_FILE" ]; then
        eval "$(grep -E '^(MSSQL_PORT|BACKEND_DB_PORT|API_PORT|STREAMLIT_PORT|FRONTEND_PORT|REDIS_PORT|REDIS_INSIGHT_PORT|SUPERSET_PORT)=' "$ENV_FILE" 2>/dev/null)" || true
    fi
    MSSQL_PORT="${MSSQL_PORT:-1433}"
    BACKEND_DB_PORT="${BACKEND_DB_PORT:-1434}"
    API_PORT="${API_PORT:-8000}"
    STREAMLIT_PORT="${STREAMLIT_PORT:-8501}"
    FRONTEND_PORT="${FRONTEND_PORT:-5173}"
    REDIS_PORT="${REDIS_PORT:-6379}"
    REDIS_INSIGHT_PORT="${REDIS_INSIGHT_PORT:-8001}"
    SUPERSET_PORT="${SUPERSET_PORT:-8088}"
}

# ---------------------------------------------------------------------------
# PHASE 0: Pre-flight checks
# ---------------------------------------------------------------------------
echo ""
echo "============================================================"
echo "  Local LLM Research Agent - Full Stack Deployment"
echo "============================================================"
echo ""

# Check Docker
echo "[Phase 0] Pre-flight checks..."
echo ""
if ! docker info > /dev/null 2>&1; then
    echo "  [FAIL] Docker is not running. Please start Docker and try again."
    exit 1
fi
echo "  [OK] Docker is running"

# Check .env
if [ ! -f "$ENV_FILE" ]; then
    echo "  [WARN] No .env file found at $ENV_FILE"
    echo "         Creating from .env.example..."
    if [ -f "$PROJECT_ROOT/.env.example" ]; then
        cp "$PROJECT_ROOT/.env.example" "$ENV_FILE"
        echo "  [OK] Created .env from .env.example (edit with your settings)"
    else
        echo "  [FAIL] No .env.example found either. Cannot continue."
        exit 1
    fi
else
    echo "  [OK] .env file found"
fi

# Check Ollama
if curl -sf http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "  [OK] Ollama is running on host"
else
    echo "  [WARN] Ollama not detected at localhost:11434"
    echo "         LLM features will not work until Ollama is started."
    echo "         Run: ollama serve"
fi

# Port conflict check
echo ""
echo "[Phase 0.5] Port conflict check..."
echo ""
if [ -x "$SCRIPT_DIR/check-ports.sh" ] || chmod +x "$SCRIPT_DIR/check-ports.sh" 2>/dev/null; then
    if ! "$SCRIPT_DIR/check-ports.sh"; then
        echo ""
        echo "  Port conflicts detected! Options:"
        echo "    1. Auto-fix:  ./docker/check-ports.sh --fix"
        echo "    2. Manual:    Edit .env port variables"
        echo "    3. Continue:  Conflicts may cause startup failures"
        echo ""
        read -p "  Continue anyway? (y/N): " confirm
        if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
            echo "  Aborted. Resolve port conflicts first."
            exit 1
        fi
    fi
fi

# ---------------------------------------------------------------------------
# PHASE 1: Build images
# ---------------------------------------------------------------------------
echo ""
echo "============================================================"
echo "[Phase 1] Building container images..."
echo "============================================================"
echo ""

# Build all images that have custom Dockerfiles
echo "  Building Streamlit UI image (Dockerfile)..."
$COMPOSE_CMD build agent-ui

echo ""
echo "  Building FastAPI API image (Dockerfile.api)..."
$COMPOSE_CMD build api

echo ""
echo "  Building React Frontend image (Dockerfile.frontend)..."
$COMPOSE_CMD build frontend

if [ "$SKIP_SUPERSET" = "false" ]; then
    echo ""
    echo "  Building Superset image (Dockerfile.superset)..."
    $COMPOSE_CMD build superset
fi

echo ""
echo "  [OK] All images built successfully"

if [ "$BUILD_ONLY" = "true" ]; then
    echo ""
    echo "  --build-only flag set. Images built. Exiting."
    exit 0
fi

# ---------------------------------------------------------------------------
# PHASE 2: Start database services
# ---------------------------------------------------------------------------
echo ""
echo "============================================================"
echo "[Phase 2] Starting database services..."
echo "============================================================"
echo ""

echo "  Starting SQL Server 2022 (sample data)..."
$COMPOSE_CMD up -d mssql

echo "  Starting SQL Server 2025 (backend + vectors)..."
$COMPOSE_CMD up -d mssql-backend

echo "  Starting Redis Stack..."
$COMPOSE_CMD up -d redis-stack

echo ""
echo "  Waiting for databases to be healthy..."
wait_healthy "local-agent-mssql" "SQL Server 2022" 120
wait_healthy "local-agent-mssql-backend" "SQL Server 2025" 120
wait_healthy "local-agent-redis" "Redis Stack" 60

echo ""
echo "  [OK] All databases are healthy"

# ---------------------------------------------------------------------------
# PHASE 3: Initialize databases (first run)
# ---------------------------------------------------------------------------
if [ "$SKIP_INIT" = "false" ]; then
    echo ""
    echo "============================================================"
    echo "[Phase 3] Initializing databases (safe to re-run)..."
    echo "============================================================"
    echo ""

    echo "  Running ResearchAnalytics init scripts (SQL Server 2022)..."
    $COMPOSE_CMD --profile init up mssql-tools
    echo ""

    echo "  Running LLM_BackEnd init scripts (SQL Server 2025)..."
    $COMPOSE_CMD --profile init up mssql-backend-tools
    echo ""

    echo "  [OK] Database initialization complete"
else
    echo ""
    echo "[Phase 3] Skipped database initialization (--no-init)"
fi

# ---------------------------------------------------------------------------
# PHASE 4: Start application services
# ---------------------------------------------------------------------------
echo ""
echo "============================================================"
echo "[Phase 4] Starting application services..."
echo "============================================================"
echo ""

if [ "$SKIP_SUPERSET" = "false" ]; then
    echo "  Starting full stack (API + Streamlit + React + Superset)..."
    $COMPOSE_CMD --profile full up -d
else
    echo "  Starting stack without Superset (API + Streamlit + React)..."
    $COMPOSE_CMD --profile frontend up -d
    # Also start Streamlit (it's in the default profile, not frontend)
    $COMPOSE_CMD up -d agent-ui
fi

echo ""
echo "  Waiting for application services..."

# Wait for API first (other services may depend on it)
echo -n "  Waiting for FastAPI..."
for i in $(seq 1 40); do
    if curl -sf "http://localhost:${API_PORT:-8000}/api/health/live" > /dev/null 2>&1; then
        echo " ready! ($((i * 3))s)"
        break
    fi
    if [ "$i" -eq 40 ]; then
        echo " still starting (check logs: docker logs local-agent-api)"
    fi
    sleep 3
    echo -n "."
done

# Check Streamlit
echo -n "  Waiting for Streamlit..."
for i in $(seq 1 20); do
    if curl -sf "http://localhost:${STREAMLIT_PORT:-8501}/_stcore/health" > /dev/null 2>&1; then
        echo " ready! ($((i * 3))s)"
        break
    fi
    if [ "$i" -eq 20 ]; then
        echo " still starting (check logs: docker logs local-agent-streamlit-ui)"
    fi
    sleep 3
    echo -n "."
done

echo ""
echo "  [OK] Application services started"

# ---------------------------------------------------------------------------
# PHASE 5: Summary
# ---------------------------------------------------------------------------
load_env_ports

echo ""
echo "============================================================"
echo "  Deployment Complete!"
echo "============================================================"
echo ""
echo "  Web Interfaces:"
echo "    React Frontend:  http://localhost:$FRONTEND_PORT"
echo "    FastAPI Docs:    http://localhost:$API_PORT/docs"
echo "    API Health:      http://localhost:$API_PORT/api/health"
echo "    Streamlit UI:    http://localhost:$STREAMLIT_PORT"
if [ "$SKIP_SUPERSET" = "false" ]; then
echo "    Superset BI:     http://localhost:$SUPERSET_PORT"
fi
echo "    RedisInsight:    http://localhost:$REDIS_INSIGHT_PORT"
echo ""
echo "  Databases:"
echo "    SQL Server 2022: localhost,$MSSQL_PORT  (ResearchAnalytics)"
echo "    SQL Server 2025: localhost,$BACKEND_DB_PORT  (LLM_BackEnd)"
echo "    Redis Stack:     localhost:$REDIS_PORT"
echo ""
echo "  Useful Commands:"
echo "    View logs:       docker compose -f docker/docker-compose.yml logs -f [service]"
echo "    Stop all:        docker compose -f docker/docker-compose.yml down"
echo "    Restart service: docker compose -f docker/docker-compose.yml restart [service]"
echo "    Run CLI:         docker compose -f docker/docker-compose.yml --profile cli run --rm agent-cli"
echo ""
echo "  Container Status:"
docker ps --filter "name=local-agent-" --format "    {{.Names}}\t{{.Status}}" 2>/dev/null || true
echo ""
