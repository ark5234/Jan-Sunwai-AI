#!/usr/bin/env bash
# Run from project root: bash scripts/run_tests.sh
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [[ -f "${SCRIPT_DIR}/.venv/bin/activate" ]]; then
	# shellcheck disable=SC1091
	source "${SCRIPT_DIR}/.venv/bin/activate"
fi

echo "Running backend test suite..."
cd "$SCRIPT_DIR"
export PYTHONPATH="$SCRIPT_DIR/backend"
python -m pytest backend/tests/ -q

if [[ -d "${SCRIPT_DIR}/frontend" ]]; then
	echo "Running frontend lint/build smoke..."
	cd "${SCRIPT_DIR}/frontend"
	npm run lint
	npm run build
fi
