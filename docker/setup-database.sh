#!/bin/bash
# =============================================================================
# setup-database.sh
# Complete database setup for Local LLM Research Agent
# Sets up both SQL Server 2022 (Sample) and SQL Server 2025 (Backend)
# =============================================================================

set -e

echo ""
echo "============================================================"
echo "  Local LLM Research Agent - Complete Database Setup"
echo "============================================================"
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "[ERROR] Docker is not running. Please start Docker and try again."
    exit 1
fi

# Navigate to docker directory
cd "$(dirname "$0")"

# Check for .env file in parent directory
if [ ! -f "../.env" ]; then
    echo "[WARNING] No .env file found in project root."
    echo "Using default configuration from docker-compose.yml"
    echo "For custom settings, copy .env.example to .env in project root."
    echo ""
fi

echo "============================================================"
echo " PHASE 1: SQL Server 2022 - Sample Database (ResearchAnalytics)"
echo "============================================================"
echo ""

echo "[Step 1/3] Starting SQL Server 2022 container..."
docker compose --env-file ../.env up -d mssql
if [ $? -ne 0 ]; then
    echo "[ERROR] Failed to start SQL Server 2022 container."
    exit 1
fi

echo ""
echo "[Step 2/3] Waiting for SQL Server 2022 to be healthy..."
while [ "$(docker inspect --format='{{.State.Health.Status}}' local-agent-mssql 2>/dev/null)" != "healthy" ]; do
    echo "  Still waiting for SQL Server 2022..."
    sleep 5
done
echo "  SQL Server 2022 is healthy!"

echo ""
echo "[Step 3/3] Running ResearchAnalytics initialization scripts..."
docker compose --env-file ../.env --profile init up mssql-tools
if [ $? -ne 0 ]; then
    echo "[ERROR] Failed to run sample database initialization scripts."
    exit 1
fi

echo ""
echo "============================================================"
echo " PHASE 2: SQL Server 2025 - Backend Database (LLM_BackEnd)"
echo "============================================================"
echo ""

echo "[Step 1/3] Starting SQL Server 2025 container..."
docker compose --env-file ../.env up -d mssql-backend
if [ $? -ne 0 ]; then
    echo "[ERROR] Failed to start SQL Server 2025 container."
    exit 1
fi

echo ""
echo "[Step 2/3] Waiting for SQL Server 2025 to be healthy..."
while [ "$(docker inspect --format='{{.State.Health.Status}}' local-agent-mssql-backend 2>/dev/null)" != "healthy" ]; do
    echo "  Still waiting for SQL Server 2025..."
    sleep 5
done
echo "  SQL Server 2025 is healthy!"

echo ""
echo "[Step 3/3] Running LLM_BackEnd initialization scripts..."
echo "  (includes app schema, vectors schema, and hybrid search setup)"
docker compose --env-file ../.env --profile init up mssql-backend-tools
if [ $? -ne 0 ]; then
    echo "[ERROR] Failed to run backend database initialization scripts."
    exit 1
fi

echo ""
echo "============================================================"
echo " PHASE 3: Redis Stack"
echo "============================================================"
echo ""

echo "Starting Redis Stack for caching and optional vector fallback..."
docker compose --env-file ../.env up -d redis-stack
if [ $? -ne 0 ]; then
    echo "[ERROR] Failed to start Redis Stack container."
    exit 1
fi

echo "Waiting for Redis to be healthy..."
while [ "$(docker inspect --format='{{.State.Health.Status}}' local-agent-redis 2>/dev/null)" != "healthy" ]; do
    echo "  Still waiting for Redis..."
    sleep 3
done
echo "  Redis Stack is healthy!"

echo ""
echo "============================================================"
echo "  Database Setup Complete!"
echo "============================================================"
echo ""
echo "  SQL Server 2022 (Sample Database):"
echo "    Server:   localhost,1433"
echo "    Database: ResearchAnalytics"
echo "    User:     sa"
echo "    Password: (see MSSQL_SA_PASSWORD in .env)"
echo ""
echo "  SQL Server 2025 (Backend Database):"
echo "    Server:   localhost,1434"
echo "    Database: LLM_BackEnd"
echo "    User:     sa"
echo "    Password: (see MSSQL_SA_PASSWORD in .env)"
echo "    Features: Native VECTOR type, Full-Text Search, Hybrid Search"
echo ""
echo "  Redis Stack:"
echo "    Server:   localhost:6379"
echo "    GUI:      http://localhost:8001 (RedisInsight)"
echo ""
echo "  Backend Features Initialized:"
echo "    - app schema (conversations, messages, dashboards, settings)"
echo "    - vectors schema (document embeddings with native VECTOR type)"
echo "    - Hybrid Search (full-text + vector combined with RRF)"
echo ""
echo "  To test connections:"
echo "    sqlcmd -S localhost,1433 -U sa -P 'LocalLLM@2024!' -d ResearchAnalytics -Q 'SELECT 1'"
echo "    sqlcmd -S localhost,1434 -U sa -P 'LocalLLM@2024!' -d LLM_BackEnd -Q 'SELECT 1'"
echo ""
echo "  To stop all databases:"
echo "    docker compose --env-file ../.env down"
echo ""
echo "  To stop and remove all data (DESTRUCTIVE):"
echo "    docker compose --env-file ../.env down -v"
echo ""
