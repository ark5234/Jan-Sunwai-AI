#!/usr/bin/env bash
set -euo pipefail

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
OUT_DIR=${1:-"./backups/mongo_${TIMESTAMP}"}
MONGO_URI=${MONGODB_URL:-"mongodb://localhost:27017/jan_sunwai_db"}

echo "[backup] creating backup at: ${OUT_DIR}"
mkdir -p "${OUT_DIR}"

mongodump --uri="${MONGO_URI}" --out="${OUT_DIR}"

echo "[backup] completed successfully"
