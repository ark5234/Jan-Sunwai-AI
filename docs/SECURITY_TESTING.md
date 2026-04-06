# Security Testing Guide

This guide reflects currently implemented controls and testable behaviors in the backend and frontend.

## Security Control Coverage

| Control Area | Current Implementation |
| --- | --- |
| Authentication | JWT bearer via OAuth2 password flow |
| Authorization | Role-gated dependencies (`citizen`, `worker`, `dept_head`, `admin`) |
| Password Storage | bcrypt hash via passlib |
| Reset Tokens | SHA-256 hashed token storage + TTL index |
| Upload Security | Extension allowlist + max size + magic number check |
| Input Sanitization | HTML escaping and text sanitization on user-provided fields |
| Headers | CSP, X-Frame-Options, Referrer-Policy, HSTS (prod), etc. |
| CORS | Configurable allowlist from env |
| Rate Limiting | Optional slowapi integration (`RATE_LIMIT_ENABLED`) |
| Notification Safety | User-scoped read/update actions |

## Threat Surface Map

```mermaid
flowchart LR
    User[Browser Client] --> API[FastAPI]
    API --> DB[(MongoDB)]
    API --> FS[Upload Storage]
    API --> OLLAMA[Ollama Runtime]
    API --> SMTP[SMTP Relay]

    Threat1[Token theft/forgery] --> API
    Threat2[Malicious upload payload] --> FS
    Threat3[XSS payloads] --> API
    Threat4[Privilege escalation] --> API
    Threat5[Resource exhaustion] --> API
```

## Automated Tests

Run from `backend`:

```bash
pytest tests/test_resilience_security.py tests/test_notification_chain.py -q
```

Covered checks include:

- Upload magic-number mismatch rejection.
- Graceful `/analyze` `503` behavior on classifier failure.
- `/health/ready` degraded response when DB ping fails.
- Sanitization of script payloads.
- Notification chain behavior for status updates.
- Mark-all-read unread-counter behavior.

## Manual Security Probes

## 1) JWT Validation

```bash
curl -H "Authorization: Bearer invalid.token.here" http://localhost:8000/complaints
```

Expected: `401`

## 2) Role Access Enforcement

Try admin-only endpoint with non-admin token:

```bash
curl -H "Authorization: Bearer <citizen-token>" http://localhost:8000/workers
```

Expected: `403`

## 3) Upload Magic Number Validation

Upload mismatched extension/content:

```bash
curl -X POST http://localhost:8000/analyze \
  -H "Authorization: Bearer <token>" \
  -F "file=@fake.jpg" \
  -F "language=en"
```

Expected: `400` with header mismatch message.

## 4) XSS Sanitization

Inject script payload in complaint note or comment body and verify escaped output is returned (for example `&lt;script&gt;`).

## 5) Notification Ownership

Call `PATCH /notifications/{id}/read` with another user's notification ID.

Expected: `404` (not found for current user scope).

## 6) Rate Limit Behavior (if enabled)

Burst request to limited endpoints and verify `429` responses.

## Test Workflow

```mermaid
flowchart TD
    A[Start Test Session] --> B[Run automated pytest security suite]
    B --> C[Execute manual auth and role probes]
    C --> D[Execute upload and XSS probes]
    D --> E[Capture logs and HTTP codes]
    E --> F[Classify findings by severity]
    F --> G[Patch and re-run impacted tests]
```

## Security Headers Checklist

Validate these response headers on API responses:

- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `Referrer-Policy: strict-origin-when-cross-origin`
- `Permissions-Policy: geolocation=(), microphone=(), camera=()`
- `Content-Security-Policy` present
- `Strict-Transport-Security` present in production mode

## Release Gate Recommendations

Before production handover:

1. Run this security checklist against the production URL.
2. Execute external scanner pass (OWASP ZAP or Burp suite).
3. Validate TLS policy, reverse-proxy hardening, and firewall rules.
4. Verify secrets management and non-default `JWT_SECRET_KEY`.
5. Confirm `ALLOWED_ORIGINS` is locked to deployment domains.
