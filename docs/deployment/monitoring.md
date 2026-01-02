# Monitoring and Alerting Setup

> **Comprehensive monitoring configuration for production deployments**

---

## Table of Contents

- [Overview](#overview)
- [Health Check Endpoints](#health-check-endpoints)
- [Metrics Collection](#metrics-collection)
- [Log Aggregation](#log-aggregation)
- [Alerting Configuration](#alerting-configuration)
- [Performance Monitoring](#performance-monitoring)
- [Dashboard Setup](#dashboard-setup)
- [Troubleshooting](#troubleshooting)

---

## Overview

Effective monitoring ensures system reliability, performance, and early detection of issues. This guide covers monitoring setup for all components of the Local LLM Research Agent.

### Monitoring Stack

```
┌─────────────────────────────────────────────────────────────┐
│                    Monitoring Architecture                   │
└─────────────────────────────────────────────────────────────┘

  Application Layer                    Monitoring Tools
  ┌──────────────┐                    ┌──────────────┐
  │ FastAPI      │─── metrics ───────▶│ Prometheus   │
  │ React UI     │                    └──────────────┘
  │ Streamlit    │                           │
  └──────────────┘                           │
         │                                   ▼
         │                            ┌──────────────┐
         └────── logs ───────────────▶│ Loki/ELK     │
                                      └──────────────┘
                                             │
  Data Layer                                 │
  ┌──────────────┐                           │
  │ SQL Server   │─── logs ──────────────────┤
  │ Redis        │                           │
  └──────────────┘                           │
         │                                   ▼
         │                            ┌──────────────┐
         └────── health ────────────▶│ Grafana      │
                                      │ Dashboards   │
                                      └──────────────┘
                                             │
                                             ▼
                                      ┌──────────────┐
                                      │ AlertManager │
                                      │ PagerDuty    │
                                      │ Slack        │
                                      └──────────────┘
```

---

## Health Check Endpoints

### Built-in Health Checks

The FastAPI backend provides comprehensive health check endpoints:

#### 1. Liveness Check

**Endpoint:** `GET /api/health/live`

**Purpose:** Verify the application is running

**Response:**
```json
{
  "status": "alive"
}
```

**Use Case:** Kubernetes/Docker liveness probe

```yaml
# docker-compose.yml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/api/health/live"]
  interval: 30s
  timeout: 10s
  retries: 3
```

#### 2. Readiness Check

**Endpoint:** `GET /api/health/ready`

**Purpose:** Verify the application is ready to accept traffic

**Response:**
```json
{
  "status": "ready"
}
```

**Use Case:** Kubernetes readiness probe, load balancer health checks

#### 3. Full Health Check

**Endpoint:** `GET /api/health`

**Purpose:** Comprehensive health status of all dependencies

**Response:**
```json
{
  "status": "healthy",
  "services": [
    {
      "name": "sql_server",
      "status": "healthy",
      "latency_ms": 12.5
    },
    {
      "name": "redis",
      "status": "healthy",
      "latency_ms": 2.3
    },
    {
      "name": "ollama",
      "status": "healthy",
      "latency_ms": 45.8
    },
    {
      "name": "superset",
      "status": "unknown",
      "message": "Not available"
    }
  ]
}
```

**Status Values:**
- `healthy` - Service is fully operational
- `degraded` - Some services unhealthy, but core functionality available
- `unhealthy` - Critical services are down
- `unknown` - Service status cannot be determined

#### 4. Services Status

**Endpoint:** `GET /api/health/services`

**Purpose:** Detailed service configuration and status

**Response:**
```json
{
  "api": {
    "status": "running",
    "version": "2.1.0"
  },
  "redis": {
    "status": "connected"
  },
  "mcp_servers": [
    {
      "id": "mssql",
      "name": "MSSQL Server",
      "type": "stdio",
      "enabled": true
    }
  ]
}
```

### Testing Health Endpoints

```bash
# Quick health check
curl http://localhost:8000/api/health/live

# Full health status
curl http://localhost:8000/api/health | jq

# Check specific service
curl http://localhost:8000/api/health | jq '.services[] | select(.name=="sql_server")'

# Monitor continuously
watch -n 5 'curl -s http://localhost:8000/api/health | jq ".status"'
```

---

## Metrics Collection

### Prometheus Integration

#### Install Prometheus

**docker-compose.yml extension:**

```yaml
services:
  prometheus:
    image: prom/prometheus:latest
    container_name: local-agent-prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--storage.tsdb.retention.time=30d'
    restart: unless-stopped
    networks:
      - llm-network

volumes:
  prometheus_data:
    name: local-llm-prometheus-data
```

#### Prometheus Configuration

Create `monitoring/prometheus.yml`:

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s
  external_labels:
    cluster: 'local-llm-agent'
    environment: 'production'

scrape_configs:
  # FastAPI metrics
  - job_name: 'fastapi'
    static_configs:
      - targets: ['api:8000']
    metrics_path: '/metrics'

  # Docker container metrics
  - job_name: 'docker'
    static_configs:
      - targets: ['host.docker.internal:9323']

  # SQL Server metrics (via exporter)
  - job_name: 'mssql'
    static_configs:
      - targets: ['mssql-exporter:9399']

  # Redis metrics (via exporter)
  - job_name: 'redis'
    static_configs:
      - targets: ['redis-exporter:9121']

  # Node exporter (system metrics)
  - job_name: 'node'
    static_configs:
      - targets: ['node-exporter:9100']
```

#### Add FastAPI Metrics Endpoint

Install Prometheus client:

```bash
uv add prometheus-client
```

Add metrics to `src/api/main.py`:

```python
from prometheus_client import Counter, Histogram, Gauge, make_asgi_app
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

# Define metrics
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request latency',
    ['method', 'endpoint']
)

active_requests = Gauge(
    'active_requests',
    'Number of active requests'
)

# Add Prometheus middleware
@app.middleware("http")
async def prometheus_middleware(request: Request, call_next):
    active_requests.inc()
    start_time = time.time()

    response = await call_next(request)

    duration = time.time() - start_time
    http_request_duration_seconds.labels(
        method=request.method,
        endpoint=request.url.path
    ).observe(duration)

    http_requests_total.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()

    active_requests.dec()
    return response

# Metrics endpoint
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)
```

### SQL Server Metrics Exporter

Add to `docker-compose.yml`:

```yaml
services:
  mssql-exporter:
    image: awaragi/prometheus-mssql-exporter:latest
    container_name: local-agent-mssql-exporter
    environment:
      SERVER: "mssql"
      PORT: "1433"
      USERNAME: "sa"
      PASSWORD: "${MSSQL_SA_PASSWORD}"
      ENCRYPT: "disable"
    ports:
      - "9399:4000"
    restart: unless-stopped
    networks:
      - llm-network
```

### Redis Metrics Exporter

```yaml
services:
  redis-exporter:
    image: oliver006/redis_exporter:latest
    container_name: local-agent-redis-exporter
    environment:
      REDIS_ADDR: "redis-stack:6379"
      REDIS_PASSWORD: "${REDIS_PASSWORD:-}"
    ports:
      - "9121:9121"
    restart: unless-stopped
    networks:
      - llm-network
```

### System Metrics (Node Exporter)

```yaml
services:
  node-exporter:
    image: prom/node-exporter:latest
    container_name: local-agent-node-exporter
    ports:
      - "9100:9100"
    volumes:
      - /proc:/host/proc:ro
      - /sys:/host/sys:ro
      - /:/rootfs:ro
    command:
      - '--path.procfs=/host/proc'
      - '--path.sysfs=/host/sys'
      - '--collector.filesystem.mount-points-exclude=^/(sys|proc|dev|host|etc)($$|/)'
    restart: unless-stopped
    networks:
      - llm-network
```

### Key Metrics to Monitor

| Metric | Description | Alert Threshold |
|--------|-------------|-----------------|
| `http_requests_total` | Total API requests | - |
| `http_request_duration_seconds` | Request latency | p95 > 1s |
| `active_requests` | Concurrent requests | > 100 |
| `process_cpu_seconds_total` | CPU usage | > 80% |
| `process_resident_memory_bytes` | Memory usage | > 4GB |
| `mssql_up` | SQL Server availability | == 0 |
| `redis_up` | Redis availability | == 0 |
| `mssql_connections` | Active connections | > 80% of pool |

---

## Log Aggregation

### Docker Logging Configuration

Configure structured logging in `docker-compose.yml`:

```yaml
services:
  api:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "5"
        labels: "service,component"
```

### Centralized Logging with Loki

#### Install Loki and Promtail

```yaml
services:
  loki:
    image: grafana/loki:latest
    container_name: local-agent-loki
    ports:
      - "3100:3100"
    volumes:
      - ./monitoring/loki-config.yml:/etc/loki/local-config.yaml:ro
      - loki_data:/loki
    command: -config.file=/etc/loki/local-config.yaml
    restart: unless-stopped
    networks:
      - llm-network

  promtail:
    image: grafana/promtail:latest
    container_name: local-agent-promtail
    volumes:
      - ./monitoring/promtail-config.yml:/etc/promtail/config.yml:ro
      - /var/lib/docker/containers:/var/lib/docker/containers:ro
      - /var/run/docker.sock:/var/run/docker.sock
    command: -config.file=/etc/promtail/config.yml
    restart: unless-stopped
    networks:
      - llm-network

volumes:
  loki_data:
    name: local-llm-loki-data
```

#### Loki Configuration

Create `monitoring/loki-config.yml`:

```yaml
auth_enabled: false

server:
  http_listen_port: 3100

ingester:
  lifecycler:
    address: 127.0.0.1
    ring:
      kvstore:
        store: inmemory
      replication_factor: 1
    final_sleep: 0s
  chunk_idle_period: 5m
  chunk_retain_period: 30s

schema_config:
  configs:
    - from: 2023-01-01
      store: boltdb
      object_store: filesystem
      schema: v11
      index:
        prefix: index_
        period: 168h

storage_config:
  boltdb:
    directory: /loki/index
  filesystem:
    directory: /loki/chunks

limits_config:
  enforce_metric_name: false
  reject_old_samples: true
  reject_old_samples_max_age: 168h
```

#### Promtail Configuration

Create `monitoring/promtail-config.yml`:

```yaml
server:
  http_listen_port: 9080
  grpc_listen_port: 0

positions:
  filename: /tmp/positions.yaml

clients:
  - url: http://loki:3100/loki/api/v1/push

scrape_configs:
  - job_name: docker
    docker_sd_configs:
      - host: unix:///var/run/docker.sock
        refresh_interval: 5s
        filters:
          - name: name
            values: ["local-agent-*"]
    relabel_configs:
      - source_labels: ['__meta_docker_container_name']
        regex: '/(.*)'
        target_label: 'container'
      - source_labels: ['__meta_docker_container_log_stream']
        target_label: 'stream'
```

### Structured Logging in Application

Ensure structured logging is configured in `src/utils/logger.py`:

```python
import structlog

structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()
```

### Log Query Examples

```bash
# Query Loki logs via CLI
curl -G -s "http://localhost:3100/loki/api/v1/query" \
  --data-urlencode 'query={container="local-agent-api"}' \
  | jq

# Filter by log level
curl -G -s "http://localhost:3100/loki/api/v1/query" \
  --data-urlencode 'query={container="local-agent-api"} |= "ERROR"' \
  | jq

# Count errors in last hour
curl -G -s "http://localhost:3100/loki/api/v1/query_range" \
  --data-urlencode 'query=count_over_time({container="local-agent-api"} |= "ERROR" [1h])' \
  | jq
```

---

## Alerting Configuration

### AlertManager Setup

```yaml
services:
  alertmanager:
    image: prom/alertmanager:latest
    container_name: local-agent-alertmanager
    ports:
      - "9093:9093"
    volumes:
      - ./monitoring/alertmanager.yml:/etc/alertmanager/alertmanager.yml:ro
    command:
      - '--config.file=/etc/alertmanager/alertmanager.yml'
    restart: unless-stopped
    networks:
      - llm-network
```

### AlertManager Configuration

Create `monitoring/alertmanager.yml`:

```yaml
global:
  resolve_timeout: 5m
  slack_api_url: 'https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK'

route:
  group_by: ['alertname', 'cluster', 'service']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 12h
  receiver: 'default'
  routes:
    - match:
        severity: critical
      receiver: 'critical'
    - match:
        severity: warning
      receiver: 'warning'

receivers:
  - name: 'default'
    slack_configs:
      - channel: '#llm-agent-alerts'
        title: 'LLM Agent Alert'
        text: '{{ range .Alerts }}{{ .Annotations.description }}{{ end }}'

  - name: 'critical'
    slack_configs:
      - channel: '#llm-agent-critical'
        title: 'CRITICAL: LLM Agent Alert'
        text: '{{ range .Alerts }}{{ .Annotations.description }}{{ end }}'
    # Add PagerDuty, email, etc.

  - name: 'warning'
    slack_configs:
      - channel: '#llm-agent-alerts'
        title: 'Warning: LLM Agent'
        text: '{{ range .Alerts }}{{ .Annotations.description }}{{ end }}'
```

### Alert Rules

Create `monitoring/alert-rules.yml`:

```yaml
groups:
  - name: api_alerts
    interval: 30s
    rules:
      # API is down
      - alert: APIDown
        expr: up{job="fastapi"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "API is down"
          description: "FastAPI service is not responding"

      # High error rate
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.05
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High API error rate"
          description: "Error rate is {{ $value }} errors/sec"

      # High response time
      - alert: HighLatency
        expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High API latency"
          description: "P95 latency is {{ $value }}s"

  - name: database_alerts
    interval: 30s
    rules:
      # SQL Server down
      - alert: SQLServerDown
        expr: mssql_up == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "SQL Server is down"
          description: "SQL Server is not responding"

      # High connection count
      - alert: HighSQLConnections
        expr: mssql_connections > 80
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High SQL Server connections"
          description: "{{ $value }} active connections"

      # Redis down
      - alert: RedisDown
        expr: redis_up == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Redis is down"
          description: "Redis is not responding"

  - name: system_alerts
    interval: 30s
    rules:
      # High CPU usage
      - alert: HighCPUUsage
        expr: rate(process_cpu_seconds_total[5m]) > 0.8
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High CPU usage"
          description: "CPU usage is {{ $value }}%"

      # High memory usage
      - alert: HighMemoryUsage
        expr: process_resident_memory_bytes > 4e9
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High memory usage"
          description: "Memory usage is {{ $value | humanize }}B"

      # Disk space low
      - alert: LowDiskSpace
        expr: node_filesystem_avail_bytes{mountpoint="/"} / node_filesystem_size_bytes{mountpoint="/"} < 0.1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Low disk space"
          description: "Only {{ $value | humanizePercentage }} free"
```

Update `prometheus.yml` to include alert rules:

```yaml
rule_files:
  - /etc/prometheus/alert-rules.yml

alerting:
  alertmanagers:
    - static_configs:
        - targets: ['alertmanager:9093']
```

---

## Performance Monitoring

### Application Performance Monitoring (APM)

For detailed application tracing, consider integrating:

#### OpenTelemetry

```bash
# Install OpenTelemetry
uv add opentelemetry-api opentelemetry-sdk opentelemetry-instrumentation-fastapi
```

```python
# src/api/main.py
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

# Configure tracing
trace.set_tracer_provider(TracerProvider())
tracer = trace.get_tracer(__name__)

# Add OTLP exporter
otlp_exporter = OTLPSpanExporter(endpoint="http://jaeger:4317")
trace.get_tracer_provider().add_span_processor(
    BatchSpanProcessor(otlp_exporter)
)

# Instrument FastAPI
FastAPIInstrumentor.instrument_app(app)
```

#### Jaeger for Distributed Tracing

```yaml
services:
  jaeger:
    image: jaegertracing/all-in-one:latest
    container_name: local-agent-jaeger
    ports:
      - "5775:5775/udp"
      - "6831:6831/udp"
      - "6832:6832/udp"
      - "5778:5778"
      - "16686:16686"  # UI
      - "14268:14268"
      - "14250:14250"
      - "4317:4317"    # OTLP gRPC
    environment:
      COLLECTOR_OTLP_ENABLED: "true"
    restart: unless-stopped
    networks:
      - llm-network
```

### Query Performance Monitoring

Monitor SQL query performance:

```python
# Custom middleware to track SQL query performance
from sqlalchemy import event
from sqlalchemy.engine import Engine
import time

@event.listens_for(Engine, "before_cursor_execute")
def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    conn.info.setdefault('query_start_time', []).append(time.time())

@event.listens_for(Engine, "after_cursor_execute")
def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    total = time.time() - conn.info['query_start_time'].pop(-1)
    if total > 1.0:  # Log slow queries (>1s)
        logger.warning("slow_query",
            duration_ms=total * 1000,
            statement=statement[:200]
        )
```

---

## Dashboard Setup

### Grafana Installation

```yaml
services:
  grafana:
    image: grafana/grafana:latest
    container_name: local-agent-grafana
    ports:
      - "3000:3000"
    volumes:
      - grafana_data:/var/lib/grafana
      - ./monitoring/grafana/dashboards:/etc/grafana/provisioning/dashboards:ro
      - ./monitoring/grafana/datasources:/etc/grafana/provisioning/datasources:ro
    environment:
      GF_SECURITY_ADMIN_PASSWORD: "${GRAFANA_ADMIN_PASSWORD:-admin}"
      GF_USERS_ALLOW_SIGN_UP: "false"
      GF_SERVER_ROOT_URL: "http://localhost:3000"
    restart: unless-stopped
    networks:
      - llm-network

volumes:
  grafana_data:
    name: local-llm-grafana-data
```

### Datasource Configuration

Create `monitoring/grafana/datasources/datasources.yml`:

```yaml
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true

  - name: Loki
    type: loki
    access: proxy
    url: http://loki:3100
```

### Pre-built Dashboards

Create `monitoring/grafana/dashboards/dashboards.yml`:

```yaml
apiVersion: 1

providers:
  - name: 'Local LLM Agent'
    orgId: 1
    folder: ''
    type: file
    disableDeletion: false
    updateIntervalSeconds: 10
    allowUiUpdates: true
    options:
      path: /etc/grafana/provisioning/dashboards
```

### Sample Dashboard JSON

Create `monitoring/grafana/dashboards/api-dashboard.json` with panels for:

1. **API Request Rate** - requests/second
2. **API Latency** - P50, P95, P99
3. **Error Rate** - 4xx, 5xx errors
4. **Active Requests** - Concurrent requests
5. **SQL Server Connections** - Active connections
6. **Redis Memory** - Memory usage
7. **System Resources** - CPU, Memory, Disk

Access Grafana at `http://localhost:3000` (default: admin/admin)

---

## Troubleshooting

### Monitoring Stack Issues

#### Prometheus Not Scraping

```bash
# Check Prometheus targets
curl http://localhost:9090/api/v1/targets | jq

# Check Prometheus configuration
curl http://localhost:9090/api/v1/status/config | jq

# Verify network connectivity
docker exec local-agent-prometheus wget -O- http://api:8000/metrics
```

#### Loki Not Receiving Logs

```bash
# Check Promtail targets
curl http://localhost:9080/targets | jq

# Test Loki ingestion
curl -H "Content-Type: application/json" -XPOST -s "http://localhost:3100/loki/api/v1/push" \
  --data-raw '{"streams": [{"stream": {"job": "test"}, "values": [["'$(date +%s)000000000'", "test log"]]}]}'

# Query recent logs
curl -G -s "http://localhost:3100/loki/api/v1/query" \
  --data-urlencode 'query={job="test"}' | jq
```

#### Grafana Dashboard Not Loading

```bash
# Check Grafana datasource health
curl -u admin:admin http://localhost:3000/api/datasources

# Test Prometheus connectivity from Grafana
docker exec local-agent-grafana wget -O- http://prometheus:9090/api/v1/query?query=up
```

### Performance Troubleshooting

```bash
# Check metric cardinality
curl http://localhost:9090/api/v1/label/__name__/values | jq

# View Prometheus TSDB stats
curl http://localhost:9090/api/v1/status/tsdb | jq

# Check Loki storage
docker exec local-agent-loki du -sh /loki/*
```

---

## Monitoring Checklist

### Setup Checklist

- [ ] Health check endpoints configured and tested
- [ ] Prometheus installed and scraping metrics
- [ ] Exporters configured (SQL Server, Redis, Node)
- [ ] Loki and Promtail installed for log aggregation
- [ ] AlertManager configured with notification channels
- [ ] Alert rules defined for critical scenarios
- [ ] Grafana installed with datasources configured
- [ ] Dashboards created for key metrics
- [ ] Retention policies configured
- [ ] Backup monitoring data

### Operational Checklist

- [ ] Daily: Review alert notifications
- [ ] Daily: Check dashboard for anomalies
- [ ] Weekly: Review slow query logs
- [ ] Weekly: Check disk space for metrics/logs
- [ ] Monthly: Review and update alert thresholds
- [ ] Monthly: Archive old monitoring data
- [ ] Quarterly: Capacity planning based on trends

---

## Next Steps

1. **Customize Alerts** - Adjust thresholds for your workload
2. **Create Runbooks** - Document response procedures for each alert
3. **Test Alerts** - Trigger test alerts to verify notification flow
4. **Optimize Retention** - Balance storage costs with retention needs
5. **Advanced Tracing** - Implement distributed tracing for complex issues

---

## Resources

- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Dashboards](https://grafana.com/grafana/dashboards/)
- [Loki Documentation](https://grafana.com/docs/loki/latest/)
- [AlertManager Configuration](https://prometheus.io/docs/alerting/latest/configuration/)
- [OpenTelemetry](https://opentelemetry.io/)

---

*Last Updated: December 2025*
