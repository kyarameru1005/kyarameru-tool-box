# ハーネス構築計画（v1）

## 1. 目的と成功条件を定義

- 目的: `install/update/uninstall` と運用ルール順守を自動検証する。
- 成功条件:
- ローカルで1コマンド実行できる。
- CIで同じ検証が再現できる。
- 失敗時に原因と再実行方法が分かる。

## 2. 検証スコープを3層に分割

- `smoke`:
- `python3 scripts/install.py install --dry-run`
- `python3 scripts/install.py status`
- `regression`:
- `python3 -m pytest -q`
- `policy`:
- 必須ファイル存在チェック（例: `toolbox/AGENTS.md`, workflow）
- ルール文書の最低要件チェック（PR正本ログ方針など）

## 3. 実行入口を統一

- `scripts/harness.sh` を作成し、以下を順次実行:
- 環境前提チェック（Python/venv）
- `smoke` -> `regression` -> `policy`
- `--quick` オプションで `smoke` のみ実行可能にする。

## 4. CI連携

- 既存 `.github/workflows/tests.yml` を拡張し、`harness` ジョブを追加。
- ジョブ内では `pip install -e '.[dev]'` 後に `bash scripts/harness.sh` を実行。
- 失敗時はログをそのまま表示し、どのフェーズで落ちたか分かるようにする。

## 5. 出力仕様（失敗時）

- 各フェーズ開始時に見出しを出力（`[SMOKE]` など）。
- 失敗時は:
- 失敗したコマンド
- 終了コード
- 再現コマンド
- を必ず表示して終了。

## 6. 導入手順

1. `scripts/harness.sh` 追加
2. README に「ハーネス実行方法」を追記
3. CI workflow 更新
4. ローカル実行確認（quick/full）
5. PRでCI通過確認

## 7. 受け入れ基準

- ローカル: `bash scripts/harness.sh` が通る。
- CI: `harness` ジョブが green。
- ドキュメント: README に実行手順とトラブルシュートがある。
