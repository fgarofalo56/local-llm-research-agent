#!/bin/bash
# =============================================================================
# setup-database.sh
# Helper script to set up SQL Server Docker container and initialize database
# =============================================================================

set -e

echo ""
echo "============================================"
echo " Local LLM Research Agent - Database Setup"
echo "============================================"
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "ERROR: Docker is not running. Please start Docker and try again."
    exit 1
fi

# Navigate to docker directory
cd "$(dirname "$0")"

echo "Step 1: Starting SQL Server container..."
docker compose up -d mssql
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to start SQL Server container."
    exit 1
fi

echo ""
echo "Step 2: Waiting for SQL Server to be healthy..."
while [ "$(docker inspect --format='{{.State.Health.Status}}' local-llm-mssql 2>/dev/null)" != "healthy" ]; do
    echo "  Still waiting..."
    sleep 5
done
echo "  SQL Server is healthy!"

echo ""
echo "Step 3: Running database initialization scripts..."
docker compose --profile init up mssql-tools
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to run initialization scripts."
    exit 1
fi

echo ""
echo "============================================"
echo " Database Setup Complete!"
echo "============================================"
echo ""
echo "Connection Details:"
echo "  Server:   localhost,1433"
echo "  Database: ResearchAnalytics"
echo "  User:     sa"
echo "  Password: LocalLLM@2024! (or your MSSQL_SA_PASSWORD)"
echo ""
echo "To connect with sqlcmd:"
echo "  sqlcmd -S localhost,1433 -U sa -P 'LocalLLM@2024!' -d ResearchAnalytics"
echo ""
echo "To stop the database:"
echo "  docker compose down"
echo ""
echo "To stop and remove data:"
echo "  docker compose down -v"
echo ""
