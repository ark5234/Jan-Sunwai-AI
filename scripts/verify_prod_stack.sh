#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "${ROOT_DIR}"

echo "[prod-verify] bringing up production compose stack"
docker compose --profile prod up -d --build

echo "[prod-verify] checking backend live endpoint"
for _ in $(seq 1 20); do
  if curl -fsS http://localhost:8000/api/v1/health/live >/dev/null 2>&1; then
    break
  fi
  sleep 2
done
curl -fsS http://localhost:8000/api/v1/health/live >/dev/null

echo "[prod-verify] checking SPA deep-link fallback"
STATUS=$(curl -o /tmp/jan_sunwai_deeplink.html -s -w "%{http_code}" http://localhost:5173/dashboard)
if [ "${STATUS}" != "200" ]; then
  echo "[prod-verify] FAIL: SPA deep link returned ${STATUS}"
  exit 1
fi
if ! grep -iq "<html" /tmp/jan_sunwai_deeplink.html; then
  echo "[prod-verify] FAIL: SPA deep link did not return HTML"
  exit 1
fi

echo "[prod-verify] checking backend-to-ollama network route"
docker compose --profile prod exec -T backend python -c "import os,urllib.request;u=os.getenv('OLLAMA_BASE_URL','http://host.docker.internal:11434').rstrip('/')+'/api/tags';urllib.request.urlopen(u,timeout=5);print('ok')"

echo "[prod-verify] running short load smoke against production stack"
USERS=${USERS:-20} SPAWN_RATE=${SPAWN_RATE:-5} DURATION=${DURATION:-2m} bash scripts/run_load_test.sh http://localhost:8000

echo "[prod-verify] PASS"
