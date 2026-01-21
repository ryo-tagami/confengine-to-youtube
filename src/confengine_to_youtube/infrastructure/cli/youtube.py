from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING

from returns.io import IOFailure, IOSuccess
from returns.unsafe import unsafe_perform_io

from confengine_to_youtube.adapters.confengine_api import ConfEngineApiGateway
from confengine_to_youtube.adapters.mapping_file_reader import MappingFileReader
from confengine_to_youtube.adapters.markdown_converter import MarkdownConverter
from confengine_to_youtube.adapters.youtube_api import YouTubeApiGateway
from confengine_to_youtube.adapters.youtube_description_builder import (
    YouTubeDescriptionBuilder,
)
from confengine_to_youtube.adapters.youtube_title_builder import YouTubeTitleBuilder
from confengine_to_youtube.infrastructure.cli.diff_formatter import DiffFormatter
from confengine_to_youtube.infrastructure.cli.result_aggregator import (
    aggregate_session_results,
)
from confengine_to_youtube.infrastructure.http_client import HttpClient
from confengine_to_youtube.infrastructure.youtube_auth import YouTubeAuthClient
from confengine_to_youtube.usecases.deps import UpdateYouTubeDeps
from confengine_to_youtube.usecases.update_youtube_descriptions import (
    update_youtube_descriptions,
)

if TYPE_CHECKING:
    import argparse

    from confengine_to_youtube.usecases.dto import YouTubeUpdateResult

from rich.console import Console


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
    youtube_api = YouTubeApiGateway(auth_provider=auth_client, youtube=None)

    description_builder = YouTubeDescriptionBuilder()
    title_builder = YouTubeTitleBuilder()

    # 依存関係を組み立て
    deps = UpdateYouTubeDeps(
        confengine_api=confengine_api,
        mapping_reader=mapping_reader,
        youtube_api=youtube_api,
        description_builder=description_builder,
        title_builder=title_builder,
    )

    # RequiresContextを実行
    result = update_youtube_descriptions(
        mapping_file=Path(args.mapping),
        dry_run=args.dry_run,
    )(deps)

    match result:
        case IOFailure():
            error = unsafe_perform_io(result.failure())
            print(f"Error: {error}", file=sys.stderr)  # noqa: T201
            sys.exit(1)
        case IOSuccess():
            batch = unsafe_perform_io(result.unwrap())
            youtube_result = aggregate_session_results(batch=batch)
            _print_result(result=youtube_result)


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
