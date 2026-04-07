#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
FRONTEND_DIR="${ROOT_DIR}/frontend"

cd "${FRONTEND_DIR}"

echo "[perf] installing frontend dependencies"
npm install

echo "[perf] building production bundle"
npm run build:prod

echo "[perf] starting preview server"
npm run preview:ci > "${ROOT_DIR}/reports/lighthouse-preview.log" 2>&1 &
PREVIEW_PID=$!

cleanup() {
  if ps -p "${PREVIEW_PID}" >/dev/null 2>&1; then
    kill "${PREVIEW_PID}" >/dev/null 2>&1 || true
  fi
}
trap cleanup EXIT

for _ in $(seq 1 30); do
  if curl -fsS "http://127.0.0.1:4173" >/dev/null 2>&1; then
    break
  fi
  sleep 1
done

echo "[perf] running lighthouse"
npm run perf:lighthouse

SCORE=$(node -e "const fs=require('fs');const r=JSON.parse(fs.readFileSync('lighthouse-report.json','utf8'));const score=Math.round((r.categories.performance.score||0)*100);process.stdout.write(String(score));")
echo "[perf] Lighthouse performance score: ${SCORE}"

if [ "${SCORE}" -lt 80 ]; then
  echo "[perf] FAIL: score below target (80)"
  exit 1
fi

echo "[perf] PASS"
