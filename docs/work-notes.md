# 作業メモ

最終更新: 2026-03-24

## これからの作業

1. テスト実行環境の固定
- `pyproject.toml` にテスト依存を定義し、README にセットアップ手順を明記する。
- 目標: ローカルで `python3 -m pytest -q` が再現可能な状態にする。

2. CI の追加
- `.github/workflows/tests.yml` を追加し、push / pull_request で pytest を自動実行する。
- 目標: 変更時にテスト破壊を即検知できる状態にする。

3. ブランチ保護の適用（GitHub設定）
- `main` への直接 push を禁止。
- PR 必須 + CI 成功必須を有効化。

4. `.gitignore` の強化
- 候補: `.venv/`, `.coverage`, `htmlcov/`, `.mypy_cache/`, `dist/`, `build/` を追加。
- 目標: 開発生成物の混入防止。

## メモ
- 現状: `python3 -m pytest -q` は `No module named pytest` で失敗。
- Git 状態: `main` は `origin/main` を追跡中。
