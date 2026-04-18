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
  echo "[deploy-sim] FAIL: backend/.env is missing."
  echo "[deploy-sim] Create backend/.env before running deployment simulation."
  exit 1
fi

echo "[deploy-sim] validating compose config"
docker compose --profile prod config -q

echo "[deploy-sim] measuring cold start"
START=$(date +%s)
docker compose --profile prod up -d --build
END=$(date +%s)
ELAPSED=$((END - START))
echo "[deploy-sim] cold-start seconds: ${ELAPSED}"

curl -fsS http://localhost:8000/api/v1/health/live >/dev/null
curl -fsS http://localhost:5173 >/dev/null

echo "[deploy-sim] PASS"
