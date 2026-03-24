# kyarameru-tool-box

Codex 専用の個人ツールボックスです。`~/.codex` へスキルとフックを配備します。

## 前提

- Python 3.11+
- pytest（テスト実行時のみ）

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
python3 -m pytest -q
```
