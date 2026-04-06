# NDMC Deployment Guide

Before this production runbook, complete local bootstrap from the Quick Start in [README.md](../README.md).

## 1. Prerequisites

- Ubuntu 22.04+
- Docker 24+
- Docker Compose v2
- NVIDIA GPU + drivers if Ollama runs locally
- Ollama runtime reachable from backend

## 2. Configure Environment

1. Copy backend env template: `cp backend/env.production backend/.env`
2. Set required values: JWT_SECRET_KEY, ALLOWED_ORIGINS, OLLAMA_BASE_URL, RATE_LIMIT_ENABLED=true, SMTP_HOST, SMTP_PORT, SMTP_FROM

## 3. Start Production Stack

- docker compose -f docker-compose.prod.yml up --build -d
- Frontend serves the SPA on port 5173 and proxies `/api/*` to backend service.

## 3.1 Initialize Database Indexes

- python backend/create_indexes.py

## 4. Health Checks

- Backend health:
  - GET /health/live
- Frontend:
  - Open port 5173
- MongoDB:
  - service health in compose output

## 5. Backup and Recovery

- Backup command:
  - bash scripts/backup_db.sh
  - powershell -ExecutionPolicy Bypass -File scripts/backup_db.ps1
- Restore:
  - mongorestore --uri=$MONGO_URI /path/to/backup-folder
- Recommended NDMC schedule:
  - Daily backup at off-peak time (e.g. 02:00)
  - Retain last 30 daily snapshots

## 6. Common Troubleshooting

- Ollama unavailable:
  - verify OLLAMA_BASE_URL
  - verify host firewall and port 11434
- JWT auth failures:
  - verify JWT_SECRET_KEY consistency across restarts
- CORS failures:
  - verify ALLOWED_ORIGINS includes frontend domain
- Rate limiter module errors (`No module named slowapi`):
  - rebuild backend image after dependency updates
  - for local/dev fallback, set `RATE_LIMIT_ENABLED=false`

## 7. Related Operational Guides

- Load testing: [LOAD_TESTING.md](LOAD_TESTING.md)
- Security validation: [SECURITY_TESTING.md](SECURITY_TESTING.md)
- Production rollout plan: [PRODUCTION_DEPLOYMENT_PLAN.md](PRODUCTION_DEPLOYMENT_PLAN.md)
