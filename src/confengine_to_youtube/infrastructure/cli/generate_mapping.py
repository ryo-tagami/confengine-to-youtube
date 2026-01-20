from __future__ import annotations

import sys
from contextlib import AbstractContextManager, nullcontext
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import argparse
    from typing import TextIO

from confengine_to_youtube.adapters.confengine_api import ConfEngineApiGateway
from confengine_to_youtube.adapters.mapping_file_writer import MappingFileWriter
from confengine_to_youtube.adapters.markdown_converter import MarkdownConverter
from confengine_to_youtube.infrastructure.http_client import HttpClient
from confengine_to_youtube.usecases.generate_mapping import GenerateMappingUseCase


def add_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "conf_id",
        help="カンファレンスID (例: scrum-fest-osaka-2024)",
    )
    parser.add_argument(
        "-o",
        "--output",
        help="出力ファイルパス (省略時はstdoutに出力)",
    )


def run(args: argparse.Namespace) -> None:
    http_client = HttpClient()
    confengine_api = ConfEngineApiGateway(
        http_client=http_client,
        markdown_converter=MarkdownConverter(),
    )
    mapping_writer = MappingFileWriter()

    usecase = GenerateMappingUseCase(
        confengine_api=confengine_api,
        mapping_writer=mapping_writer,
    )

    try:
        output_context: AbstractContextManager[TextIO]

        if args.output:
            output_path = Path(args.output)
            output_context = output_path.open(mode="w", encoding="utf-8")
            output_name = str(output_path)
        else:
            output_context = nullcontext(sys.stdout)
            output_name = "stdout"

        with output_context as f:
            result = usecase.execute(
                conf_id=args.conf_id,
                output=f,
            )

        print(  # noqa: T201
            f"Generated: {output_name} ({result.session_count} sessions)",
            file=sys.stderr,
        )

    # CLIエントリポイントで全例外をキャッチし、ユーザーフレンドリーなエラー表示を行う
    except Exception as e:  # noqa: BLE001
        print(f"Error: {type(e).__name__}: {e}", file=sys.stderr)  # noqa: T201
        sys.exit(1)
