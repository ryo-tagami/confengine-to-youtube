# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## コマンド

```bash
uv run task check          # lint + test を実行
uv run task lint           # ruff check, ruff format --check, mypy
uv run task test           # pytest (カバレッジ付き)
uv run pytest tests/path/to/test.py::test_name  # 単一テスト実行
uv run ruff format .       # フォーマット
```

## アーキテクチャ

Clean Architectureに基づく4層構造:

```
confengine_exporter/
├── domain/          # ビジネスエンティティ (Session, Speaker, VideoMapping)
├── usecases/        # ビジネスロジック (依存性は注入)
├── adapters/        # 外部サービスとのインターフェース
└── infrastructure/  # 技術的詳細 (HTTP, 認証, CLI)
```

**依存の方向**: infrastructure → adapters → usecases → domain

### ユースケース

- `UpdateYouTubeDescriptionsUseCase`: セッション情報でYouTube動画のタイトルとdescriptionを更新
- `GenerateMappingUseCase`: マッピングYAML雛形を生成

### データフロー

1. CLI (`infrastructure/cli/`) が引数をパースし依存性を組み立て
2. UseCase がビジネスロジックを実行
3. Adapter (`adapters/`) が外部APIとの通信を担当

## コーディング規約

- `ruff` の `select = ["ALL"]` を使用（厳格なリンティング）
- D100-D103 は無効化（自明なコードにdocstringを強制しない）
- 日本語コメント可
- `from __future__ import annotations` を全ファイルで使用（`__init__.py` と `tests/` を除く）
- 型ヒント専用のimportは `TYPE_CHECKING` ブロック内に配置
- 関数・メソッド呼び出しでは、キーワード引数で渡せる引数は常にキーワード引数を使用する（位置専用引数を除く）
