# Performance Testing Quickstart

## Setup

1. Install dependencies (if not already installed):
```bash
uv sync
```

2. Start the FastAPI backend:
```bash
uv run uvicorn src.api.main:app --host 0.0.0.0 --port 8000
```

## Run Performance Tests

### Option 1: Web UI (Recommended for Development)

```bash
cd E:/Repos/GitHub/MyDemoRepos/local-llm-research-agent
uv run locust -f tests/performance/locustfile.py --host=http://localhost:8000
```

Then open http://localhost:8089 in your browser and configure:
- Number of users: 10 (start small)
- Spawn rate: 2 users/second
- Host: http://localhost:8000 (pre-filled)

Click "Start swarming" and watch real-time metrics!

### Option 2: Headless Mode (CI/CD)

Quick 1-minute load test:
```bash
uv run locust -f tests/performance/locustfile.py \
  --host=http://localhost:8000 \
  --users 10 \
  --spawn-rate 2 \
  --run-time 1m \
  --headless
```

Extended 5-minute load test with HTML report:
```bash
uv run locust -f tests/performance/locustfile.py \
  --host=http://localhost:8000 \
  --users 50 \
  --spawn-rate 5 \
  --run-time 5m \
  --headless \
  --html=tests/performance/report.html
```

## Understanding Results

### Key Metrics

- **RPS (Requests/s)**: Higher is better
- **Response Time p50**: Median response time (50% of requests faster)
- **Response Time p95**: 95th percentile (95% of requests faster)
- **Response Time p99**: 99th percentile (99% of requests faster)
- **Failure Rate**: Should be < 1%

### Example Good Results

```
Type     Name                    # reqs  # fails  Avg    Min    Max    Median p95    p99   req/s
GET      /api/health             3000    0        15     5      120    12     35     58    50.0
GET      /api/conversations      2000    0        85     30     450    75     180    290   33.3
POST     /api/agent/chat         1000    2        1200   450    5000   1100   2500   3800  16.7
```

### Warning Signs

- p95 > 2x p50 (high variance)
- Increasing response times over duration (memory leak?)
- Failure rate > 5% (backend issues)
- RPS dropping over time (resource exhaustion)

## User Classes

### ResearchAgentUser
Simulates normal user workflow:
- 30% health checks
- 20% list conversations
- 20% list documents
- 10% chat requests
- 10% document search

### DashboardUser
Simulates dashboard/monitoring:
- 70% list dashboards
- 30% get settings

## Customization

Edit `tests/performance/locustfile.py` to:
- Add new endpoints
- Change task weights
- Adjust wait times
- Add authentication
- Test specific scenarios

## Common Issues

### Port 8089 in use
```bash
uv run locust -f tests/performance/locustfile.py \
  --host=http://localhost:8000 \
  --web-port=8090
```

### API not responding
1. Check API is running: `curl http://localhost:8000/api/health`
2. Check logs: `docker logs local-agent-api` (if using Docker)
3. Verify firewall settings

### High error rates
1. Reduce user count: `--users 5`
2. Reduce spawn rate: `--spawn-rate 1`
3. Check backend logs for errors
4. Verify database connections
