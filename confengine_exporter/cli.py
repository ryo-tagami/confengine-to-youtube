"""CLIエントリーポイント"""

import argparse
import sys
from pathlib import Path

from confengine_exporter.adapters.confengine_api import ConfEngineApiGateway
from confengine_exporter.adapters.file_writer import SessionFileWriter
from confengine_exporter.adapters.markdown_builder import (
    MarkdownOptions,
    SessionMarkdownBuilder,
)
from confengine_exporter.infrastructure.http_client import HttpClient
from confengine_exporter.usecases.export_sessions import ExportSessionsUseCase

DEFAULT_FOOTER = (
    "This video contains music from Shutterstock, licensed by Splice video editing app."
)


def main() -> None:
    """メインエントリーポイント"""
    parser = argparse.ArgumentParser(
        description="ConfEngineのスケジュールを1セッション1ファイルでエクスポート"
    )
    parser.add_argument(
        "conf_id",
        help="カンファレンスID (例: scrum-fest-osaka-2024)",
    )
    parser.add_argument(
        "--hashtags",
        help="ハッシュタグ (例: '#RSGT2026 #Agile #Scrum')",
    )
    parser.add_argument(
        "-o",
        "--output",
        help="出力ディレクトリ (省略時はカンファレンスID名)",
    )

    args = parser.parse_args()

    # 依存関係の組み立て
    http_client = HttpClient()
    api_gateway = ConfEngineApiGateway(http_client=http_client)

    markdown_options = MarkdownOptions(
        hashtags=args.hashtags or "",
        footer_text=DEFAULT_FOOTER,
    )
    markdown_builder = SessionMarkdownBuilder(options=markdown_options)

    output_dir = Path(args.output) if args.output else Path(args.conf_id)
    file_writer = SessionFileWriter(output_dir=output_dir)

    # ユースケース実行
    usecase = ExportSessionsUseCase(
        api_gateway=api_gateway,
        markdown_builder=markdown_builder,
        file_writer=file_writer,
    )

    try:
        result = usecase.execute(conf_id=args.conf_id)
        print(  # noqa: T201
            f"Exported {result.exported_count} sessions to {result.output_dir}/",
            file=sys.stderr,
        )
    except Exception as e:  # noqa: BLE001
        print(f"Error: {e}", file=sys.stderr)  # noqa: T201
        sys.exit(1)


if __name__ == "__main__":
    main()
