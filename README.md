# kyarameru-tool-box

Codex 専用の個人ツールボックスです。`~/.codex` へスキルとフックを配備します。

## 前提

- Python 3.11+
- pip（`python3 -m pip` が利用可能）

## クイックスタート

```bash
cd /Users/ryukisato/deta_box/Project/kyarameru-tool-box
python3 scripts/install.py install
python3 scripts/install.py status
```

## コマンド

```bash
python3 scripts/install.py install [--mode copy|link] [--dry-run]
python3 scripts/install.py update [--mode copy|link] [--dry-run]
python3 scripts/install.py status
python3 scripts/install.py uninstall [--dry-run]
```

- `install`: `toolbox/` 配下を `~/.codex` へ配備
- `update`: `install` を再実行
- `status`: 配備状態を表示
- `uninstall`: マニフェストに記録された管理対象のみ削除

## 初期同梱内容

- `toolbox/skills/plan-worker/SKILL.md`
- `toolbox/skills/mcp-worker/SKILL.md`
- `toolbox/hooks/preflight.sh`
- `toolbox/AGENTS.md`（`~/.codex/AGENTS.md` へ配備）

`~/.codex/AGENTS.md` が既存の場合、`AGENTS.md.bak.<timestamp>` を作成してから置き換えます。

## テスト

```bash
python3 -m pip install -e '.[dev]'
python3 -m pytest -q
```

## ハーネス実行

検証を `smoke -> regression -> policy` の順で実行します。

```bash
bash scripts/harness.sh
```

`smoke` のみを実行する場合:

```bash
bash scripts/harness.sh --quick
```

失敗時は以下を表示して終了します。
- 失敗フェーズ
- 失敗コマンド
- 終了コード
- 再現コマンド

トラブルシュート:
- `No module named pytest` の場合は `.venv` を有効化して `python -m pip install -e '.[dev]'` を実行する。
- `scripts/harness.sh` は `.venv/bin/python` が存在すれば自動で優先利用する。

policy チェックのみを単体実行する場合:

```bash
bash scripts/policy-check.sh
```

PR作成時はテンプレートを使う:

```bash
gh pr create --title "<title>" --body-file docs/pr-template.md
```

補助スクリプトでPR作成する場合:

```bash
bash scripts/create-pr.sh "<title>"
```

## CI

GitHub Actions で `push` / `pull_request` 時にテストを自動実行します。

- ワークフロー: `.github/workflows/tests.yml`
- ジョブ名: `tests`
- 実行コマンド: `python3 -m pytest -q`

## main ブランチ保護

### GitHub UI で設定する場合

1. GitHub の対象リポジトリで `Settings` を開く。
2. `Branches` -> `Branch protection rules` -> `Add rule` を開く。
3. `Branch name pattern` に `main` を設定する。
4. 以下を有効化して保存する。
   - `Require a pull request before merging`
   - `Require status checks to pass before merging`（`tests` を必須チェックに追加）
   - `Do not allow bypassing the above settings`（利用可能なら有効化）
   - `Restrict pushes that create files` / `Restrict who can push to matching branches`（利用可能なら直接 push を禁止）

### gh CLI で設定する場合（管理者権限が必要）

`OWNER` と `REPO` を置き換えて実行します。

```bash
OWNER="your-org-or-user"
REPO="your-repo"

gh api \
  --method PUT \
  -H "Accept: application/vnd.github+json" \
  "/repos/${OWNER}/${REPO}/branches/main/protection" \
  -f required_status_checks.strict=true \
  -F required_status_checks.contexts[]="tests" \
  -f enforce_admins=true \
  -f required_pull_request_reviews.dismiss_stale_reviews=true \
  -f required_pull_request_reviews.required_approving_review_count=1 \
  -f required_conversation_resolution=true \
  -f restrictions=
```

補足:
- 設定には `admin` 権限を持つトークンで `gh auth login` 済みである必要があります。
- 直接 push を完全に禁止する運用では、上記に加えて Organization 側 Ruleset の利用も検討してください。
