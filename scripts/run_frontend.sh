#!/usr/bin/env bash
# Run from project root: bash scripts/run_frontend.sh
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
echo "Starting Jan-Sunwai AI Frontend..."
cd "$SCRIPT_DIR/frontend"
npm run dev
