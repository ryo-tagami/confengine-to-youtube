from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import argparse

    from confengine_to_youtube.usecases.dto import YouTubeUpdateResult

from rich.console import Console

from confengine_to_youtube.adapters.confengine_api import ConfEngineApiGateway
from confengine_to_youtube.adapters.mapping_file_reader import MappingFileReader
from confengine_to_youtube.adapters.markdown_converter import MarkdownConverter
from confengine_to_youtube.adapters.youtube_api import YouTubeApiGateway
from confengine_to_youtube.infrastructure.cli.diff_formatter import DiffFormatter
from confengine_to_youtube.infrastructure.http_client import HttpClient
from confengine_to_youtube.infrastructure.youtube_auth import YouTubeAuthClient
from confengine_to_youtube.usecases.update_youtube_descriptions import (
    UpdateYouTubeDescriptionsUseCase,
)


def add_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "-m",
        "--mapping",
        required=True,
        help="マッピングYAMLファイル",
    )
    parser.add_argument(
        "--credentials",
        default=".credentials.json",
        help="OAuth credentials.jsonのパス",
    )
    parser.add_argument(
        "--token",
        default=".token.json",
        help="トークン保存先",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="実際の更新を行わずプレビュー表示",
    )


def run(args: argparse.Namespace) -> None:
    http_client = HttpClient()
    confengine_api = ConfEngineApiGateway(
        http_client=http_client,
        markdown_converter=MarkdownConverter(),
    )

    mapping_reader = MappingFileReader()

    credentials_path = Path(args.credentials)
    token_path = Path(args.token)

    if not credentials_path.exists():
        print(  # noqa: T201
            f"Error: credentials file not found: {credentials_path}",
            file=sys.stderr,
        )
        print(  # noqa: T201
            "Please download credentials.json from Google Cloud Console",
            file=sys.stderr,
        )
        sys.exit(1)

    auth_client = YouTubeAuthClient(
        credentials_path=credentials_path,
        token_path=token_path,
    )
    youtube_api = YouTubeApiGateway.from_auth_provider(auth_provider=auth_client)

    usecase = UpdateYouTubeDescriptionsUseCase(
        confengine_api=confengine_api,
        mapping_reader=mapping_reader,
        youtube_api=youtube_api,
    )

    try:
        result = usecase.execute(
            mapping_file=Path(args.mapping),
            dry_run=args.dry_run,
        )

        _print_result(result=result)

    # CLIエントリポイントで全例外をキャッチし、ユーザーフレンドリーなエラー表示を行う
    except Exception as e:  # noqa: BLE001
        print(f"Error: {type(e).__name__}: {e}", file=sys.stderr)  # noqa: T201
        sys.exit(1)


def _print_result(result: YouTubeUpdateResult) -> None:
    if result.is_dry_run:
        formatter = DiffFormatter(console=Console(stderr=True))

        formatter.print_header(message="=== Dry Run Mode ===")

        for i, preview in enumerate(iterable=result.previews, start=1):
            formatter.print_preview(preview=preview, index=i)

        formatter.print_summary(count=len(result.previews))
    else:
        print(f"Updated: {result.updated_count} videos", file=sys.stderr)  # noqa: T201

    if result.no_content_count > 0:
        print(  # noqa: T201
            f"Skipped (no content): {result.no_content_count}",
            file=sys.stderr,
        )
    if result.no_mapping_count > 0:
        print(  # noqa: T201
            f"Skipped (no mapping): {result.no_mapping_count}",
            file=sys.stderr,
        )
    if result.unused_mappings_count > 0:
        print(  # noqa: T201
            f"Unused mappings: {result.unused_mappings_count}",
            file=sys.stderr,
        )

    if result.errors:
        print(  # noqa: T201
            f"Errors: {len(result.errors)}",
            file=sys.stderr,
        )
        for error in result.errors:
            print(  # noqa: T201
                f"  - {error.session_key} ({error.video_id}): {error.error.message}",
                file=sys.stderr,
            )
