from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import argparse

from confengine_exporter.adapters.confengine_api import ConfEngineApiGateway
from confengine_exporter.adapters.mapping_file_writer import MappingFileWriter
from confengine_exporter.infrastructure.http_client import HttpClient
from confengine_exporter.usecases.generate_mapping import GenerateMappingUseCase


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
    confengine_api = ConfEngineApiGateway(http_client=http_client)
    mapping_writer = MappingFileWriter()

    usecase = GenerateMappingUseCase(
        confengine_api=confengine_api,
        mapping_writer=mapping_writer,
    )

    try:
        if args.output:
            output_path = Path(args.output)
            with output_path.open(mode="w", encoding="utf-8") as f:
                result = usecase.execute(conf_id=args.conf_id, output=f)
            msg = f"Generated: {output_path} ({result.session_count} sessions)"
            print(msg, file=sys.stderr)  # noqa: T201
        else:
            result = usecase.execute(conf_id=args.conf_id, output=sys.stdout)
            msg = f"Generated: stdout ({result.session_count} sessions)"
            print(msg, file=sys.stderr)  # noqa: T201

    except Exception as e:  # noqa: BLE001
        print(f"Error: {type(e).__name__}: {e}", file=sys.stderr)  # noqa: T201
        sys.exit(1)
