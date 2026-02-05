#Requires -Version 5.1
<#
.SYNOPSIS
    Fresh rebuild and deploy of ALL Docker services with data preservation.

.DESCRIPTION
    This script performs a complete rebuild and deployment:
    - Stops all running containers (gracefully)
    - Removes old container images (for fresh build)
    - Builds all images from scratch (no cache)
    - Starts all services in dependency order
    - Waits for health checks

    DATA PRESERVATION:
    - Database volumes are PRESERVED (SQL Server data, settings)
    - Redis data is PRESERVED
    - Superset configuration is PRESERVED
    - Only container images are rebuilt

.PARAMETER Quick
    Use cached layers for faster builds (default: fresh build with no cache)

.PARAMETER NoSuperset
    Skip Apache Superset service (faster startup)

.PARAMETER CleanData
    WARNING: Also removes all data volumes (destructive!)

.EXAMPLE
    .\rebuild-deploy.ps1
    Fresh rebuild and deploy all services

.EXAMPLE
    .\rebuild-deploy.ps1 -Quick
    Quick rebuild using cached layers

.EXAMPLE
    .\rebuild-deploy.ps1 -NoSuperset
    Deploy without Superset for faster startup

.EXAMPLE
    .\rebuild-deploy.ps1 -CleanData
    Complete reset including all data (DESTRUCTIVE)
#>

[CmdletBinding()]
param(
    [switch]$Quick,
    [switch]$NoSuperset,
    [switch]$CleanData
)

$ErrorActionPreference = "Stop"

# Colors for output
function Write-Step { param($msg) Write-Host "`n[$msg]" -ForegroundColor Cyan }
function Write-OK { param($msg) Write-Host "  [OK] $msg" -ForegroundColor Green }
function Write-Warn { param($msg) Write-Host "  [WARN] $msg" -ForegroundColor Yellow }
function Write-Err { param($msg) Write-Host "  [ERROR] $msg" -ForegroundColor Red }

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  Local LLM Research Agent - REBUILD AND DEPLOY" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Handle clean-data warning
if ($CleanData) {
    Write-Host ""
    Write-Host "  *** WARNING: -CleanData mode enabled ***" -ForegroundColor Red
    Write-Host "  This will DELETE ALL DATABASE DATA including:" -ForegroundColor Red
    Write-Host "    - SQL Server databases (ResearchAnalytics, LLM_BackEnd)" -ForegroundColor Red
    Write-Host "    - Redis cache data" -ForegroundColor Red
    Write-Host "    - Superset configuration" -ForegroundColor Red
    Write-Host ""
    $confirm = Read-Host "Are you sure? Type YES to continue"
    if ($confirm -ne "YES") {
        Write-Host "Aborted."
        exit 0
    }
}

# =============================================================================
# Prerequisites Check
# =============================================================================
Write-Step "PREREQ: Checking prerequisites"

# Check .env
if (-not (Test-Path ".env")) {
    Write-Err ".env file not found! Please copy .env.example to .env"
    exit 1
}
Write-OK ".env file found"

# Check Docker
try {
    docker info 2>&1 | Out-Null
    Write-OK "Docker is running"
} catch {
    Write-Err "Docker is not running! Please start Docker Desktop."
    exit 1
}

# Check Ollama
try {
    $null = Invoke-WebRequest -Uri "http://localhost:11434/api/tags" -TimeoutSec 5 -ErrorAction SilentlyContinue
    Write-OK "Ollama is running"
} catch {
    Write-Warn "Ollama is not running - agent features will not work"
}

# =============================================================================
# PHASE 1: Stop and Clean
# =============================================================================
Write-Step "PHASE 1: Stopping existing services"

Write-Host "[1/3] Stopping all containers gracefully..."
docker-compose -f docker/docker-compose.yml --env-file .env --profile full down 2>$null
docker-compose -f docker/docker-compose.yml --env-file .env down 2>$null
Write-OK "Containers stopped"

Write-Host "[2/3] Removing old container images..."
$images = @(
    "local-agent-ai-stack-agent-ui",
    "local-agent-ai-stack-agent-cli",
    "local-agent-ai-stack-api",
    "local-agent-ai-stack-frontend",
    "local-agent-ai-stack-superset"
)
foreach ($img in $images) {
    docker rmi $img 2>$null | Out-Null
}
Write-OK "Old images removed"

Write-Host "[3/3] Cleaning up dangling images..."
docker image prune -f 2>$null | Out-Null
Write-OK "Cleanup complete"

if ($CleanData) {
    Write-Host ""
    Write-Host "[CLEAN-DATA] Removing data volumes..." -ForegroundColor Yellow
    docker volume rm local-llm-mssql-data 2>$null | Out-Null
    docker volume rm local-llm-backend-data 2>$null | Out-Null
    docker volume rm local-llm-redis-data 2>$null | Out-Null
    docker volume rm local-llm-superset-data 2>$null | Out-Null
    Write-OK "Data volumes removed"
}

# =============================================================================
# PHASE 2: Ensure Volumes
# =============================================================================
Write-Step "PHASE 2: Ensuring data volumes exist"

Write-Host "Creating/verifying Docker volumes (data preserved if exists)..."
docker volume create local-llm-mssql-data 2>$null | Out-Null
docker volume create local-llm-backend-data 2>$null | Out-Null
docker volume create local-llm-redis-data 2>$null | Out-Null
docker volume create local-llm-superset-data 2>$null | Out-Null

Write-OK "local-llm-mssql-data (SQL Server 2022)"
Write-OK "local-llm-backend-data (SQL Server 2025)"
Write-OK "local-llm-redis-data (Redis)"
Write-OK "local-llm-superset-data (Superset)"

# =============================================================================
# PHASE 3: Build Images
# =============================================================================
Write-Step "PHASE 3: Building all Docker images"

if ($Quick) {
    Write-Host "  Mode: QUICK BUILD (using cached layers)" -ForegroundColor Yellow
    docker-compose -f docker/docker-compose.yml --env-file .env --profile full build
} else {
    Write-Host "  Mode: FRESH BUILD (no cache - this will take several minutes)" -ForegroundColor Yellow
    docker-compose -f docker/docker-compose.yml --env-file .env --profile full build --no-cache
}

if ($LASTEXITCODE -ne 0) {
    Write-Err "Docker build failed!"
    exit 1
}
Write-OK "Build complete"

# =============================================================================
# PHASE 4: Start Databases
# =============================================================================
Write-Step "PHASE 4: Starting database services"

# SQL Server 2022
Write-Host "[1/4] Starting SQL Server 2022 (Sample Database)..."
docker-compose -f docker/docker-compose.yml --env-file .env up -d mssql

Write-Host "Waiting for SQL Server 2022 to be healthy..."
do {
    Start-Sleep -Seconds 5
    $health = docker inspect --format="{{.State.Health.Status}}" local-agent-mssql 2>$null
    if ($health -ne "healthy") {
        Write-Host "  Still waiting for SQL Server 2022..."
    }
} while ($health -ne "healthy")
Write-OK "SQL Server 2022 is healthy"

# SQL Server 2025
Write-Host "[2/4] Starting SQL Server 2025 (Backend Database)..."
docker-compose -f docker/docker-compose.yml --env-file .env up -d mssql-backend

Write-Host "Waiting for SQL Server 2025 to be healthy..."
do {
    Start-Sleep -Seconds 5
    $health = docker inspect --format="{{.State.Health.Status}}" local-agent-mssql-backend 2>$null
    if ($health -ne "healthy") {
        Write-Host "  Still waiting for SQL Server 2025..."
    }
} while ($health -ne "healthy")
Write-OK "SQL Server 2025 is healthy"

# Redis
Write-Host "[3/4] Starting Redis Stack..."
docker-compose -f docker/docker-compose.yml --env-file .env up -d redis-stack

Write-Host "Waiting for Redis to be healthy..."
do {
    Start-Sleep -Seconds 3
    $health = docker inspect --format="{{.State.Health.Status}}" local-agent-redis 2>$null
    if ($health -ne "healthy") {
        Write-Host "  Still waiting for Redis..."
    }
} while ($health -ne "healthy")
Write-OK "Redis Stack is healthy"

# Database init
Write-Host "[4/4] Running database initialization (if needed)..."
docker-compose -f docker/docker-compose.yml --env-file .env --profile init up mssql-tools 2>$null
docker-compose -f docker/docker-compose.yml --env-file .env --profile init up mssql-backend-tools 2>$null
Write-OK "Database initialization complete"

# =============================================================================
# PHASE 5: Start Application Services
# =============================================================================
Write-Step "PHASE 5: Starting application services"

# FastAPI
Write-Host "[1/4] Starting FastAPI Backend..."
docker-compose -f docker/docker-compose.yml --env-file .env --profile api up -d api

Write-Host "Waiting for FastAPI to be ready..."
do {
    Start-Sleep -Seconds 5
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8000/api/health" -TimeoutSec 5 -ErrorAction SilentlyContinue
        $apiReady = $true
    } catch {
        Write-Host "  Still waiting for FastAPI..."
        $apiReady = $false
    }
} while (-not $apiReady)
Write-OK "FastAPI is ready"

# React Frontend
Write-Host "[2/4] Starting React Frontend..."
docker-compose -f docker/docker-compose.yml --env-file .env --profile frontend up -d frontend
Start-Sleep -Seconds 5
Write-OK "React Frontend starting"

# Streamlit
Write-Host "[3/4] Starting Streamlit UI..."
docker-compose -f docker/docker-compose.yml --env-file .env up -d agent-ui
Start-Sleep -Seconds 3
Write-OK "Streamlit UI starting"

# Superset
if (-not $NoSuperset) {
    Write-Host "[4/4] Starting Apache Superset..."
    docker-compose -f docker/docker-compose.yml --env-file .env --profile superset up -d superset
    Write-OK "Superset starting (may take 1-2 minutes)"
} else {
    Write-Host "[4/4] Skipping Superset (-NoSuperset flag)"
}

# =============================================================================
# PHASE 6: Verification
# =============================================================================
Write-Step "PHASE 6: Verifying deployment"

Write-Host "Waiting for services to stabilize..."
Start-Sleep -Seconds 10

Write-Host ""
Write-Host "Service Status:" -ForegroundColor Cyan
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | Where-Object { $_ -notmatch "tools" }

# =============================================================================
# Complete
# =============================================================================
Write-Host ""
Write-Host "============================================================" -ForegroundColor Green
Write-Host "  REBUILD AND DEPLOY COMPLETE!" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Write-Host ""
Write-Host "  Database Services:" -ForegroundColor White
Write-Host "    - SQL Server 2022: localhost:1433 (ResearchAnalytics)"
Write-Host "    - SQL Server 2025: localhost:1434 (LLM_BackEnd + Vectors)"
Write-Host "    - Redis Stack:     localhost:`$env:REDIS_PORT (default: 6390)"
Write-Host "    - RedisInsight:    http://localhost:`$env:REDIS_INSIGHT_PORT (default: 8008)"
Write-Host ""
Write-Host "  Application Services:" -ForegroundColor White
Write-Host "    - FastAPI Backend: http://localhost:`$env:API_PORT (default: 8200)"
Write-Host "    - FastAPI Docs:    http://localhost:`$env:API_PORT/docs"
Write-Host "    - React Frontend:  http://localhost:5173"
Write-Host "    - Streamlit UI:    http://localhost:8501"
if (-not $NoSuperset) {
    Write-Host "    - Apache Superset: http://localhost:`$env:SUPERSET_PORT (default: 8288)"
}
Write-Host ""
Write-Host "  Data Preservation:" -ForegroundColor White
Write-Host "    - Database data: PRESERVED (volumes not deleted)"
Write-Host "    - Redis cache:   PRESERVED"
Write-Host "    - Superset config: PRESERVED"
Write-Host ""
Write-Host "  Useful commands:" -ForegroundColor White
Write-Host "    View logs:    docker-compose -f docker/docker-compose.yml logs -f [service]"
Write-Host "    Stop all:     docker-compose -f docker/docker-compose.yml --profile full down"
Write-Host "    CLI access:   docker-compose -f docker/docker-compose.yml --profile cli run --rm agent-cli"
Write-Host ""

$openBrowser = Read-Host "Open React app in browser? (Y/n)"
if ($openBrowser -ne "n") {
    Start-Process "http://localhost:5173"
}
