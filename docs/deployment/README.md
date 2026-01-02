# Deployment Guide

> **Comprehensive guide for deploying the Local LLM Research Agent in various environments**

---

## Table of Contents

- [Overview](#overview)
- [Deployment Options](#deployment-options)
- [Prerequisites](#prerequisites)
- [Quick Deployment](#quick-deployment)
- [Production Checklist](#production-checklist)
- [Related Documentation](#related-documentation)

---

## Overview

The Local LLM Research Agent is designed for flexible deployment, from local development to production environments. This guide covers deployment strategies, security considerations, and monitoring setup.

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     User Access Layer                        │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────────┐   │
│  │ React UI     │  │ Streamlit UI │  │ FastAPI Docs    │   │
│  │ Port 5173    │  │ Port 8501    │  │ Port 8000       │   │
│  └──────────────┘  └──────────────┘  └─────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                   Application Layer                          │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ FastAPI Backend (Uvicorn)                            │   │
│  │ - REST API endpoints                                 │   │
│  │ - WebSocket streaming                                │   │
│  │ - Agent orchestration                                │   │
│  │ - RAG pipeline                                       │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                            │
          ┌─────────────────┴─────────────────┬──────────────┐
          ▼                 ▼                 ▼              ▼
┌──────────────────┐ ┌──────────────┐ ┌───────────┐ ┌──────────────┐
│ SQL Server 2022  │ │ SQL Server   │ │ Redis     │ │ Ollama       │
│ (Sample DB)      │ │ 2025         │ │ Stack     │ │ (Host)       │
│ Port 1433        │ │ (Backend)    │ │ Port 6379 │ │ Port 11434   │
│                  │ │ Port 1434    │ │           │ │              │
│ ResearchAnalytics│ │ LLM_BackEnd  │ │ Cache +   │ │ Local LLM    │
│ (Demo Data)      │ │ (App State + │ │ Vectors   │ │ Inference    │
│                  │ │  Vectors)    │ │ (fallback)│ │              │
└──────────────────┘ └──────────────┘ └───────────┘ └──────────────┘
```

---

## Deployment Options

### 1. Local Development

**Best for:** Development, testing, experimentation

**Characteristics:**
- Single machine deployment
- Docker containers for databases
- Host-based Ollama
- Quick setup
- Full debugging access

**Setup Time:** 15-30 minutes

**See:** [Quick Deployment](#quick-deployment)

---

### 2. Docker Compose Production

**Best for:** Small to medium production deployments, single-server setups

**Characteristics:**
- All services containerized
- Docker networks for isolation
- Persistent volumes for data
- Easy backup and restore
- Simplified deployment

**Setup Time:** 30-60 minutes

**See:** [docker-compose.md](docker-compose.md)

---

### 3. Kubernetes (Future)

**Best for:** Large-scale production, high availability, auto-scaling

**Characteristics:**
- Horizontal scaling
- Load balancing
- Self-healing
- Rolling updates
- Multi-node deployment

**Status:** Planned for future release

---

### 4. Hybrid Deployment

**Best for:** Existing infrastructure integration

**Characteristics:**
- Existing SQL Server
- Existing Redis cluster
- Containerized application
- Integration with enterprise systems

**Setup Time:** 1-2 hours (varies by environment)

---

## Prerequisites

### Required Software

| Component | Version | Purpose | Installation |
|-----------|---------|---------|--------------|
| **Docker Desktop** | Latest | Container runtime | [Download](https://www.docker.com/products/docker-desktop/) |
| **Docker Compose** | 2.0+ | Multi-container orchestration | Included with Docker Desktop |
| **Ollama** | Latest | Local LLM inference | [Download](https://ollama.com/) |
| **Git** | 2.0+ | Source control | [Download](https://git-scm.com/) |

### Optional Software

| Component | Purpose |
|-----------|---------|
| **SQL Server Management Studio** | Database administration |
| **Azure Data Studio** | Cross-platform SQL client |
| **Redis CLI** | Redis command-line tools |
| **Node.js 18+** | MCP server (if not using Python version) |

### System Requirements

#### Minimum

| Resource | Requirement |
|----------|-------------|
| **CPU** | 4 cores |
| **RAM** | 16 GB |
| **Disk** | 50 GB free |
| **GPU** | Not required (CPU inference) |

#### Recommended

| Resource | Requirement |
|----------|-------------|
| **CPU** | 8+ cores (AMD Ryzen 9 / Intel i9) |
| **RAM** | 32+ GB |
| **Disk** | 100+ GB SSD |
| **GPU** | NVIDIA GPU with 8+ GB VRAM (for faster inference) |

### Network Requirements

| Port | Service | Required |
|------|---------|----------|
| 1433 | SQL Server 2022 (Sample) | Yes |
| 1434 | SQL Server 2025 (Backend) | Yes |
| 5173 | React Frontend | Yes (production) |
| 6379 | Redis | Yes |
| 8000 | FastAPI Backend | Yes |
| 8001 | RedisInsight (GUI) | Optional |
| 8088 | Apache Superset | Optional |
| 8501 | Streamlit UI | Optional |
| 11434 | Ollama | Yes |

---

## Quick Deployment

### Step 1: Clone Repository

```bash
git clone https://github.com/yourusername/local-llm-research-agent.git
cd local-llm-research-agent
```

### Step 2: Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env file with your settings
# Minimum required:
# - MSSQL_SA_PASSWORD (strong password)
# - OLLAMA_HOST (http://localhost:11434 or http://host.docker.internal:11434)
# - OLLAMA_MODEL (qwen2.5:7b-instruct)
```

**Critical Variables:**

```bash
# Strong password for SQL Server
MSSQL_SA_PASSWORD=YourSecurePassword123!

# LLM Configuration
OLLAMA_HOST=http://host.docker.internal:11434
OLLAMA_MODEL=qwen2.5:7b-instruct
EMBEDDING_MODEL=nomic-embed-text

# Vector Store (use SQL Server 2025 native vectors)
VECTOR_STORE_TYPE=mssql
VECTOR_DIMENSIONS=768
```

### Step 3: Pull Ollama Models

```bash
# Required: LLM model for inference
ollama pull qwen2.5:7b-instruct

# Required: Embedding model for RAG
ollama pull nomic-embed-text

# Optional: Alternative models
ollama pull llama3.1:8b
ollama pull mistral:7b-instruct
```

### Step 4: Start Services

```bash
# From project root - Start all services
docker-compose -f docker/docker-compose.yml --env-file .env --profile full up -d

# Initialize databases (first time only)
docker-compose -f docker/docker-compose.yml --env-file .env --profile init up mssql-tools
docker-compose -f docker/docker-compose.yml --env-file .env --profile init up mssql-backend-tools
```

### Step 5: Verify Deployment

```bash
# Check all containers are running
docker ps --filter name=local-agent

# Check health status
curl http://localhost:8000/api/health

# View logs
docker-compose -f docker/docker-compose.yml logs -f
```

### Step 6: Access Interfaces

| Interface | URL | Credentials |
|-----------|-----|-------------|
| **React UI** | http://localhost:5173 | None |
| **FastAPI Docs** | http://localhost:8000/docs | None |
| **Streamlit UI** | http://localhost:8501 | None |
| **Superset** | http://localhost:8088 | admin / (see SUPERSET_ADMIN_PASSWORD) |

### Step 7: Test Functionality

```bash
# Test chat endpoint
curl -X POST http://localhost:8000/api/agent/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What tables are in the database?"}'

# Test document upload
curl -X POST http://localhost:8000/api/documents \
  -F "file=@sample.pdf"

# Test vector search
curl -X POST http://localhost:8000/api/documents/search \
  -H "Content-Type: application/json" \
  -d '{"query": "machine learning"}'
```

---

## Production Checklist

Before deploying to production, ensure:

### Security

- [ ] Changed default passwords (SQL Server, Superset)
- [ ] Generated secure secret keys
- [ ] Configured firewall rules
- [ ] Enabled SSL/TLS certificates
- [ ] Restricted network access
- [ ] Configured environment variables securely
- [ ] Removed debug mode (`DEBUG=false`)

**See:** [security-checklist.md](security-checklist.md)

### Data Persistence

- [ ] Verified Docker volume persistence
- [ ] Configured backup strategy
- [ ] Tested restore procedures
- [ ] Documented disaster recovery plan

### Monitoring

- [ ] Health check endpoints configured
- [ ] Log aggregation setup
- [ ] Metrics collection enabled
- [ ] Alerting configured
- [ ] Performance baseline established

**See:** [monitoring.md](monitoring.md)

### Performance

- [ ] Database connection pooling configured
- [ ] Redis cache tuned
- [ ] Ollama model optimized for hardware
- [ ] API rate limiting configured
- [ ] Load testing completed

### Documentation

- [ ] Deployment runbook created
- [ ] Rollback procedures documented
- [ ] Contact information updated
- [ ] Configuration documented

---

## Related Documentation

### Deployment Guides

- [Docker Compose Deployment](docker-compose.md) - Production deployment with Docker Compose
- [Security Checklist](security-checklist.md) - Security hardening guide
- [Monitoring Setup](monitoring.md) - Monitoring and alerting configuration

### Configuration

- [Configuration Guide](../guides/configuration.md) - Environment variables and settings
- [Docker Services Guide](../guides/docker-services.md) - Service-specific documentation
- [Troubleshooting Guide](../guides/troubleshooting.md) - Common issues and solutions

### Architecture

- [FastAPI Documentation](../api/fastapi.md) - Backend API reference
- [RAG Pipeline](../api/rag.md) - RAG system architecture
- [Architecture Decision Records](../adr/README.md) - Design decisions

---

## Support

### Common Issues

For troubleshooting deployment issues:

1. Check [Troubleshooting Guide](../guides/troubleshooting.md)
2. Review container logs: `docker-compose -f docker/docker-compose.yml logs`
3. Verify health endpoints: `curl http://localhost:8000/api/health`
4. Check GitHub Issues: [Project Issues](https://github.com/yourusername/local-llm-research-agent/issues)

### Getting Help

- **Documentation:** Start with the guides in `docs/`
- **GitHub Issues:** Report bugs and request features
- **Community:** Check discussions for Q&A

---

## Next Steps

After successful deployment:

1. **Configure Users** - Set up user access (if implementing authentication)
2. **Upload Documents** - Add documents for RAG pipeline
3. **Create Dashboards** - Build analytics dashboards
4. **Setup Superset** - Configure BI platform (optional)
5. **Enable Monitoring** - Set up health checks and alerts
6. **Backup Configuration** - Document and backup your setup

---

*Last Updated: December 2025*
