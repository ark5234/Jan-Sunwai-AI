#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
HOST="${1:-http://localhost:8000}"
USERS="${USERS:-70}"
SPAWN_RATE="${SPAWN_RATE:-10}"
DURATION="${DURATION:-15m}"

STAMP="$(date +%Y%m%d_%H%M%S)"
OUT_DIR="${ROOT_DIR}/reports/load/${STAMP}"

mkdir -p "${OUT_DIR}"

cd "${ROOT_DIR}/backend"

python -m pip install -r requirements-loadtest.txt
python -m locust -f locustfile.py \
	--host "${HOST}" \
	--headless \
	-u "${USERS}" \
	-r "${SPAWN_RATE}" \
	-t "${DURATION}" \
	--html "${OUT_DIR}/locust-report.html" \
	--csv "${OUT_DIR}/locust" \
	--only-summary

echo "[load-test] report generated at: ${OUT_DIR}"
