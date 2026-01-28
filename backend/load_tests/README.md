# Load Testing Suite for FaceMortgage

This directory contains load testing scenarios using Locust.

## Installation

```bash
pip install locust faker
```

## Running Tests

### Interactive UI Mode
```bash
cd backend/load_tests
locust -f locustfile.py --host=http://localhost:8000
```
Then open http://localhost:8089 in your browser.

### Headless Mode
```bash
cd backend/load_tests
locust -f locustfile.py --host=http://localhost:8000 \
    --headless \
    --users=100 \
    --spawn-rate=10 \
    --run-time=60s
```

## Test Scenarios

| Scenario | Description | Target RPS |
|----------|-------------|------------|
| `grid_browsing.py` | Grid browsing and filtering | 100+ |
| `call_flow.py` | Call initiation flow | 50+ |
| `auth_flow.py` | Login/register | 30+ |
| `api_stress.py` | API endpoint stress | 200+ |

## Configuration

Set environment variables for authentication:
```bash
export TEST_USER_EMAIL="test@example.com"
export TEST_USER_PASSWORD="testpassword123"
```

## Performance Targets

| Endpoint | P95 Response Time | Target RPS |
|----------|-------------------|------------|
| GET /grid | < 200ms | 100 |
| GET /professionals/:id | < 150ms | 50 |
| POST /calls/request | < 500ms | 20 |
| GET /dashboard | < 300ms | 30 |
