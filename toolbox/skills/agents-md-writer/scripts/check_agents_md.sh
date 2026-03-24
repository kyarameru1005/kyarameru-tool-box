#!/usr/bin/env bash
set -euo pipefail

TARGET="${1:-AGENTS.md}"

if [[ ! -f "$TARGET" ]]; then
  echo "[ERROR] file not found: $TARGET"
  exit 1
fi

has_pattern() {
  local pattern="$1"
  local file="$2"
  if command -v rg >/dev/null 2>&1; then
    rg -q "$pattern" "$file"
  else
    grep -Eq "$pattern" "$file"
  fi
}

required_patterns=(
  "目的"
  "優先"
  "応答"
  "実行"
  "Git"
  "ログ"
  "命名"
)

for pat in "${required_patterns[@]}"; do
  if ! has_pattern "$pat" "$TARGET"; then
    echo "[ERROR] missing required section/keyword: $pat"
    exit 1
  fi
done

for bad in "適宜" "必要に応じて" "可能であれば" "状況に応じて"; do
  if has_pattern "$bad" "$TARGET"; then
    echo "[ERROR] ambiguous phrase found: $bad"
    exit 1
  fi
done

if ! has_pattern "kebab-case|ハイフン" "$TARGET"; then
  echo "[ERROR] missing naming rule (kebab-case/hyphen)"
  exit 1
fi

if ! has_pattern "PR本文.*正本|正本.*PR本文" "$TARGET"; then
  echo "[WARN] PR本文を正本とする記述が見つかりません"
fi

echo "[OK] AGENTS.md check passed: $TARGET"
