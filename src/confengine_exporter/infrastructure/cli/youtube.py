from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import argparse

    from confengine_exporter.usecases.dto import YouTubeUpdateResult

from rich.console import Console

from confengine_exporter.adapters.confengine_api import ConfEngineApiGateway
from confengine_exporter.adapters.mapping_file_reader import MappingFileReader
from confengine_exporter.adapters.youtube_api import YouTubeApiGateway
from confengine_exporter.adapters.youtube_description_builder import (
    YouTubeDescriptionBuilder,
    YouTubeDescriptionOptions,
)
from confengine_exporter.adapters.youtube_title_builder import YouTubeTitleBuilder
from confengine_exporter.infrastructure.cli.constants import DEFAULT_FOOTER
from confengine_exporter.infrastructure.cli.diff_formatter import DiffFormatter
from confengine_exporter.infrastructure.http_client import HttpClient
from confengine_exporter.infrastructure.youtube_auth import YouTubeAuthClient
from confengine_exporter.usecases.update_youtube_descriptions import (
    UpdateYouTubeDescriptionsUseCase,
)


def add_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "conf_id",
        help="カンファレンスID (例: scrum-fest-osaka-2024)",
    )
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
    confengine_api = ConfEngineApiGateway(http_client=http_client)

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
    youtube_api = YouTubeApiGateway(auth_provider=auth_client)

    description_options = YouTubeDescriptionOptions(
        footer_text=DEFAULT_FOOTER,
    )
    description_builder = YouTubeDescriptionBuilder(options=description_options)
    title_builder = YouTubeTitleBuilder()

    usecase = UpdateYouTubeDescriptionsUseCase(
        confengine_api=confengine_api,
        mapping_reader=mapping_reader,
        youtube_api=youtube_api,
        description_builder=description_builder,
        title_builder=title_builder,
    )

    try:
        mapping_file = Path(args.mapping)

        if not mapping_file.exists():
            print(  # noqa: T201
                f"Error: mapping file not found: {mapping_file}",
                file=sys.stderr,
            )
            sys.exit(1)

        result = usecase.execute(
            conf_id=args.conf_id,
            mapping_file=mapping_file,
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

        success_count = 0
        error_count = 0

        for i, preview in enumerate(iterable=result.previews, start=1):
            formatter.print_preview(preview=preview, index=i)

            if preview.error:
                error_count += 1
            else:
                success_count += 1

        formatter.print_summary(success_count=success_count, error_count=error_count)
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
