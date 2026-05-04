# Load Testing Guide

This runbook is aligned with `backend/locustfile.py` and `scripts/run_load_test.*`.

## Objective

Validate the behavior of:

- Public feed endpoint under read-heavy load.
- Health endpoint baseline responsiveness.
- Notification badge endpoint with auth.
- Analyze endpoint behavior under inference pressure.

## Scenario Topology

```mermaid
flowchart LR
    Locust[Locust Workers] --> API[FastAPI Backend]
    API --> Mongo[(MongoDB)]
    API --> Ollama[Ollama Models]

    Locust -->|/api/v1/users/login| API
    Locust -->|/api/v1/public/api/v1/complaints| API
    Locust -->|/api/v1/health/live| API
    Locust -->|/api/v1/notifications/unread-count| API
    Locust -->|/api/v1/analyze multipart| API
```

## Endpoint Mix (Current Locust Tasks)

Task weights in `locustfile.py`:

- `4` -> `GET /api/v1/public/api/v1/complaints`
- `3` -> `GET /api/v1/health/live`
- `2` -> `GET /api/v1/notifications/unread-count` (authenticated request)
- `1` -> `POST /api/v1/analyze` (multipart image upload)

## Acceptance Rules in Locust Script

- `GET /api/v1/public/api/v1/complaints` must return `200`.
- `GET /api/v1/health/live` must return `200`.
- `GET /api/v1/notifications/unread-count` accepts `200` or `401`.
- `POST /api/v1/analyze` accepts `200`, `429`, or `503`.

`429` and `503` on `/api/v1/analyze` are treated as controlled degradation under pressure.

## Prerequisites

1. Backend and MongoDB running.
2. Ollama running with configured models.
3. At least one test citizen account available for login.
4. Python dependencies for load testing installed.

## Run Commands

### Linux/macOS

```bash
bash scripts/run_load_test.sh http://localhost:8000
```

### Windows

```bat
scripts\run_load_test.bat http://localhost:8000
```

### Windows (PowerShell)

```powershell
powershell -ExecutionPolicy Bypass -File scripts/run_load_test.ps1 http://localhost:8000
```

### Direct Locust command

```bash
cd backend
python -m pip install -r requirements-loadtest.txt
locust -f locustfile.py --host http://localhost:8000
```

Open Locust UI at `http://localhost:8089`.

Headless mode note:

- Current run scripts execute locust in headless mode and save timestamped reports under `reports/load/<timestamp>/`.

## Optional Credentials

Set environment variables if default credentials are different:

- `LOCUST_CITIZEN_USERNAME`
- `LOCUST_CITIZEN_PASSWORD`

Note:

- The application is cookie-first for browser clients, but the current locust script still uses bearer compatibility from login response.
- If your runtime does not return `access_token` in login responses, either enable compatibility (`RETURN_ACCESS_TOKEN_IN_RESPONSE=true`) for load runs, or update `backend/locustfile.py` to use cookie sessions only.

Example:

```bash
export LOCUST_CITIZEN_USERNAME=citizen_demo
export LOCUST_CITIZEN_PASSWORD=citizen123
```

## Suggested Test Matrix

| Profile | Users | Spawn Rate | Duration | Purpose |
| --- | --- | --- | --- | --- |
| Smoke | 20 | 5/s | 5 min | Quick baseline verification |
| Baseline | 70 | 10/s | 15 min | Typical stress profile |
| Peak | 120 | 20/s | 20 min | Degradation and recovery behavior |

## Capture Checklist

For each run, record:

1. P95 and P99 latency per endpoint.
2. Request throughput (req/s).
3. Failure rate by endpoint and status code.
4. `/api/v1/analyze` distribution of `200`, `429`, `503`.
5. CPU/RAM for backend and MongoDB.
6. Model response behavior (slow vs unavailable windows).

## Result Interpretation

```mermaid
flowchart TD
    Start[Run Finished] --> A{High /api/v1/analyze 503?}
    A -->|Yes| A1[Check Ollama process and model availability]
    A -->|No| B{High /api/v1/analyze 429?}
    B -->|Yes| B1[Rate limiting reached; tune limits or worker count]
    B -->|No| C{High p95 on public/api/v1/health?}
    C -->|Yes| C1[Investigate backend and MongoDB bottlenecks]
    C -->|No| D[Run considered stable for tested profile]
```

## Notes

- Production and local runs can differ significantly depending on `APP_ENV` and `RATE_LIMIT_ENABLED`.
- If using production frontend with `VITE_API_URL=/api/v1`, test host should still point to backend gateway where `/api/*` is proxied correctly.
