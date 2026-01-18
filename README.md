# confengine-exporter

ConfEngineのセッション情報を使ってYouTube動画のdescriptionを更新するCLIツール。

## 必要要件

- Python 3.14以上
- [uv](https://docs.astral.sh/uv/)

## インストール

```bash
uv sync
```

## 使い方

YouTube動画のdescriptionをConfEngineのセッション情報で更新。

### マッピングファイルの雛形生成

ConfEngineからセッション情報を取得し、マッピングファイルの雛形を生成:

```bash
# stdoutに出力
uv run confengine-export generate-mapping <カンファレンスID>

# ファイルに出力
uv run confengine-export generate-mapping <カンファレンスID> -o mapping.yaml
```

| 引数/オプション | 説明 |
|----------------|------|
| `conf_id` | カンファレンスID |
| `-o, --output` | 出力ファイルパス (省略時はstdoutに出力) |

生成されたYAMLの `video_id` フィールドにYouTube動画IDを入力してください。

### 事前準備: YouTube API 認証設定

1. [Google Cloud Console](https://console.cloud.google.com/) でプロジェクトを作成
2. YouTube Data API v3 を有効化
3. OAuth 同意画面を設定
   - User Type は「Internal」と「External」から選択
   - 「Internal」は Google Workspace 組織内のユーザーのみ利用可能
   - 個人の Google アカウント（@gmail.com 等）で使用する場合は「External」を選択
4. OAuth 2.0 クライアント ID を作成（デスクトップアプリ）
5. credentials.json をダウンロードし、プロジェクトルートに `.credentials.json` として配置

初回実行時にブラウザが開き、Google アカウントでの認証が求められます。認証後、トークンが `.token.json` に保存されます。

### コマンド

```bash
uv run confengine-export youtube-update <カンファレンスID> -m <マッピングファイル> [オプション]
```

| 引数/オプション | 説明 |
|----------------|------|
| `conf_id` | カンファレンスID |
| `-m, --mapping` | セッションと動画のマッピングYAMLファイル (必須) |
| `--credentials` | OAuth credentials.jsonのパス (デフォルト: `.credentials.json`) |
| `--token` | トークン保存先 (デフォルト: `.token.json`) |
| `--dry-run` | 実際の更新を行わずプレビュー表示 |
| `--hashtags` | descriptionに追加するハッシュタグ |

### マッピングファイルの形式

```yaml
sessions:
  2026-01-08:
    Hall A:
      "09:30": { video_id: "xxxxxxxxxxx" }
      "10:30": { video_id: "yyyyyyyyyyy" }
    Hall B:
      "09:30": { video_id: "zzzzzzzzzzz" }
```

### 実行例

```bash
# プレビュー (実際の更新なし)
uv run confengine-export youtube-update regional-scrum-gathering-tokyo-2026 \
  -m mapping.yaml \
  --dry-run

# 実際に更新
uv run confengine-export youtube-update regional-scrum-gathering-tokyo-2026 \
  -m mapping.yaml \
  --hashtags '#RSGT2026'
```

## 開発

```bash
uv run task check   # lint + test を実行
uv run task lint    # ruff check, ruff format --check, mypy
uv run task test    # pytest
```

## ライセンス

MIT
