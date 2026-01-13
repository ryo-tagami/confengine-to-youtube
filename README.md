# confengine-exporter

ConfEngineのカンファレンススケジュールを1セッション1ファイルのMarkdown形式でエクスポートするCLIツール。

## 必要要件

- Python 3.14以上
- [uv](https://docs.astral.sh/uv/)

## インストール

```bash
uv sync
```

## 使い方

```bash
uv run confengine-export <カンファレンスID> [オプション]
```

### 引数

| 引数 | 説明 |
|------|------|
| `conf_id` | カンファレンスID (例: `regional-scrum-gathering-tokyo-2026`) |

### オプション

| オプション | 説明 |
|------------|------|
| `--hashtags` | Markdownに追加するハッシュタグ (例: `'#RSGT2026 #Agile'`) |
| `-o, --output` | 出力ディレクトリ (省略時はカンファレンスID名) |

### 実行例

```bash
# 基本的な使い方
uv run confengine-export regional-scrum-gathering-tokyo-2026

# ハッシュタグを追加
uv run confengine-export regional-scrum-gathering-tokyo-2026 --hashtags '#RSGT2026 #Agile #Scrum'

# 出力ディレクトリを指定
uv run confengine-export regional-scrum-gathering-tokyo-2026 -o output/
```

## 出力形式

各セッションは以下の形式でMarkdownファイルとして出力されます:

- ファイル名: `{日付}_{部屋名}_{開始時刻}.md`
- 例: `2026-01-07_Hall-A_10-00.md`

## 開発

### チェック (リンター・型チェック・テスト)

```bash
uv run task check   # lint + test を実行
uv run task lint    # ruff check, ruff format --check, mypy
uv run task test    # pytest
```

### フォーマット

```bash
uv run ruff format .
```

## ライセンス

MIT
