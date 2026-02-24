#!/usr/bin/env bash
# Run from project root: bash scripts/run_backend.sh
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
echo "Starting Jan-Sunwai AI Backend..."
cd "$SCRIPT_DIR"
source .venv/bin/activate
export PYTHONPATH="$SCRIPT_DIR/backend:$SCRIPT_DIR"
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
