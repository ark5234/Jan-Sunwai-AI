#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "${ROOT_DIR}"

TAG="${1:-v1.0-rc1}"

echo "[release] running backend tests"
PYTHONPATH="${ROOT_DIR}/backend" python -m pytest backend/tests -q

echo "[release] running frontend lint/build"
cd frontend
npm run lint
npm run build
cd "${ROOT_DIR}"

if git rev-parse "${TAG}" >/dev/null 2>&1; then
  echo "[release] tag already exists: ${TAG}"
  exit 0
fi

git tag -a "${TAG}" -m "Release candidate ${TAG}"
echo "[release] created local tag: ${TAG}"
echo "[release] push with: git push origin ${TAG}"
