#!/usr/bin/env bash
set -euo pipefail

BASE_BRANCH="main"
HEAD_BRANCH=""
DRAFT_MODE=0

usage() {
  echo "Usage: bash scripts/create-pr.sh \"<title>\" [--base <branch>] [--head <branch>] [--draft]"
}

if [[ $# -lt 1 ]]; then
  usage
  exit 2
fi

TITLE="$1"
shift

while [[ $# -gt 0 ]]; do
  case "$1" in
    --base)
      BASE_BRANCH="${2:-}"
      shift 2
      ;;
    --head)
      HEAD_BRANCH="${2:-}"
      shift 2
      ;;
    --draft)
      DRAFT_MODE=1
      shift
      ;;
    *)
      echo "[ERROR] unknown option: $1"
      usage
      exit 2
      ;;
  esac
done

if [[ -z "$TITLE" ]]; then
  echo "[ERROR] title is required"
  usage
  exit 2
fi

if ! command -v gh >/dev/null 2>&1; then
  echo "[ERROR] gh command is required"
  echo "[ERROR] install guide: https://cli.github.com/"
  exit 127
fi

if [[ ! -f "docs/pr-template.md" ]]; then
  echo "[ERROR] docs/pr-template.md not found"
  exit 1
fi

if [[ -z "$HEAD_BRANCH" ]]; then
  HEAD_BRANCH="$(git rev-parse --abbrev-ref HEAD)"
fi

if [[ "$HEAD_BRANCH" == "main" ]]; then
  echo "[ERROR] head branch is main. create and switch to a feature branch first."
  exit 1
fi

CMD=(gh pr create --base "$BASE_BRANCH" --head "$HEAD_BRANCH" --title "$TITLE" --body-file docs/pr-template.md)
if [[ $DRAFT_MODE -eq 1 ]]; then
  CMD+=(--draft)
fi

echo "[INFO] creating pull request"
"${CMD[@]}"
