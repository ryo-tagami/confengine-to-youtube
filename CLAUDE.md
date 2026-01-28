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
confengine_to_youtube/
├── domain/          # ビジネスエンティティ (Session, Speaker, VideoMapping)
├── usecases/        # ビジネスロジック (依存性は注入)
├── adapters/        # 外部サービスとのインターフェース
└── infrastructure/  # 技術的詳細 (HTTP, 認証, CLI)
```

**依存の方向**: infrastructure → adapters → usecases → domain

### ドメイン層の設計方針

ドメイン層では `snakemd` ライブラリを使用してMarkdownドキュメントを構築している。これは意図的な設計判断である。YouTube descriptionの生成はこのアプリケーションのコアビジネスロジックであり、Markdownフォーマッティングはその本質的な機能の一部である。`snakemd` はHTTPクライアントやDBドライバのような「インフラストラクチャの詳細」ではなく、`Decimal` や `datetime` と同様に「ドメインの概念を表現するライブラリ」として位置づけている。

同様に、`returns` ライブラリの Result 型をドメイン層のエラーハンドリングに使用している。これにより、予期されるエラーを型で表現し、呼び出し側に明示的なハンドリングを強制できる。

### エラーハンドリング戦略

エラーの種類によって表現方法を使い分けている:

| エラーの種類 | 表現方法 | 例 |
|------------|---------|-----|
| 予期されるビジネスエラー | `Result` 型 | タイトルが長すぎる、フレームオーバーフロー |
| インフラ由来の回復不能エラー | 例外 | ファイルが見つからない、動画が存在しない |

- **`Result` 型** (`domain/errors.py`): ドメイン層で発生する予期されるエラー。呼び出し側に明示的なハンドリングを強制する。
- **例外** (`usecases/errors.py`): インフラ層に由来するエラー。CLI層でキャッチしてユーザーにエラーメッセージを表示する。

### ユースケース

- `UpdateYouTubeDescriptionsUseCase`: セッション情報でYouTube動画のタイトル、description、プレイリスト順序を更新
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

## ドキュメント更新

- 新機能追加時はREADME.mdも更新する
- ユースケースやアーキテクチャに変更がある場合はCLAUDE.mdも更新する

## テストコード

### 基本方針

- 似た構造のテストは `@pytest.mark.parametrize` で集約する
- テスト用のエンティティ作成が複数箇所で必要な場合は `tests/conftest.py` にヘルパー関数を用意する
- 繰り返しインスタンス化するオブジェクト（Builder等）はフィクスチャ化する
- Mockを使う場合は `assert_called_once()` 等で呼び出しを検証する
- テストでプライベート属性（`_xxx`）への直接アクセスや `patch` は避け、コンストラクタ引数で依存性を注入する

### アサーションのパターン

- **部分一致アサーションは禁止**: `assert "str" in "string"` のような部分一致は誤検出の原因になる
- 代わりに以下のパターンを使用する:

| 目的 | 推奨パターン | 避けるべきパターン |
|---|---|---|
| 完全一致 | `assert x == "expected"` | `assert "expected" in x` |
| 前方一致 | `assert x.startswith("prefix")` | `assert "prefix" in x` |
| 後方一致 | `assert x.endswith("suffix")` | `assert "suffix" in x` |
| 型チェック | `assert isinstance(error, MyError)` | `assert "MyError" in type(error).__name__` |
| プロパティ検証 | `assert error.video_id == "abc"` | `assert "abc" in str(error)` |
| 行の存在確認 | `assert "line" in output.splitlines()` | `assert "line" in output` |

```python
# 非推奨: 部分一致
assert "エラー" in result.failure().message
assert "ValidationError" in type(error).__name__

# 推奨: 完全一致または明示的なパターン
assert result.failure().message == "タイトルは必須エラーです"
assert isinstance(error, ValidationError)
assert result.failure().message.startswith("フレーム部分")
```

### 依存性注入

- `datetime.now()` などの非決定的な値は `patch` ではなく依存性注入する
  - 例: `clock: Callable[[], datetime]` をコンストラクタで受け取り、本番では `lambda: datetime.now().astimezone()` を渡す
- 外部APIクライアントなどもコンストラクタで注入し、テストではモックを渡す

### フィクスチャとヘルパー

- タイムゾーン等の共通定数はフィクスチャ化する（例: `jst` フィクスチャ）
- ファイル書き込みなどの共通パターンはヘルパー関数化する（例: `write_yaml_file`）
- 複数のテストファイルで共通するフィクスチャはサブディレクトリの `conftest.py` に配置
  - 例: `tests/usecases/conftest.py` に usecase テスト共通のフィクスチャを配置

### モックの作成

- `MagicMock()` ではなく `create_autospec(SpecClass, spec_set=True)` を使用する
  - 存在しないメソッドの呼び出しや間違った引数を検出できる
  - `spec_set=True` で存在しない属性への代入も禁止
  - 例外: `googleapiclient` のようにメソッドが実行時に動的生成されるライブラリは `create_autospec` が使えないため `MagicMock` を許容する
- 型アノテーションは Protocol 型を使用する（例: `ConfEngineApiProtocol`）
- モック特有のメソッド（`assert_called_once`, `side_effect` 等）を使う箇所には `# type: ignore[attr-defined]` を追加する

```python
# 例
def create_mock_confengine_api(
    sessions: tuple[Session, ...], timezone: ZoneInfo
) -> ConfEngineApiProtocol:
    mock = create_autospec(ConfEngineApiProtocol, spec_set=True)
    mock.fetch_sessions.return_value = (sessions, timezone)
    return mock  # type: ignore[no-any-return]

# モック特有のメソッドを使う場合
mock_api.fetch_sessions.assert_called_once()  # type: ignore[attr-defined]
```

### プライベートメソッドのテスト

- 原則として公開インターフェース経由でテストする
- やむを得ずプライベートメソッドを直接テストする場合は、ファイル先頭のdocstringに理由を明記する

### テストの分類（テストピラミッド）

テストはサイズ別にディレクトリで分類する:

```
tests/
├── unit/           # ユニットテスト
│   ├── domain/
│   ├── adapters/
│   └── infrastructure/
├── integration/    # 統合テスト
│   ├── usecases/
│   ├── adapters/
│   └── infrastructure/
└── conftest.py     # 共通フィクスチャ
```

#### Unit Testの条件（すべて満たす）

1. テスト対象が単一クラス/関数
2. **実際の外部リソースへのI/Oなし**
   - ファイルシステム（tmp_path等）へのアクセスなし
   - ネットワークアクセスなし
   - StringIO等のメモリストリームはI/Oに含まない
3. モックが不要、または単一のシンプルなモックのみ

#### Integration Testの条件（いずれかを満たす）

1. 複数のProtocolモックを組み合わせる
2. **実際のファイルI/O**（tmp_path使用）を伴う
3. HTTPクライアントのモックを使用し、外部API応答の変換ロジックをテスト
4. 複数コンポーネントの連携を検証

#### E2E Testの条件

1. CLIコマンドをsubprocess経由で実行
2. 実際の外部APIに接続
3. システム全体の動作を検証
