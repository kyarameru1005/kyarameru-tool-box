# kyarameru-tool-box ルール

- 言語: Python 3.11+
- CLI は `scripts/install.py` に集約し、依存は標準ライブラリを優先する
- 既存ユーザー環境の破壊を避ける（未管理ファイルは上書き/削除しない）
- テストは `pytest` で単体テスト中心
- 変更時は `ai_log/YYYY-MM-DD.md` に追記する
