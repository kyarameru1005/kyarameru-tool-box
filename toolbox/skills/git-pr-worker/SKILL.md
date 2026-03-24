---
name: git-pr-worker
description: ブランチ作成、差分整理、コミット、PR作成/更新、CI確認までを安全に進める。gitやPR運用の依頼、マージブロック調査、レビュー待ち整理のときに使う。
---

# git-pr-worker

目的: Git/PR作業を安全かつ再現可能に進める。

## 推奨トリガー

- 「PRを作って」「コミットしてpushして」
- 「CIで止まった原因を調べて」
- 「マージできない理由を調べて」
- 「ブランチ保護に合わせて運用したい」

## 基本原則

- 非破壊優先。`reset --hard` や履歴改変は明示依頼がある場合のみ。
- 無関係な差分を混ぜない（明示依頼がない `ai_log` などは除外）。
- まず事実確認してから操作する（推測で進めない）。

## 標準ワークフロー

1. `scripts/pr_precheck.sh` で状態確認（branch/status/remotes）。
2. 必要なら作業ブランチを作成。
3. 変更対象を明示して選択的に stage/commit。
4. `git push -u origin <branch>`。
5. `gh pr create` または `gh pr edit` でPR本文を整備。
6. `gh pr checks` / `gh pr view` でCIとブロック要因を確認。
7. ブロックがある場合は「原因・修正方針・次手」を短く提示。

## PR本文の最小要件

- 目的
- 主な変更点
- 検証結果（実行コマンドと要点）

## CI失敗時の対応

- 失敗ジョブ名、失敗ステップ、エラーメッセージを抜き出す。
- ローカル再現コマンドを提示する。
- 修正後に再実行し、通過ログを確認する。

## 参考

詳細パターンは [references/git-pr-best-practices.md](references/git-pr-best-practices.md) を参照。
