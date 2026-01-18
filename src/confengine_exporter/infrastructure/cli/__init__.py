from __future__ import annotations

import argparse
import sys

from confengine_exporter.infrastructure.cli import generate_mapping, youtube


def main() -> None:
    parser = argparse.ArgumentParser(
        description="ConfEngineのセッション情報でYouTube動画のdescriptionを更新"
    )

    subparsers = parser.add_subparsers(dest="command")

    youtube_parser = subparsers.add_parser(
        name="youtube-update",
        help="YouTube動画のdescriptionを更新",
    )
    youtube.add_arguments(youtube_parser)

    generate_mapping_parser = subparsers.add_parser(
        name="generate-mapping",
        help="マッピングYAML雛形を生成",
    )
    generate_mapping.add_arguments(generate_mapping_parser)

    args = parser.parse_args()

    match args.command:
        case None:
            parser.print_help()
            sys.exit(1)
        case "youtube-update":
            youtube.run(args)
        case "generate-mapping":
            generate_mapping.run(args)


if __name__ == "__main__":
    main()
