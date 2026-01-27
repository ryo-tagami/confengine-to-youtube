from __future__ import annotations

import sys
from contextlib import AbstractContextManager, nullcontext
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

from confengine_to_youtube.adapters.mapping_file_writer import MappingFileWriter
from confengine_to_youtube.infrastructure.cli.factories import create_confengine_api
from confengine_to_youtube.usecases.generate_mapping import GenerateMappingUseCase

if TYPE_CHECKING:
    import argparse
    from typing import TextIO


@dataclass(frozen=True)
class GenerateMappingConfig:
    """generate-mapping コマンドの設定"""

    conf_id: str
    output_path: Path | None

    @classmethod
    def from_args(cls, args: argparse.Namespace) -> GenerateMappingConfig:
        """argparse.Namespace から設定オブジェクトを生成"""
        return cls(
            conf_id=args.conf_id,
            output_path=Path(args.output) if args.output else None,
        )


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
    config = GenerateMappingConfig.from_args(args=args)

    confengine_api = create_confengine_api()
    mapping_writer = MappingFileWriter()

    usecase = GenerateMappingUseCase(
        confengine_api=confengine_api,
        mapping_writer=mapping_writer,
        clock=lambda: datetime.now().astimezone(),
    )

    try:
        output_context: AbstractContextManager[TextIO]

        if config.output_path:
            output_context = config.output_path.open(mode="w", encoding="utf-8")
            output_name = str(config.output_path)
        else:
            output_context = nullcontext(sys.stdout)
            output_name = "stdout"

        with output_context as f:
            result = usecase.execute(
                conf_id=config.conf_id,
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
