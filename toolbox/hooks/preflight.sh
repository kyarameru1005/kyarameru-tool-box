#!/usr/bin/env bash
set -euo pipefail

# 最小プレフライト: Python の存在確認
if ! command -v python3 >/dev/null 2>&1; then
  echo "[ERROR] python3 が見つかりません" >&2
  exit 1
fi

echo "[INFO] preflight OK"
