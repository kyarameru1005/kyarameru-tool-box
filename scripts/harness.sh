#!/usr/bin/env bash
set -euo pipefail

QUICK_MODE=0
PYTHON_BIN="${PYTHON_BIN:-python3}"

for arg in "$@"; do
  case "$arg" in
    --quick)
      QUICK_MODE=1
      ;;
    *)
      echo "[ERROR] unknown option: $arg"
      echo "Usage: bash scripts/harness.sh [--quick]"
      exit 2
      ;;
  esac
done

run_step() {
  local phase="$1"
  local cmd="$2"

  echo "[$phase] $cmd"
  set +e
  bash -lc "$cmd"
  local rc=$?
  set -e

  if [[ $rc -ne 0 ]]; then
    echo "[ERROR] phase failed: $phase"
    echo "[ERROR] command: $cmd"
    echo "[ERROR] exit code: $rc"
    echo "[ERROR] reproduce: $cmd"
    exit "$rc"
  fi
}

echo "[SETUP] checking python3"
if [[ -x ".venv/bin/python" ]]; then
  PYTHON_BIN=".venv/bin/python"
fi

if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  echo "[ERROR] python not found: $PYTHON_BIN"
  echo "[ERROR] reproduce: command -v $PYTHON_BIN"
  exit 127
fi

run_step "SMOKE" "$PYTHON_BIN scripts/install.py install --dry-run"
run_step "SMOKE" "$PYTHON_BIN scripts/install.py status"

if [[ $QUICK_MODE -eq 1 ]]; then
  echo "[DONE] quick mode completed (SMOKE only)"
  exit 0
fi

run_step "REGRESSION" "$PYTHON_BIN -m pytest -q"

run_step "POLICY" "test -f AGENTS.md"
run_step "POLICY" "test -f toolbox/AGENTS.md"
run_step "POLICY" "test -f .github/workflows/tests.yml"
run_step "POLICY" "bash toolbox/skills/agents-md-writer/scripts/check_agents_md.sh AGENTS.md"
run_step "POLICY" "bash toolbox/skills/agents-md-writer/scripts/check_agents_md.sh toolbox/AGENTS.md"

echo "[DONE] all phases passed"
