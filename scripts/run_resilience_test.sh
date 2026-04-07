#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "${ROOT_DIR}"

export PYTHONPATH="${ROOT_DIR}/backend"

echo "[resilience] running resilience/security pytest suite"
python -m pytest backend/tests/test_resilience_security.py backend/tests/test_api_matrix.py -q

echo "[resilience] PASS"
