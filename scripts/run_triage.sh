#!/usr/bin/env bash
# Run from project root: bash scripts/run_triage.sh
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
echo "Running Automated Triage..."
cd "$SCRIPT_DIR/backend"
source "$SCRIPT_DIR/.venv/bin/activate"
python automated_triage.py --dataset-dir sorted_dataset --output-dir triage_output --prune-ratio 0.15
