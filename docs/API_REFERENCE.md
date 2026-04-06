# API Reference (Core)

## Auth

- POST /users/register
- POST /users/login
- GET /users/me
- PATCH /users/me
- POST /users/forgot-password
- POST /users/reset-password

Example: Login request

```http
POST /users/login
Content-Type: application/x-www-form-urlencoded

username=citizen1&password=secret123
```

Example: Login success response

```json
{
  "access_token": "<jwt>",
  "token_type": "bearer",
  "username": "citizen1",
  "role": "citizen"
}
```

## Analyze and Draft

- POST /analyze
- POST /analyze/regenerate
- GET /complaints/generation/{job_id}

Example: Analyze success response (truncated)

```json
{
  "department": "Municipal - Street Lighting",
  "confidence": 0.89,
  "generated_complaint": "Subject: Complaint Regarding Streetlight Outage...",
  "timings": {
    "vision_ms": 782.14,
    "rule_engine_ms": 4.22,
    "reasoning_ms": 0,
    "total_analyze_ms": 1021.33
  }
}
```

Example: Analyze temporary failure

```json
{
  "message": "AI analysis unavailable — please try again in a few minutes.",
  "details": "Model pipeline unavailable",
  "retryable": true
}
```

## Complaints

- POST /complaints
- GET /complaints
- GET /complaints/{complaint_id}
- PATCH /complaints/{complaint_id}/status
- PATCH /complaints/{complaint_id}/transfer
- POST /complaints/{complaint_id}/feedback
- POST /complaints/{complaint_id}/notes
- GET /complaints/{complaint_id}/notes
- POST /complaints/{complaint_id}/comments
- GET /complaints/{complaint_id}/comments
- POST /complaints/bulk/status
- POST /complaints/bulk/transfer
- GET /complaints/export/csv

## Notifications

- GET /notifications
- GET /notifications/unread-count
- PATCH /notifications/{notification_id}/read
- PATCH /notifications/read-all

## Versioned Alias

- All core routes are also exposed under /api/v1 prefix.

## Timing Metadata

Analyze responses include:

- timings.vision_ms
- timings.rule_engine_ms
- timings.reasoning_ms
- timings.total_analyze_ms

## Graceful AI Failure

If AI analysis backend is unavailable, /analyze returns HTTP 503 with retryable=true.

## Common Error Codes

- 400: invalid payload or malformed request body
- 401: missing or invalid JWT token
- 403: role/access violation
- 404: requested complaint/user/notification not found
- 413: image upload exceeds configured size limit
- 429: rate limit exceeded
- 503: AI model pipeline temporarily unavailable
