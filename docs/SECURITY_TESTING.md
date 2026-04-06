# Security Testing Notes

## Automated Checks Added

Run from the backend directory:

```bash
pytest tests/test_resilience_security.py tests/test_notification_chain.py -q
```

The suite validates:

- Malicious upload content is blocked by magic-number validation.
- `/analyze` degrades gracefully with HTTP 503 when classifier/model pipeline fails.
- `/health/ready` reports degraded mode when MongoDB ping fails.
- XSS payloads are escaped by sanitization utilities.
- Status-update notification chain triggers one in-app notification and one email event.
- `mark-all-read` clears unread badge counts.

## Manual Security Probes

Recommended curl probes:

1. JWT tampering:
```bash
curl -H "Authorization: Bearer invalid.token.here" http://localhost:8000/complaints
```
Expect `401`.

2. Malicious file spoofing:
```bash
curl -X POST http://localhost:8000/analyze \
  -H "Authorization: Bearer <token>" \
  -F "file=@fake.jpg" \
  -F "language=en"
```
Expect `400` for header mismatch.

3. XSS payload in note/feedback/comment:
- Submit payload containing `<script>` and verify rendered output is escaped.

## Outstanding External Validation

- Full penetration testing with an external scanner (OWASP ZAP/Burp) is still recommended before production handover.
- Infra-level checks (TLS policy, reverse proxy hardening, host firewall rules) must be executed on the deployment environment.
