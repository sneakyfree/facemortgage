# FaceMortgage Load Testing

This directory contains load testing scripts for the FaceMortgage API using [Locust](https://locust.io/).

## Prerequisites

Install Locust:

```bash
pip install locust
```

## Running Load Tests

### Interactive Mode (Web UI)

Start Locust with the web interface:

```bash
cd backend
locust -f tests/load/locustfile.py --host=http://localhost:8000
```

Then open http://localhost:8089 in your browser to configure and run the test.

### Headless Mode (CLI)

Run a test directly from the command line:

```bash
# Run with 100 users, spawning 10 per second, for 5 minutes
locust -f tests/load/locustfile.py --host=http://localhost:8000 \
    --headless -u 100 -r 10 --run-time 5m
```

### Distributed Mode

For higher load, run multiple workers:

```bash
# Start master
locust -f tests/load/locustfile.py --master

# Start workers (on same or different machines)
locust -f tests/load/locustfile.py --worker --master-host=localhost
```

## User Types

The load test simulates different user behaviors:

| User Type | Weight | Description |
|-----------|--------|-------------|
| BorrowerUser | 10 | Browses grid, filters, views profiles |
| ProfessionalUser | 2 | Checks dashboard, updates status |
| DataProviderUser | 3 | Requests professional stats |
| HealthCheckUser | 1 | Simulates load balancer probes |

## Performance Targets

Based on the application requirements:

| Endpoint | P50 Target | P95 Target | P99 Target |
|----------|------------|------------|------------|
| GET /api/v1/grid | 50ms | 150ms | 300ms |
| GET /api/v1/professionals/{id} | 30ms | 100ms | 200ms |
| POST /api/v1/calls/initiate | 100ms | 300ms | 500ms |
| GET /health/ready | 50ms | 100ms | 200ms |

## Interpreting Results

### Key Metrics

- **RPS (Requests Per Second)**: Total throughput
- **Response Time**: P50, P95, P99 percentiles
- **Failure Rate**: Should be < 0.1% under normal load
- **Users**: Number of concurrent users simulated

### Warning Signs

- P95 response times > 500ms indicate performance issues
- Failure rate > 1% suggests capacity limits reached
- Increasing response times over test duration = potential memory leak

## Test Scenarios

### Smoke Test
Quick validation that the system handles basic load:
```bash
locust -f tests/load/locustfile.py --host=http://localhost:8000 \
    --headless -u 10 -r 2 --run-time 1m
```

### Load Test
Normal expected traffic:
```bash
locust -f tests/load/locustfile.py --host=http://localhost:8000 \
    --headless -u 100 -r 10 --run-time 10m
```

### Stress Test
Push beyond expected limits:
```bash
locust -f tests/load/locustfile.py --host=http://localhost:8000 \
    --headless -u 500 -r 50 --run-time 15m
```

### Soak Test
Extended duration to find memory leaks:
```bash
locust -f tests/load/locustfile.py --host=http://localhost:8000 \
    --headless -u 50 -r 5 --run-time 2h
```

## CI/CD Integration

Add to your CI pipeline:

```yaml
load-test:
  stage: test
  script:
    - pip install locust
    - locust -f tests/load/locustfile.py --host=$API_URL \
        --headless -u 50 -r 10 --run-time 5m \
        --csv=results --html=report.html
  artifacts:
    paths:
      - results*.csv
      - report.html
```

## Customizing Tests

### Adding New Endpoints

Add new tasks to the appropriate user class:

```python
@task(weight)
def my_new_task(self):
    with self.client.get("/api/v1/new-endpoint", catch_response=True) as response:
        if response.status_code == 200:
            response.success()
        else:
            response.failure(f"Failed with {response.status_code}")
```

### Testing Authenticated Endpoints

For endpoints requiring authentication, add login in `on_start`:

```python
def on_start(self):
    response = self.client.post("/api/v1/auth/login", json={
        "email": "test@example.com",
        "password": "testpassword"
    })
    # Token will be stored in cookies automatically
```

## Troubleshooting

### Tests fail to start
- Ensure the API server is running
- Check the `--host` URL is correct

### All requests fail
- Check API server logs for errors
- Verify network connectivity
- Check if rate limiting is blocking requests

### High response times
- Check database connection pool settings
- Monitor CPU and memory on server
- Look for slow database queries
