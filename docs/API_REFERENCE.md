# Jan-Sunwai AI API Reference

This document reflects the current FastAPI implementation in `backend/main.py` and `backend/app/routers/*`.

## Base URLs and Versioning

- Primary API base: `http://localhost:8000`
- Versioned alias base: `http://localhost:8000/api/v1`
- Swagger UI: `/docs`

Every major router is exposed both unversioned and under `/api/v1`.

## Authentication Model

- Auth scheme: httpOnly cookie session (primary) with Bearer JWT compatibility (fallback).
- Login endpoint uses OAuth2 password form fields (`username`, `password`).
- Login sets `js_access_token` cookie; API clients may still send `Authorization: Bearer <jwt>`.
- Logout endpoint clears the auth cookie.
- Self-registration is allowed for:
  - `citizen`
  - `worker` (pending admin approval)

## Route Map

```mermaid
flowchart LR
  Client["Frontend or API Consumer"]

  Client --> U
  Client --> A
  Client --> C
  Client --> W
  Client --> N
  Client --> T
  Client --> X

  subgraph Users
    direction TB
    U["/api/v1/users"] --> U1["POST /api/v1/users/register"]
    U --> U2["POST /api/v1/users/login"]
    U --> U3["POST /api/v1/users/logout"]
    U --> U4["GET /api/v1/users/me"]
    U --> U5["PATCH /api/v1/users/me"]
    U --> U6["POST /api/v1/users/forgot-password"]
    U --> U7["POST /api/v1/users/reset-password"]
  end

  subgraph Analyze
    direction TB
    A["/api/v1/analyze"] --> A1["POST /api/v1/analyze"]
    A --> A2["POST /api/v1/analyze/regenerate"]
    A --> A3["GET /api/v1/complaints/generation/{job_id}"]
  end

  subgraph Complaints
    direction TB
    C["/api/v1/complaints"] --> C1["POST /api/v1/complaints"]
    C --> C2["GET /api/v1/complaints"]
    C --> C3["GET /api/v1/complaints/{complaint_id}"]
    C --> C4["PATCH /api/v1/complaints/{complaint_id}/status"]
    C --> C5["PATCH /api/v1/complaints/{complaint_id}/transfer"]
    C --> C6["POST /api/v1/complaints/{complaint_id}/escalate"]
    C --> C7["POST /api/v1/complaints/{complaint_id}/feedback"]
    C --> C8["POST /api/v1/complaints/{complaint_id}/notes"]
    C --> C9["GET /api/v1/complaints/{complaint_id}/notes"]
    C --> C10["POST /api/v1/complaints/{complaint_id}/comments"]
    C --> C11["GET /api/v1/complaints/{complaint_id}/comments"]
    C --> C12["POST /api/v1/complaints/bulk/status"]
    C --> C13["POST /api/v1/complaints/bulk/transfer"]
    C --> C14["GET /api/v1/complaints/export/csv"]
  end

  subgraph Workers
    direction TB
    W["/api/v1/workers"] --> W1["GET /api/v1/workers/me"]
    W --> W2["PATCH /api/v1/workers/me/status"]
    W --> W3["PATCH /api/v1/workers/me/complaints/{id}/done"]
    W --> W4["GET /api/v1/workers"]
    W --> W5["GET /api/v1/workers/my-department"]
    W --> W6["PATCH /api/v1/workers/{worker_id}/approve"]
    W --> W7["DELETE /api/v1/workers/{worker_id}/reject"]
    W --> W8["POST /api/v1/workers/{worker_id}/assign/{complaint_id}"]
    W --> W9["PATCH /api/v1/workers/{worker_id}/area"]
    W --> W10["GET /api/v1/workers/assignment-debug"]
    W --> W11["POST /api/v1/workers/reassign-unassigned"]
  end

  subgraph Notifications
    direction TB
    N["/api/v1/notifications"] --> N1["GET /api/v1/notifications"]
    N --> N2["GET /api/v1/notifications/unread-count"]
    N --> N3["PATCH /api/v1/notifications/{notification_id}/read"]
    N --> N4["PATCH /api/v1/notifications/read-all"]
  end

  subgraph Triage
    direction TB
    T["/api/v1/triage"] --> T1["GET /api/v1/triage/review-queue"]
    T --> T2["POST /api/v1/triage/review-queue/decision"]
  end

  subgraph AnalyticsPublicHealth
    direction TB
    X["/api/v1/analytics, /api/v1/public, /api/v1/health"] --> X1["GET /api/v1/analytics/overview"]
    X --> X2["GET /api/v1/analytics/heatmap"]
    X --> X3["GET /api/v1/public/complaints"]
    X --> X4["GET /api/v1/health/live"]
    X --> X5["GET /api/v1/health/ready"]
    X --> X6["GET /api/v1/health/models"]
    X --> X7["GET /api/v1/health/gpu"]
  end
```

## Endpoint Reference

## Users

| Method | Endpoint | Auth | Notes |
| --- | --- | --- | --- |
| `POST` | `/api/v1/users/register` | No | Registers `citizen` or `worker` only |
| `POST` | `/api/v1/users/login` | No | OAuth2 form login |
| `POST` | `/api/v1/users/logout` | No | Clears auth cookie if present |
| `GET` | `/api/v1/users/me` | Yes | Returns current user profile |
| `PATCH` | `/api/v1/users/me` | Yes | Updates `full_name` and/or `phone_number` |
| `POST` | `/api/v1/users/forgot-password` | No | Always generic response; no account enumeration |
| `POST` | `/api/v1/users/reset-password` | No | Uses reset token |

## Analyze + Draft

| Method | Endpoint | Auth | Notes |
| --- | --- | --- | --- |
| `POST` | `/api/v1/analyze` | Yes | Upload image + optional language; returns classification + location + draft status |
| `POST` | `/api/v1/analyze/regenerate` | Yes | Re-queues draft generation for existing analyzed image |
| `GET` | `/api/v1/complaints/generation/{job_id}` | Yes | Poll queued generation result |

## Complaints

| Method | Endpoint | Auth | Notes |
| --- | --- | --- | --- |
| `POST` | `/api/v1/complaints` | Yes | Creates complaint from analyzed payload (supports `analysis_token`) |
| `GET` | `/api/v1/complaints` | Yes | Role-filtered listing |
| `GET` | `/api/v1/complaints/{complaint_id}` | Yes | Complaint details |
| `PATCH` | `/api/v1/complaints/{complaint_id}/status` | Admin/Dept Head | Appends `status_history` and triggers notification/email |
| `PATCH` | `/api/v1/complaints/{complaint_id}/transfer` | Admin/Dept Head | Department override transfer |
| `POST` | `/api/v1/complaints/{complaint_id}/escalate` | Admin/Dept Head | Escalates authority level |
| `POST` | `/api/v1/complaints/{complaint_id}/feedback` | Citizen owner | One-time post-resolution feedback |
| `POST` | `/api/v1/complaints/{complaint_id}/notes` | Admin/Dept Head | Internal department notes |
| `GET` | `/api/v1/complaints/{complaint_id}/notes` | Admin/Dept Head | Fetch internal notes |
| `POST` | `/api/v1/complaints/{complaint_id}/comments` | Yes | Shared complaint thread |
| `GET` | `/api/v1/complaints/{complaint_id}/comments` | Yes | Shared complaint thread |
| `POST` | `/api/v1/complaints/bulk/status` | Admin | Bulk status update |
| `POST` | `/api/v1/complaints/bulk/transfer` | Admin | Bulk department transfer |
| `GET` | `/api/v1/complaints/export/csv` | Admin | CSV export |

## Workers

| Method | Endpoint | Auth | Notes |
| --- | --- | --- | --- |
| `GET` | `/api/v1/workers/me` | Worker | Profile + active + resolved history |
| `PATCH` | `/api/v1/workers/me/status` | Worker | Only `available`/`offline` allowed manually |
| `PATCH` | `/api/v1/workers/me/complaints/{id}/done` | Worker | Marks complaint resolved and frees slot |
| `GET` | `/api/v1/workers` | Admin | Lists workers; supports `pending_only` |
| `GET` | `/api/v1/workers/my-department` | Admin/Dept Head | Department-scoped workers |
| `PATCH` | `/api/v1/workers/{worker_id}/approve` | Admin | Approves worker account |
| `DELETE` | `/api/v1/workers/{worker_id}/reject` | Admin | Rejects pending worker registration |
| `POST` | `/api/v1/workers/{worker_id}/assign/{complaint_id}` | Admin | Manual assignment override |
| `PATCH` | `/api/v1/workers/{worker_id}/area` | Admin | Updates worker service area |
| `GET` | `/api/v1/workers/assignment-debug` | Admin | Assignment diagnostics |
| `POST` | `/api/v1/workers/reassign-unassigned` | Admin | Bulk auto-assignment retry |

## Notifications

| Method | Endpoint | Auth | Notes |
| --- | --- | --- | --- |
| `GET` | `/api/v1/notifications` | Yes | List notifications (`skip`, `limit`, `unread_only`) |
| `GET` | `/api/v1/notifications/unread-count` | Yes | Badge counter |
| `PATCH` | `/api/v1/notifications/{notification_id}/read` | Yes | Mark single as read |
| `PATCH` | `/api/v1/notifications/read-all` | Yes | Mark all as read |

## Triage

| Method | Endpoint | Auth | Notes |
| --- | --- | --- | --- |
| `GET` | `/api/v1/triage/review-queue` | Admin | Live low-confidence complaints from MongoDB |
| `POST` | `/api/v1/triage/review-queue/decision` | Admin | Decision payload fields: `image`, `decision`, optional `corrected_label`, `note` |

## Analytics + Public + Health

| Method | Endpoint | Auth | Notes |
| --- | --- | --- | --- |
| `GET` | `/api/v1/analytics/overview` | Admin | Status, department, trend, resolution stats |
| `GET` | `/api/v1/analytics/heatmap` | Admin/Dept Head | Geospatial aggregate points |
| `GET` | `/api/v1/public/complaints` | No | Anonymized public complaint feed |
| `GET` | `/api/v1/health/live` | No | Liveness probe |
| `GET` | `/api/v1/health/ready` | No | DB readiness probe |
| `GET` | `/api/v1/health/models` | No | Ollama model readiness |
| `GET` | `/api/v1/health/gpu` | No | Active model GPU/VRAM status |

## Request Examples

### Login

```http
POST /api/v1/users/login
Content-Type: application/x-www-form-urlencoded

username=<your_username>&password=<your_password>
```

### Analyze

```http
POST /api/v1/analyze
Content-Type: multipart/form-data

file=<image>
language=en
```

### Authentication Usage

Browser clients should use the cookie session set by `/api/v1/users/login`.

```http
GET /api/v1/complaints
Cookie: js_access_token=<jwt>
```

API clients can still use the compatibility bearer header:

```http
GET /api/v1/complaints
Authorization: Bearer <jwt>
```

### Create Complaint

```json
{
  "description": "Streetlight is non-functional and the area is dark at night.",
  "department": "Electrical Department",
  "image_url": "uploads/xxxxx.jpg",
  "location": {
    "lat": 28.6139,
    "lon": 77.2090,
    "address": "Connaught Place, New Delhi",
    "source": "manual"
  },
  "ai_metadata": {
    "model_used": "qwen2.5vl:3b",
    "confidence_score": 0.88,
    "detected_department": "Electrical Department",
    "labels": ["street light", "dark road"]
  },
  "analysis_token": "<optional-analysis-bind-token>"
}
```

### Triage Decision

```json
{
  "image": "<complaint_id_or_image_path>",
  "decision": "approve",
  "corrected_label": "Civil Department",
  "note": "Manual override after review"
}
```

## Analyze Response Notes

`POST /api/v1/analyze` includes:

- `classification`: department decision + confidence + model metadata
- `location`: EXIF-derived or fallback result
- `generated_complaint`: drafted text, queued placeholder, or fallback text
- `generation_status`: `completed`, `queued`, `failed`, or `skipped`
- `generation_job_id`: poll key for queued generation
- `analysis_token`: binding token for secure `/api/v1/complaints` creation flow
- `timings`: `vision_ms`, `rule_engine_ms`, `reasoning_ms`, `total_analyze_ms`

## Error Semantics

| Status | Typical Cases |
| --- | --- |
| `400` | Validation errors, invalid ID format, malformed payload |
| `401` | Missing/invalid token or bad login |
| `403` | Role not permitted or worker pending approval |
| `404` | Missing resource or job ID |
| `409` | Conflict (for example duplicate feedback or already-approved worker) |
| `413` | Upload exceeds max allowed size |
| `429` | Rate-limited endpoint |
| `503` | AI pipeline temporarily unavailable |

## Notes for Integrators

- `VITE_API_URL` in `frontend/.env` defaults to `http://localhost:8000/api/v1` for local development.
- In production Docker builds, override via `--build-arg VITE_API_URL=/api/v1` (relative URL, routed through nginx).
- Nginx must proxy `/api/*` to the backend service AND serve `/uploads/*` from the backend static mount.
- Static uploaded images are served at `/uploads/<filename>` — **not** under `/api/v1`.
- New browser integrations should rely on cookie auth; bearer headers are compatibility-only.
- Worker registration does not auto-login; worker must be approved by admin first.
- Bold markers (`**text**`) in generated complaint emails are rendered by `FormattedComplaintText.jsx` as `<strong>` for all supported languages including translated output.
