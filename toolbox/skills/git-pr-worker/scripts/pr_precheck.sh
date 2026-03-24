#!/usr/bin/env bash
set -euo pipefail

echo "[INFO] branch: $(git branch --show-current)"
echo "[INFO] remotes:"
git remote -v || true

echo "[INFO] status:"
git status --short

if command -v gh >/dev/null 2>&1; then
  echo "[INFO] gh auth status:"
  gh auth status >/dev/null 2>&1 && echo "  ok" || echo "  not logged in"
else
  echo "[WARN] gh not found"
fi
