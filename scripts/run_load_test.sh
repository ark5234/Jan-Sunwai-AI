#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../backend"

python -m pip install -r requirements-loadtest.txt
locust -f locustfile.py --host "${1:-http://localhost:8000}"
