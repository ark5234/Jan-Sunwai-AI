#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "${ROOT_DIR}"

export PYTHONPATH="${ROOT_DIR}/backend"

echo "[security] running automated security-focused pytest suites"
python -m pytest backend/tests/test_resilience_security.py backend/tests/test_notification_chain.py backend/tests/test_auth_permissions.py -q

echo "[security] automated checks passed"

echo "[security] optional live API probes"
echo "  curl -H 'Authorization: Bearer invalid.token' http://localhost:8000/complaints"
echo "  curl -H 'Authorization: Bearer <citizen-token>' http://localhost:8000/workers"
