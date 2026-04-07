#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "${ROOT_DIR}"

require_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "[deploy-sim] missing required command: $1"
    exit 1
  fi
}

echo "[deploy-sim] validating prerequisites"
require_cmd git
require_cmd docker
require_cmd python
require_cmd node
require_cmd npm

if [ ! -f backend/.env ]; then
  echo "[deploy-sim] backend/.env missing; copying from env.production"
  cp backend/env.production backend/.env
fi

echo "[deploy-sim] validating compose config"
docker compose -f docker-compose.prod.yml config -q

echo "[deploy-sim] measuring cold start"
START=$(date +%s)
docker compose -f docker-compose.prod.yml up -d --build
END=$(date +%s)
ELAPSED=$((END - START))
echo "[deploy-sim] cold-start seconds: ${ELAPSED}"

curl -fsS http://localhost:8000/health/live >/dev/null
curl -fsS http://localhost:5173 >/dev/null

echo "[deploy-sim] PASS"
