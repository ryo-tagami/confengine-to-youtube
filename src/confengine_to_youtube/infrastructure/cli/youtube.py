from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from rich.console import Console

from confengine_to_youtube.adapters.mapping_file_reader import MappingFileReader
from confengine_to_youtube.adapters.youtube_api import YouTubeApiGateway
from confengine_to_youtube.infrastructure.cli.diff_formatter import DiffFormatter
from confengine_to_youtube.infrastructure.cli.factories import create_confengine_api
from confengine_to_youtube.infrastructure.youtube_auth import YouTubeAuthClient
from confengine_to_youtube.usecases.update_youtube_descriptions import (
    UpdateYouTubeDescriptionsUseCase,
)

if TYPE_CHECKING:
    import argparse

    from confengine_to_youtube.usecases.dto import VideoUpdateResult


@dataclass(frozen=True)
class YouTubeUpdateConfig:
    """youtube-update コマンドの設定"""

    mapping_file: Path
    credentials_path: Path
    token_path: Path
    dry_run: bool

    @classmethod
    def from_args(cls, args: argparse.Namespace) -> YouTubeUpdateConfig:
        """argparse.Namespace から設定オブジェクトを生成"""
        return cls(
            mapping_file=Path(args.mapping),
            credentials_path=Path(args.credentials),
            token_path=Path(args.token),
            dry_run=args.dry_run,
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
    config = YouTubeUpdateConfig.from_args(args=args)

    if not config.credentials_path.exists():
        print(  # noqa: T201
            f"Error: credentials file not found: {config.credentials_path}",
            file=sys.stderr,
        )
        print(  # noqa: T201
            "Please download credentials.json from Google Cloud Console",
            file=sys.stderr,
        )
        sys.exit(1)

    confengine_api = create_confengine_api()
    mapping_reader = MappingFileReader()

    auth_client = YouTubeAuthClient(
        credentials_path=config.credentials_path,
        token_path=config.token_path,
    )
    youtube_api = YouTubeApiGateway.from_auth_provider(auth_provider=auth_client)

    usecase = UpdateYouTubeDescriptionsUseCase(
        confengine_api=confengine_api,
        mapping_reader=mapping_reader,
        youtube_api=youtube_api,
    )

    try:
        result = usecase.execute(
            mapping_file=config.mapping_file,
            dry_run=config.dry_run,
        )

        _print_result(result=result)

    # CLIエントリポイントで全例外をキャッチし、ユーザーフレンドリーなエラー表示を行う
    except Exception as e:  # noqa: BLE001
        print(f"Error: {type(e).__name__}: {e}", file=sys.stderr)  # noqa: T201
        sys.exit(1)


def _print_result(result: VideoUpdateResult) -> None:
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
