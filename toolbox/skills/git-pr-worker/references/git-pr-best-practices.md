# Git/PR Skill Best Practices

## 共通設計

- スキル記述は短くし、詳細は `references/` に分離する。
- 説明文には「何をするか」と「いつ使うか」を含める。
- 手順は実行順で書く（確認 -> 実行 -> 検証）。

## 実務で有効なルール

- PR作成前に `git status --short` で混入差分を確認する。
- ブランチ保護の必須条件（checks/review）を先に把握する。
- CI停止時は、`gh pr checks` と `gh run list/view` で一次切り分けする。
- ブロック理由は「CI失敗」か「保護ルール」かを分離して説明する。

## 失敗パターン

- PR本文のシェル展開ミス（バッククォート未エスケープ）
- 無関係ファイルの混入コミット
- CI成功なのにレビュー必須でブロックされる誤認

## 参考にした公開情報

- Claude Docs: Skill authoring best practices
- Claude Docs: Agent Skills examples（commit helper等）
- vercel-labs/skills および vercel-labs/agent-skills の公開構成
- 公開コミュニティ例の git-pushing SKILL
