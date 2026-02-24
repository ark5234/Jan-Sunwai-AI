#!/usr/bin/env bash
# Run from project root: bash scripts/run_tests.sh
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
echo "Running Backend Tests..."
cd "$SCRIPT_DIR"
source .venv/bin/activate
export PYTHONPATH="$SCRIPT_DIR/backend"
python -m pytest backend/tests/ -v
