#!/usr/bin/env bash
set -euo pipefail

check_file() {
  local path="$1"
  echo "[CHECK] file exists: $path"
  if [[ ! -f "$path" ]]; then
    echo "[ERROR] missing file: $path"
    exit 1
  fi
  echo "[OK] file exists: $path"
}

check_pattern() {
  local pattern="$1"
  local path="$2"
  local label="$3"
  echo "[CHECK] $label"
  if command -v rg >/dev/null 2>&1; then
    if ! rg -q "$pattern" "$path"; then
      echo "[ERROR] pattern not found: $label"
      echo "[ERROR] file: $path"
      exit 1
    fi
  else
    if ! grep -Eq "$pattern" "$path"; then
      echo "[ERROR] pattern not found: $label"
      echo "[ERROR] file: $path"
      exit 1
    fi
  fi
  echo "[OK] $label"
}

check_file "AGENTS.md"
check_file "toolbox/AGENTS.md"
check_file ".github/workflows/tests.yml"
check_file "toolbox/skills/agents-md-writer/scripts/check_agents_md.sh"
check_file "docs/pr-template.md"
check_file "scripts/create-pr.sh"

echo "[CHECK] validate AGENTS.md files"
bash toolbox/skills/agents-md-writer/scripts/check_agents_md.sh AGENTS.md
bash toolbox/skills/agents-md-writer/scripts/check_agents_md.sh toolbox/AGENTS.md
echo "[OK] AGENTS.md validation"

WORKFLOW_FILE=".github/workflows/tests.yml"
check_pattern "^jobs:" "$WORKFLOW_FILE" "workflow has jobs section"
check_pattern "^  tests:" "$WORKFLOW_FILE" "workflow has tests job"
check_pattern "^  harness:" "$WORKFLOW_FILE" "workflow has harness job"
check_pattern "^  agents-policy:" "$WORKFLOW_FILE" "workflow has agents-policy job"
check_pattern "bash scripts/harness\\.sh" "$WORKFLOW_FILE" "workflow runs harness"

PR_TEMPLATE_FILE="docs/pr-template.md"
check_pattern "^## 目的" "$PR_TEMPLATE_FILE" "pr template has 目的 section"
check_pattern "^## 主な変更点" "$PR_TEMPLATE_FILE" "pr template has 主な変更点 section"
check_pattern "^## 検証結果" "$PR_TEMPLATE_FILE" "pr template has 検証結果 section"

echo "[DONE] policy checks passed"
