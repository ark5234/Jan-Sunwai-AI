# Load Testing Guide (Locust)

## Setup

Install load-test dependencies:

```bash
pip install -r backend/requirements-loadtest.txt
```

## Run

From the backend directory:

```bash
locust -f locustfile.py --host http://localhost:8000
```

Open Locust UI (default: http://localhost:8089) and use baseline target:

- Users: 70
- Spawn rate: 10/s

Suggested split:

- 50 virtual users representing citizen flows
- 20 virtual users generating analyze uploads

## Environment Variables

Optional credentials for load users:

- `LOCUST_CITIZEN_USERNAME`
- `LOCUST_CITIZEN_PASSWORD`

## What Is Measured

The scenario includes:

- `GET /public/complaints`
- `GET /health/live`
- `GET /notifications/unread-count`
- `POST /analyze` with JPEG payloads

Treat `429` and `503` on `/analyze` as controlled degradation under pressure.

## Report Template

Capture the following after each run:

- P95 latency for `/analyze` and `/public/complaints`
- Request failure ratio
- Throughput (req/s)
- Observed `429` and `503` rates
- MongoDB CPU/RAM and slow query indicators
- Queueing behavior in the AI generation pipeline
