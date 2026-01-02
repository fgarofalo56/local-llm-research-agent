# Docker Compose Production Deployment

> **Production-ready deployment guide using Docker Compose**

---

## Table of Contents

- [Overview](#overview)
- [Production Architecture](#production-architecture)
- [Environment Configuration](#environment-configuration)
- [Volume Management](#volume-management)
- [Network Configuration](#network-configuration)
- [Service Configuration](#service-configuration)
- [Deployment Process](#deployment-process)
- [Scaling and Performance](#scaling-and-performance)
- [Backup and Restore](#backup-and-restore)
- [Troubleshooting](#troubleshooting)

---

## Overview

Docker Compose provides a production-ready deployment solution for small to medium-scale deployments. This guide covers production-specific configurations and best practices.

### When to Use Docker Compose

**Ideal For:**
- Single-server deployments
- Small to medium teams (1-100 users)
- Development and staging environments
- Quick production deployments
- Cost-effective hosting

**Not Ideal For:**
- Multi-node high availability
- Massive scale (1000+ concurrent users)
- Complex load balancing requirements
- Geographic distribution

---

## Production Architecture

### Service Stack

```yaml
services:
  # Data Layer
  mssql:               # SQL Server 2022 - Sample database
  mssql-backend:       # SQL Server 2025 - Backend + vectors
  redis-stack:         # Redis - Caching + vector fallback

  # Application Layer
  api:                 # FastAPI backend
  frontend:            # React frontend (production build)

  # Optional Services
  agent-ui:            # Streamlit UI (alternative interface)
  superset:            # Apache Superset BI
```

### Network Topology

```
External (Internet/Users)
         │
         ▼
    [Reverse Proxy] (nginx/traefik - optional)
         │
         ├─────────────┬──────────────┬──────────────┐
         ▼             ▼              ▼              ▼
    [Frontend]    [API:8000]   [Streamlit]   [Superset]
         │             │              │              │
         └─────────────┴──────────────┴──────────────┘
                       │
              [llm-network (bridge)]
                       │
         ┌─────────────┴──────────────┬──────────────┐
         ▼             ▼              ▼              ▼
    [mssql:1433] [mssql-backend] [redis:6379]  [host.docker.internal]
                  [1434]                        (Ollama on host)
```

---

## Environment Configuration

### Production .env File

Create a production-specific `.env.production` file:

```bash
# ==========================================
# PRODUCTION CONFIGURATION
# ==========================================
# CRITICAL: Keep this file secure and never commit to version control

# ------------------------------------------
# Security Settings
# ------------------------------------------
# Generate strong passwords: openssl rand -base64 32
MSSQL_SA_PASSWORD=<GENERATE_STRONG_PASSWORD>
SUPERSET_SECRET_KEY=<GENERATE_SECRET_KEY>
SUPERSET_ADMIN_PASSWORD=<GENERATE_STRONG_PASSWORD>

# ------------------------------------------
# LLM Provider
# ------------------------------------------
LLM_PROVIDER=ollama
OLLAMA_HOST=http://host.docker.internal:11434
OLLAMA_MODEL=qwen2.5:7b-instruct
EMBEDDING_MODEL=nomic-embed-text

# ------------------------------------------
# SQL Server 2022 - Sample Database
# ------------------------------------------
SQL_SERVER_HOST=mssql
SQL_SERVER_PORT=1433
SQL_DATABASE_NAME=ResearchAnalytics
SQL_USERNAME=sa
SQL_PASSWORD=${MSSQL_SA_PASSWORD}
SQL_TRUST_SERVER_CERTIFICATE=true

# ------------------------------------------
# SQL Server 2025 - Backend Database
# ------------------------------------------
BACKEND_DB_HOST=mssql-backend
BACKEND_DB_PORT=1433
BACKEND_DB_NAME=LLM_BackEnd
BACKEND_DB_USERNAME=sa
BACKEND_DB_PASSWORD=${MSSQL_SA_PASSWORD}
BACKEND_DB_TRUST_CERT=true

# ------------------------------------------
# Vector Store
# ------------------------------------------
VECTOR_STORE_TYPE=mssql
VECTOR_DIMENSIONS=768

# ------------------------------------------
# Redis Configuration
# ------------------------------------------
REDIS_URL=redis://redis-stack:6379
REDIS_PORT=6379
REDIS_INSIGHT_PORT=8001

# ------------------------------------------
# Application Settings
# ------------------------------------------
API_HOST=0.0.0.0
API_PORT=8000
STREAMLIT_PORT=8501
FRONTEND_PORT=5173

# Production mode
DEBUG=false
LOG_LEVEL=INFO

# ------------------------------------------
# RAG Pipeline
# ------------------------------------------
CHUNK_SIZE=500
CHUNK_OVERLAP=50
RAG_TOP_K=5
MAX_UPLOAD_SIZE_MB=100
UPLOAD_DIR=/app/data/uploads

# ------------------------------------------
# MCP Configuration
# ------------------------------------------
MCP_MSSQL_PATH=python-mcp
MCP_MSSQL_READONLY=false
MCP_CONFIG_PATH=/app/mcp_config.json

# ------------------------------------------
# Volume Configuration
# ------------------------------------------
MSSQL_VOLUME_NAME=prod-llm-mssql-data
BACKEND_VOLUME_NAME=prod-llm-backend-data
REDIS_VOLUME_NAME=prod-llm-redis-data
SUPERSET_VOLUME_NAME=prod-llm-superset-data

# ------------------------------------------
# Performance Tuning
# ------------------------------------------
CACHE_ENABLED=true
CACHE_MAX_SIZE=1000
CACHE_TTL_SECONDS=3600
RATE_LIMIT_ENABLED=true
RATE_LIMIT_RPM=100
RATE_LIMIT_BURST=20
```

### Generate Secrets

```bash
# Generate SQL Server password
openssl rand -base64 32

# Generate Superset secret key
openssl rand -base64 42

# Generate secure tokens
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

---

## Volume Management

### Volume Configuration

Production volumes should be explicitly named and backed up:

```yaml
volumes:
  mssql_data:
    name: ${MSSQL_VOLUME_NAME:-prod-llm-mssql-data}
    driver: local
    driver_opts:
      type: none
      o: bind
      device: /data/mssql

  backend_data:
    name: ${BACKEND_VOLUME_NAME:-prod-llm-backend-data}
    driver: local
    driver_opts:
      type: none
      o: bind
      device: /data/backend

  redis_data:
    name: ${REDIS_VOLUME_NAME:-prod-llm-redis-data}
    driver: local
    driver_opts:
      type: none
      o: bind
      device: /data/redis

  superset_home:
    name: ${SUPERSET_VOLUME_NAME:-prod-llm-superset-data}
    driver: local
    driver_opts:
      type: none
      o: bind
      device: /data/superset
```

### Volume Directory Setup

```bash
# Create volume directories
sudo mkdir -p /data/mssql
sudo mkdir -p /data/backend
sudo mkdir -p /data/redis
sudo mkdir -p /data/superset

# Set ownership (adjust user/group as needed)
sudo chown -R 10001:10001 /data/mssql
sudo chown -R 10001:10001 /data/backend
sudo chown -R 999:999 /data/redis

# Set permissions
sudo chmod -R 755 /data
```

### Backup Strategy

```bash
# Backup SQL Server databases
docker exec local-agent-mssql /opt/mssql-tools18/bin/sqlcmd \
  -S localhost -U sa -P "$MSSQL_SA_PASSWORD" -C \
  -Q "BACKUP DATABASE ResearchAnalytics TO DISK='/var/opt/mssql/backup/ResearchAnalytics.bak'"

docker exec local-agent-mssql-backend /opt/mssql-tools18/bin/sqlcmd \
  -S localhost -U sa -P "$MSSQL_SA_PASSWORD" -C \
  -Q "BACKUP DATABASE LLM_BackEnd TO DISK='/var/opt/mssql/backup/LLM_BackEnd.bak'"

# Backup Redis
docker exec local-agent-redis redis-cli SAVE

# Copy backups to safe location
docker cp local-agent-mssql:/var/opt/mssql/backup/ResearchAnalytics.bak ./backups/
docker cp local-agent-mssql-backend:/var/opt/mssql/backup/LLM_BackEnd.bak ./backups/
docker cp local-agent-redis:/data/dump.rdb ./backups/redis-$(date +%Y%m%d).rdb
```

---

## Network Configuration

### Custom Network

```yaml
networks:
  llm-network:
    name: local-agent-network
    driver: bridge
    ipam:
      config:
        - subnet: 172.28.0.0/16
          gateway: 172.28.0.1
```

### Service Network Aliases

```yaml
services:
  api:
    networks:
      llm-network:
        aliases:
          - api.local
          - backend.local
```

### DNS Configuration

Add to `/etc/hosts` (or Windows equivalent):

```
127.0.0.1 api.local
127.0.0.1 mssql.local
127.0.0.1 redis.local
```

---

## Service Configuration

### FastAPI Backend (Production)

```yaml
api:
  build:
    context: ..
    dockerfile: docker/Dockerfile.api
  container_name: local-agent-api
  restart: unless-stopped

  # Resource limits
  deploy:
    resources:
      limits:
        cpus: '2'
        memory: 4G
      reservations:
        cpus: '1'
        memory: 2G

  # Health checks
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:8000/api/health/live"]
    interval: 30s
    timeout: 10s
    retries: 3
    start_period: 40s

  # Logging
  logging:
    driver: json-file
    options:
      max-size: "10m"
      max-file: "3"

  # Production environment
  environment:
    DEBUG: "false"
    LOG_LEVEL: "INFO"
    # ... other env vars
```

### SQL Server (Production)

```yaml
mssql:
  image: mcr.microsoft.com/mssql/server:2022-latest
  container_name: local-agent-mssql
  restart: unless-stopped

  # Resource limits
  deploy:
    resources:
      limits:
        cpus: '4'
        memory: 8G
      reservations:
        cpus: '2'
        memory: 4G

  # Security
  security_opt:
    - seccomp:unconfined

  # Logging
  logging:
    driver: json-file
    options:
      max-size: "50m"
      max-file: "5"
```

### Redis Stack (Production)

```yaml
redis-stack:
  image: redis/redis-stack:latest
  container_name: local-agent-redis
  restart: unless-stopped

  # Resource limits
  deploy:
    resources:
      limits:
        cpus: '2'
        memory: 4G
      reservations:
        cpus: '1'
        memory: 2G

  # Redis configuration
  command: >
    redis-server
    --save 60 1000
    --appendonly yes
    --appendfsync everysec
    --maxmemory 2gb
    --maxmemory-policy allkeys-lru

  # Logging
  logging:
    driver: json-file
    options:
      max-size: "10m"
      max-file: "3"
```

---

## Deployment Process

### Initial Deployment

```bash
# 1. Create production environment file
cp .env.example .env.production
# Edit .env.production with production values

# 2. Create volume directories
sudo mkdir -p /data/{mssql,backend,redis,superset}
sudo chown -R $(id -u):$(id -g) /data

# 3. Pull images
docker-compose -f docker/docker-compose.yml --env-file .env.production pull

# 4. Start infrastructure services first
docker-compose -f docker/docker-compose.yml --env-file .env.production up -d mssql mssql-backend redis-stack

# 5. Wait for databases to be healthy
docker-compose -f docker/docker-compose.yml ps

# 6. Initialize databases
docker-compose -f docker/docker-compose.yml --env-file .env.production --profile init up mssql-tools
docker-compose -f docker/docker-compose.yml --env-file .env.production --profile init up mssql-backend-tools

# 7. Start application services
docker-compose -f docker/docker-compose.yml --env-file .env.production --profile full up -d

# 8. Verify deployment
curl http://localhost:8000/api/health
```

### Rolling Update

```bash
# 1. Pull latest images
docker-compose -f docker/docker-compose.yml --env-file .env.production pull

# 2. Recreate services with zero downtime
docker-compose -f docker/docker-compose.yml --env-file .env.production up -d --no-deps --build api

# 3. Verify health
curl http://localhost:8000/api/health

# 4. Update frontend
docker-compose -f docker/docker-compose.yml --env-file .env.production up -d --no-deps --build frontend
```

### Rollback

```bash
# 1. Check previous image
docker images | grep local-agent-api

# 2. Tag and use previous version
docker tag local-agent-api:previous local-agent-api:latest

# 3. Restart service
docker-compose -f docker/docker-compose.yml --env-file .env.production up -d api
```

---

## Scaling and Performance

### Horizontal Scaling (Multiple API Instances)

```yaml
api:
  # ... other configuration
  deploy:
    replicas: 3

  # Load balancing via nginx
  depends_on:
    - mssql
    - mssql-backend
    - redis-stack
```

### Connection Pooling

Update API environment:

```yaml
environment:
  # SQLAlchemy connection pool
  DB_POOL_SIZE: "20"
  DB_MAX_OVERFLOW: "40"
  DB_POOL_TIMEOUT: "30"
  DB_POOL_RECYCLE: "3600"

  # Redis connection pool
  REDIS_MAX_CONNECTIONS: "50"
  REDIS_SOCKET_KEEPALIVE: "true"
```

### Performance Tuning

**SQL Server:**

```yaml
environment:
  MSSQL_MEMORY_LIMIT_MB: "4096"
  MSSQL_AGENT_ENABLED: "true"
```

**Redis:**

```yaml
command: >
  redis-server
  --maxmemory 4gb
  --maxmemory-policy allkeys-lru
  --tcp-backlog 511
  --timeout 300
```

**API Workers:**

```yaml
command: >
  uvicorn src.api.main:app
  --host 0.0.0.0
  --port 8000
  --workers 4
  --limit-concurrency 1000
  --timeout-keep-alive 5
```

---

## Backup and Restore

### Automated Backup Script

Create `scripts/backup-production.sh`:

```bash
#!/bin/bash
set -e

BACKUP_DIR="/backups/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

echo "Starting backup to $BACKUP_DIR"

# Backup SQL Server databases
docker exec local-agent-mssql /opt/mssql-tools18/bin/sqlcmd \
  -S localhost -U sa -P "$MSSQL_SA_PASSWORD" -C \
  -Q "BACKUP DATABASE ResearchAnalytics TO DISK='/var/opt/mssql/backup/ResearchAnalytics.bak' WITH INIT"

docker exec local-agent-mssql-backend /opt/mssql-tools18/bin/sqlcmd \
  -S localhost -U sa -P "$MSSQL_SA_PASSWORD" -C \
  -Q "BACKUP DATABASE LLM_BackEnd TO DISK='/var/opt/mssql/backup/LLM_BackEnd.bak' WITH INIT"

# Copy SQL backups
docker cp local-agent-mssql:/var/opt/mssql/backup/ResearchAnalytics.bak "$BACKUP_DIR/"
docker cp local-agent-mssql-backend:/var/opt/mssql/backup/LLM_BackEnd.bak "$BACKUP_DIR/"

# Backup Redis
docker exec local-agent-redis redis-cli BGSAVE
sleep 5
docker cp local-agent-redis:/data/dump.rdb "$BACKUP_DIR/redis.rdb"

# Backup volumes
tar -czf "$BACKUP_DIR/uploads.tar.gz" -C /data uploads/
tar -czf "$BACKUP_DIR/superset.tar.gz" -C /data superset/

# Backup configuration
cp .env.production "$BACKUP_DIR/"
cp docker/docker-compose.yml "$BACKUP_DIR/"

echo "Backup completed: $BACKUP_DIR"
```

### Restore Procedure

```bash
#!/bin/bash
BACKUP_DIR=$1

# Restore SQL Server
docker cp "$BACKUP_DIR/ResearchAnalytics.bak" local-agent-mssql:/var/opt/mssql/backup/
docker exec local-agent-mssql /opt/mssql-tools18/bin/sqlcmd \
  -S localhost -U sa -P "$MSSQL_SA_PASSWORD" -C \
  -Q "RESTORE DATABASE ResearchAnalytics FROM DISK='/var/opt/mssql/backup/ResearchAnalytics.bak' WITH REPLACE"

# Restore Redis
docker cp "$BACKUP_DIR/redis.rdb" local-agent-redis:/data/dump.rdb
docker-compose restart redis-stack

# Restore volumes
tar -xzf "$BACKUP_DIR/uploads.tar.gz" -C /data
```

---

## Troubleshooting

### Common Issues

#### Services Not Starting

```bash
# Check logs
docker-compose -f docker/docker-compose.yml logs

# Check resource usage
docker stats

# Check health
docker-compose -f docker/docker-compose.yml ps
```

#### Database Connection Errors

```bash
# Test SQL Server connectivity
docker exec local-agent-mssql /opt/mssql-tools18/bin/sqlcmd \
  -S localhost -U sa -P "$MSSQL_SA_PASSWORD" -C -Q "SELECT @@VERSION"

# Check network connectivity
docker exec local-agent-api ping mssql
docker exec local-agent-api ping mssql-backend
```

#### Performance Issues

```bash
# Check resource usage
docker stats

# Check SQL Server wait stats
docker exec local-agent-mssql /opt/mssql-tools18/bin/sqlcmd \
  -S localhost -U sa -P "$MSSQL_SA_PASSWORD" -C \
  -Q "SELECT * FROM sys.dm_os_wait_stats ORDER BY wait_time_ms DESC"

# Check Redis memory usage
docker exec local-agent-redis redis-cli INFO memory
```

### Monitoring Commands

```bash
# View all container status
docker-compose -f docker/docker-compose.yml ps

# Follow logs for all services
docker-compose -f docker/docker-compose.yml logs -f

# Check health endpoints
curl http://localhost:8000/api/health
curl http://localhost:8088/health

# Monitor resource usage
watch -n 1 docker stats
```

---

## Security Hardening

See [security-checklist.md](security-checklist.md) for comprehensive security guidance:

- [ ] Change all default passwords
- [ ] Configure firewall rules
- [ ] Enable SSL/TLS
- [ ] Implement network isolation
- [ ] Configure secrets management
- [ ] Enable audit logging
- [ ] Set up intrusion detection

---

## Next Steps

1. **Set Up Monitoring** - Configure health checks and alerting ([monitoring.md](monitoring.md))
2. **Configure Backups** - Set up automated backup schedule
3. **Security Review** - Complete security checklist
4. **Load Testing** - Verify performance under load
5. **Documentation** - Document your specific configuration

---

*Last Updated: December 2025*
