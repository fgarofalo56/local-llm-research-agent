# Performance Tests

## Prerequisites
- Install Locust: `uv add locust`
- API running: `uv run uvicorn src.api.main:app --host 0.0.0.0 --port 8000`

## Running Tests

### Web UI Mode
```bash
locust -f tests/performance/locustfile.py --host=http://localhost:8000
```

Open http://localhost:8089 to configure and run tests.

### Headless Mode (CI)
```bash
locust -f tests/performance/locustfile.py \
  --host=http://localhost:8000 \
  --users 10 \
  --spawn-rate 2 \
  --run-time 1m \
  --headless
```

## Metrics
- RPS: Requests per second
- Response Time: p50, p95, p99
- Error Rate: % of failed requests

## User Classes

### ResearchAgentUser
Simulates typical user interactions with the research agent:
- Health checks (weight: 3)
- List conversations (weight: 2)
- List documents (weight: 2)
- Chat requests (weight: 1)
- Document search (weight: 1)

### DashboardUser
Simulates dashboard viewing patterns:
- List dashboards (weight: 5)
- Get settings (weight: 2)

## Example Results Interpretation

### Good Performance
- Health endpoint: < 50ms (p95)
- List endpoints: < 200ms (p95)
- Chat requests: < 2000ms (p95)
- Error rate: < 1%

### Performance Degradation
- Response times increasing over test duration
- Error rate > 5%
- Failed connection errors

## Troubleshooting

### Connection Errors
- Ensure API is running on port 8000
- Check firewall settings
- Verify `--host` parameter matches API URL

### High Error Rates
- Check API logs for errors
- Verify database connections
- Check resource usage (CPU, memory)
- Reduce user count or spawn rate

### Slow Response Times
- Monitor system resources
- Check database performance
- Profile slow endpoints
- Consider caching strategies
