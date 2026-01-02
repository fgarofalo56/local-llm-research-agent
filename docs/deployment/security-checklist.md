# Security Checklist

> **Comprehensive security hardening guide for production deployments**

---

## Table of Contents

- [Overview](#overview)
- [Pre-Deployment Security](#pre-deployment-security)
- [Credentials and Secrets](#credentials-and-secrets)
- [Network Security](#network-security)
- [Database Security](#database-security)
- [Application Security](#application-security)
- [Container Security](#container-security)
- [Monitoring and Auditing](#monitoring-and-auditing)
- [Compliance](#compliance)

---

## Overview

This checklist covers essential security measures for deploying the Local LLM Research Agent in production environments. Follow these guidelines to ensure a secure deployment.

### Security Principles

1. **Defense in Depth** - Multiple layers of security controls
2. **Least Privilege** - Minimum necessary permissions
3. **Secure by Default** - Safe default configurations
4. **Zero Trust** - Verify all access attempts
5. **Privacy First** - All data processing remains local

---

## Pre-Deployment Security

### Environment Preparation

- [ ] **Create dedicated user accounts** for running services
- [ ] **Disable root access** for application services
- [ ] **Configure host firewall** (iptables, ufw, or Windows Firewall)
- [ ] **Update all base images** to latest security patches
- [ ] **Scan images for vulnerabilities** using tools like Trivy or Snyk

```bash
# Update host system
sudo apt update && sudo apt upgrade -y  # Linux
# Or Windows Update for Windows hosts

# Scan Docker images for vulnerabilities
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
  aquasec/trivy image mcr.microsoft.com/mssql/server:2022-latest

# Create dedicated service account (Linux)
sudo useradd -r -s /bin/false llmagent
```

---

## Credentials and Secrets

### Password Requirements

- [ ] **Minimum 16 characters** for production passwords
- [ ] **Use password generator** for all service passwords
- [ ] **Rotate passwords** every 90 days
- [ ] **Never commit** passwords to version control
- [ ] **Use environment variables** for all credentials
- [ ] **Implement password complexity** (uppercase, lowercase, numbers, symbols)

### Generate Strong Passwords

```bash
# SQL Server SA password (16+ characters)
openssl rand -base64 24

# Superset secret key (42+ characters)
openssl rand -base64 42

# General secure tokens
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# Using pwgen (if installed)
pwgen -s 32 1
```

### Environment Variables Security

```bash
# CRITICAL: Secure .env file permissions
chmod 600 .env.production

# Verify permissions
ls -la .env.production
# Should show: -rw------- (600)

# Set ownership
chown llmagent:llmagent .env.production
```

### Secret Management

For production, consider using a dedicated secrets manager:

**Option 1: Docker Secrets (Swarm mode)**

```yaml
secrets:
  mssql_sa_password:
    external: true
  superset_secret_key:
    external: true

services:
  mssql:
    secrets:
      - mssql_sa_password
    environment:
      MSSQL_SA_PASSWORD_FILE: /run/secrets/mssql_sa_password
```

**Option 2: HashiCorp Vault**

```bash
# Store secrets in Vault
vault kv put secret/llmagent/mssql password="$MSSQL_SA_PASSWORD"

# Retrieve in application
vault kv get -field=password secret/llmagent/mssql
```

**Option 3: AWS Secrets Manager / Azure Key Vault**

For cloud deployments, use native secret management services.

### Credentials Checklist

- [ ] `MSSQL_SA_PASSWORD` - Changed from default, 16+ chars
- [ ] `SUPERSET_SECRET_KEY` - Generated unique key, 42+ chars
- [ ] `SUPERSET_ADMIN_PASSWORD` - Changed from default, 16+ chars
- [ ] `SQL_USERNAME` and `SQL_PASSWORD` - If using non-SA account
- [ ] All default passwords changed
- [ ] Passwords stored in secure secret manager
- [ ] `.env` file permissions set to 600
- [ ] `.env` file added to `.gitignore`

---

## Network Security

### Firewall Configuration

#### Linux (ufw)

```bash
# Enable firewall
sudo ufw enable

# Allow SSH (if remote access needed)
sudo ufw allow 22/tcp

# Allow application ports (adjust as needed)
sudo ufw allow 8000/tcp   # FastAPI
sudo ufw allow 5173/tcp   # React UI (if external)

# Block direct database access from external networks
sudo ufw deny 1433/tcp    # SQL Server
sudo ufw deny 1434/tcp    # Backend DB
sudo ufw deny 6379/tcp    # Redis

# Allow from specific IP range (example)
sudo ufw allow from 192.168.1.0/24 to any port 8000
```

#### Windows Firewall

```powershell
# Allow FastAPI
New-NetFirewallRule -DisplayName "LLM Agent API" -Direction Inbound -Port 8000 -Protocol TCP -Action Allow

# Block SQL Server from external
New-NetFirewallRule -DisplayName "Block SQL Server" -Direction Inbound -Port 1433,1434 -Protocol TCP -Action Block -RemoteAddress Internet
```

### Network Isolation

- [ ] **Use Docker networks** to isolate services
- [ ] **Block external database access** (ports 1433, 1434, 6379)
- [ ] **Implement reverse proxy** for external access (nginx, Traefik)
- [ ] **Enable SSL/TLS** for all external endpoints
- [ ] **Restrict MCP server access** to localhost only

```yaml
networks:
  frontend:
    driver: bridge
    internal: false  # Exposed to host
  backend:
    driver: bridge
    internal: true   # Isolated, no external access

services:
  api:
    networks:
      - frontend
      - backend

  mssql:
    networks:
      - backend  # Not accessible from frontend
```

### SSL/TLS Configuration

#### Using Let's Encrypt with nginx

```nginx
server {
    listen 80;
    server_name yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    location /api/ {
        proxy_pass http://localhost:8000/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location / {
        proxy_pass http://localhost:5173/;
        proxy_set_header Host $host;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

### Network Security Checklist

- [ ] Firewall rules configured
- [ ] Database ports blocked from external access
- [ ] SSL/TLS certificates installed and configured
- [ ] Reverse proxy configured (if exposing externally)
- [ ] Docker networks isolated (frontend/backend separation)
- [ ] Unused ports closed
- [ ] VPN or bastion host for remote database access (if needed)

---

## Database Security

### SQL Server Security

#### Authentication

- [ ] **Disable SA account** after creating dedicated accounts
- [ ] **Use Windows Authentication** where possible
- [ ] **Create service accounts** with minimal permissions
- [ ] **Enable encryption** for connections
- [ ] **Enforce strong password policies**

```sql
-- Create dedicated application user
USE master;
GO
CREATE LOGIN llm_agent_user WITH PASSWORD = '<strong_password>';
GO

-- Grant specific database access
USE ResearchAnalytics;
GO
CREATE USER llm_agent_user FOR LOGIN llm_agent_user;
GO

-- Grant minimal permissions (read-only for demo)
ALTER ROLE db_datareader ADD MEMBER llm_agent_user;
GO

-- For backend database (read/write needed)
USE LLM_BackEnd;
GO
CREATE USER llm_agent_user FOR LOGIN llm_agent_user;
GO
ALTER ROLE db_datareader ADD MEMBER llm_agent_user;
ALTER ROLE db_datawriter ADD MEMBER llm_agent_user;
GO
```

#### Encryption

```sql
-- Enable Transparent Data Encryption (TDE)
USE master;
GO
CREATE MASTER KEY ENCRYPTION BY PASSWORD = '<strong_password>';
GO

CREATE CERTIFICATE TDE_Cert WITH SUBJECT = 'TDE Certificate';
GO

USE ResearchAnalytics;
GO
CREATE DATABASE ENCRYPTION KEY
WITH ALGORITHM = AES_256
ENCRYPTION BY SERVER CERTIFICATE TDE_Cert;
GO

ALTER DATABASE ResearchAnalytics SET ENCRYPTION ON;
GO
```

#### Auditing

```sql
-- Enable SQL Server Audit
USE master;
GO
CREATE SERVER AUDIT LLMAgentAudit
TO FILE (FILEPATH = '/var/opt/mssql/audit/', MAXSIZE = 100 MB);
GO

ALTER SERVER AUDIT LLMAgentAudit WITH (STATE = ON);
GO

-- Audit database access
CREATE DATABASE AUDIT SPECIFICATION ResearchAnalyticsAudit
FOR SERVER AUDIT LLMAgentAudit
ADD (DATABASE_OBJECT_ACCESS_GROUP),
ADD (SCHEMA_OBJECT_ACCESS_GROUP)
WITH (STATE = ON);
GO
```

### Redis Security

```yaml
redis-stack:
  command: >
    redis-server
    --requirepass ${REDIS_PASSWORD}
    --maxmemory 2gb
    --maxmemory-policy allkeys-lru
    --save 900 1
    --appendonly yes
    --protected-mode yes
    --bind 127.0.0.1 ::1
```

Update environment:

```bash
REDIS_URL=redis://:${REDIS_PASSWORD}@redis-stack:6379
REDIS_PASSWORD=<generate_strong_password>
```

### Database Security Checklist

- [ ] SQL Server: SA account disabled or password changed
- [ ] Dedicated service accounts created with minimal permissions
- [ ] Transparent Data Encryption (TDE) enabled
- [ ] Connection encryption enforced (`Encrypt=true`)
- [ ] SQL Server audit enabled
- [ ] Redis password authentication enabled
- [ ] Database backup encryption enabled
- [ ] Regular security patches applied

---

## Application Security

### API Security

#### Rate Limiting

```python
# In .env.production
RATE_LIMIT_ENABLED=true
RATE_LIMIT_RPM=100       # Requests per minute
RATE_LIMIT_BURST=20       # Burst allowance
```

#### CORS Configuration

```python
# src/api/main.py
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://yourdomain.com",
        "https://app.yourdomain.com"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)
```

#### Authentication (Future Implementation)

For production with multiple users, implement authentication:

```python
# Example: JWT authentication
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    # Verify JWT token
    # ...
    return user
```

### Input Validation

- [ ] **Pydantic models** for all request/response validation
- [ ] **SQL injection prevention** via parameterized queries
- [ ] **File upload validation** (size, type, content)
- [ ] **Input sanitization** for user-provided content
- [ ] **Path traversal prevention** for file operations

```python
# Example: File upload validation
from fastapi import UploadFile, HTTPException

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt"}
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100 MB

async def validate_upload(file: UploadFile):
    # Check extension
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(400, f"File type {ext} not allowed")

    # Check size
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(400, "File too large")

    await file.seek(0)
    return file
```

### Logging Security

```python
# Sanitize logs - never log sensitive data
import structlog

logger = structlog.get_logger()

# DON'T: Log passwords
logger.info("login_attempt", username=username, password=password)

# DO: Log sanitized info
logger.info("login_attempt", username=username, ip=request.client.host)
```

### Application Security Checklist

- [ ] Debug mode disabled (`DEBUG=false`)
- [ ] Rate limiting enabled
- [ ] CORS properly configured
- [ ] Input validation on all endpoints
- [ ] SQL injection prevention via ORMs/parameterized queries
- [ ] File upload restrictions enforced
- [ ] Sensitive data not logged
- [ ] Error messages don't expose internals
- [ ] API authentication implemented (if multi-user)

---

## Container Security

### Image Security

- [ ] **Use official images** from trusted sources
- [ ] **Pin image versions** (avoid `latest` tag)
- [ ] **Scan images** for vulnerabilities
- [ ] **Minimize image layers** to reduce attack surface
- [ ] **Run as non-root** user when possible

```yaml
# Example: Non-root user in Dockerfile
FROM python:3.11-slim

# Create non-root user
RUN useradd -m -u 1000 llmagent
USER llmagent

# ... rest of Dockerfile
```

```yaml
# docker-compose.yml: Pin versions
services:
  mssql:
    image: mcr.microsoft.com/mssql/server:2022-CU10-ubuntu-22.04
    # NOT: image: mcr.microsoft.com/mssql/server:latest
```

### Runtime Security

```yaml
services:
  api:
    # Drop unnecessary capabilities
    cap_drop:
      - ALL
    cap_add:
      - NET_BIND_SERVICE

    # Read-only root filesystem
    read_only: true
    tmpfs:
      - /tmp
      - /var/tmp

    # Security options
    security_opt:
      - no-new-privileges:true
```

### Resource Limits

```yaml
services:
  api:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
        reservations:
          cpus: '1'
          memory: 2G

    # Prevent fork bombs
    ulimits:
      nproc: 65535
      nofile:
        soft: 20000
        hard: 40000
```

### Container Security Checklist

- [ ] All images from official sources
- [ ] Image versions pinned (not `latest`)
- [ ] Images scanned for vulnerabilities
- [ ] Containers run as non-root user
- [ ] Resource limits configured
- [ ] Unnecessary capabilities dropped
- [ ] Read-only filesystems where possible
- [ ] Security options enabled (no-new-privileges)

---

## Monitoring and Auditing

### Access Logging

```yaml
# nginx access log
access_log /var/log/nginx/llmagent-access.log combined;

# FastAPI access logging
# In src/api/main.py
from fastapi.middleware.trustedhost import TrustedHostMiddleware

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["yourdomain.com", "*.yourdomain.com"]
)
```

### Security Event Monitoring

Monitor for:

- [ ] **Failed login attempts** (>5 in 5 minutes)
- [ ] **Unusual query patterns** (large data exports)
- [ ] **Failed health checks** (service degradation)
- [ ] **Resource exhaustion** (CPU, memory spikes)
- [ ] **Network anomalies** (unusual ports, protocols)

```bash
# Example: Monitor failed SQL logins
docker exec local-agent-mssql /opt/mssql-tools18/bin/sqlcmd \
  -S localhost -U sa -P "$MSSQL_SA_PASSWORD" -C \
  -Q "SELECT TOP 100 * FROM sys.dm_exec_sessions WHERE login_name LIKE '%failed%' ORDER BY login_time DESC"
```

### Audit Logging

Enable comprehensive audit logging:

```python
# Example: Audit middleware
@app.middleware("http")
async def audit_middleware(request: Request, call_next):
    start_time = time.time()

    # Log request
    logger.info("request_received",
        method=request.method,
        path=request.url.path,
        client_ip=request.client.host
    )

    response = await call_next(request)

    # Log response
    logger.info("request_completed",
        method=request.method,
        path=request.url.path,
        status_code=response.status_code,
        duration_ms=(time.time() - start_time) * 1000
    )

    return response
```

### Intrusion Detection

Consider implementing:

- **Fail2ban** - Ban IPs with repeated failed attempts
- **OSSEC** - Host-based intrusion detection
- **Wazuh** - Security monitoring platform

```bash
# Example: Fail2ban for API
# /etc/fail2ban/filter.d/llmagent-api.conf
[Definition]
failregex = ^<HOST>.*"POST /api/auth/login HTTP.*" 401
ignoreregex =

# /etc/fail2ban/jail.d/llmagent-api.conf
[llmagent-api]
enabled = true
port = 8000
filter = llmagent-api
logpath = /var/log/llmagent/access.log
maxretry = 5
bantime = 3600
```

### Monitoring Checklist

- [ ] Access logging enabled
- [ ] Security events monitored
- [ ] Audit trails configured
- [ ] Failed login tracking
- [ ] Intrusion detection system (optional)
- [ ] Log rotation configured
- [ ] Logs forwarded to SIEM (optional)

---

## Compliance

### Data Privacy (GDPR, HIPAA, etc.)

- [ ] **Data minimization** - Only collect necessary data
- [ ] **Encryption at rest** - TDE, encrypted volumes
- [ ] **Encryption in transit** - SSL/TLS
- [ ] **Right to deletion** - Implement data purge procedures
- [ ] **Access controls** - Role-based access
- [ ] **Audit trails** - Comprehensive logging

### Data Retention

```sql
-- Example: Data retention policy (90 days)
CREATE PROCEDURE CleanupOldData
AS
BEGIN
    DELETE FROM app.messages
    WHERE created_at < DATEADD(DAY, -90, GETDATE());

    DELETE FROM app.conversations
    WHERE updated_at < DATEADD(DAY, -90, GETDATE())
    AND deleted = 1;
END;
GO
```

### Backup Security

- [ ] **Encrypted backups** - Encrypt backup files
- [ ] **Secure backup storage** - Separate from production
- [ ] **Backup retention policy** - 30/60/90 day retention
- [ ] **Backup testing** - Regular restore tests
- [ ] **Offsite backups** - Geographic separation

```bash
# Encrypted SQL Server backup
docker exec local-agent-mssql /opt/mssql-tools18/bin/sqlcmd \
  -S localhost -U sa -P "$MSSQL_SA_PASSWORD" -C \
  -Q "BACKUP DATABASE LLM_BackEnd TO DISK='/var/opt/mssql/backup/LLM_BackEnd_encrypted.bak' WITH ENCRYPTION (ALGORITHM = AES_256, SERVER CERTIFICATE = TDE_Cert)"
```

---

## Security Incident Response

### Incident Response Plan

1. **Detection** - Monitor alerts and logs
2. **Containment** - Isolate affected services
3. **Investigation** - Analyze logs and forensics
4. **Remediation** - Patch vulnerabilities
5. **Recovery** - Restore services
6. **Post-Mortem** - Document and improve

### Emergency Procedures

```bash
# Immediately stop all services
docker-compose -f docker/docker-compose.yml down

# Isolate specific service
docker network disconnect local-agent-network local-agent-api

# Export logs for forensics
docker logs local-agent-api > /tmp/api-logs-$(date +%Y%m%d).log
docker logs local-agent-mssql > /tmp/mssql-logs-$(date +%Y%m%d).log

# Create backup before investigation
./scripts/backup-production.sh
```

---

## Security Testing

### Penetration Testing

- [ ] **SQL injection testing** on all endpoints
- [ ] **XSS testing** on input fields
- [ ] **CSRF testing** on state-changing operations
- [ ] **Authentication bypass** attempts
- [ ] **Authorization testing** (privilege escalation)

### Vulnerability Scanning

```bash
# Scan Docker images
trivy image local-agent-api:latest

# Scan for secrets in code
gitleaks detect --source . --verbose

# Dependency vulnerability scan
pip-audit
npm audit (for frontend)
```

### Security Testing Checklist

- [ ] Penetration testing completed
- [ ] Vulnerability scan passed
- [ ] Dependency audit clean
- [ ] No secrets in code
- [ ] Security headers configured
- [ ] OWASP Top 10 mitigations verified

---

## Final Security Checklist

### Before Production

- [ ] All default passwords changed
- [ ] Environment variables secured (600 permissions)
- [ ] Firewall configured
- [ ] SSL/TLS certificates installed
- [ ] Database encryption enabled
- [ ] Backups configured and tested
- [ ] Monitoring and alerting active
- [ ] Audit logging enabled
- [ ] Security testing completed
- [ ] Incident response plan documented
- [ ] Team trained on security procedures

### Regular Maintenance

- [ ] Monthly: Review access logs
- [ ] Monthly: Update dependencies
- [ ] Monthly: Vulnerability scanning
- [ ] Quarterly: Password rotation
- [ ] Quarterly: Security audit
- [ ] Quarterly: Backup restoration test
- [ ] Annually: Penetration testing
- [ ] Annually: Security training

---

## Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [CIS Docker Benchmark](https://www.cisecurity.org/benchmark/docker)
- [SQL Server Security Best Practices](https://docs.microsoft.com/en-us/sql/relational-databases/security/security-center-for-sql-server-database-engine)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
- [Docker Security](https://docs.docker.com/engine/security/)

---

*Last Updated: December 2025*
