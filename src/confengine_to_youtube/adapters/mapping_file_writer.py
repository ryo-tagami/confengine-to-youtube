from __future__ import annotations

import functools
from typing import TYPE_CHECKING

import budoux
from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedMap
from wcwidth import wcwidth

from confengine_to_youtube.adapters.mapping_schema import MappingFileWithCommentSchema
from confengine_to_youtube.domain.constants import TITLE_SPEAKER_SEPARATOR

if TYPE_CHECKING:
    from datetime import datetime
    from typing import TextIO

    from confengine_to_youtube.domain.conference_schedule import ConferenceSchedule

# コメント行の最大幅 (80文字 - インデント8文字 - "# " 2文字 = 70文字)
_COMMENT_WIDTH = 70


@functools.cache
def _get_budoux_parser() -> budoux.Parser:
    """日本語分かち書きパーサーを取得する (遅延初期化)

    モジュールインポート時ではなく、初回使用時にパーサーを読み込む。
    """
    return budoux.load_default_japanese_parser()


class MappingFileWriter:
    def write(
        self,
        schedule: ConferenceSchedule,
        output: TextIO,
        generated_at: datetime,
    ) -> None:
        schema = MappingFileWithCommentSchema.from_conference_schedule(
            schedule=schedule,
        )

        self._schema_to_yaml(
            schema=schema,
            output=output,
            generated_at=generated_at,
        )

    def _schema_to_yaml(
        self,
        schema: MappingFileWithCommentSchema,
        output: TextIO,
        generated_at: datetime,
    ) -> None:
        """PydanticスキーマをコメントつきYAMLとしてファイルに書き込む"""
        root = CommentedMap()

        root.yaml_set_start_comment(
            comment=f"ConfEngine Mapping Template\n"
            f"Generated: {generated_at.isoformat()}",
        )

        root["conf_id"] = schema.conf_id
        root["playlist_id"] = schema.playlist_id

        # fmt: off
        root.yaml_set_comment_before_after_key(
            key="playlist_id",
            before=(
                "プレイリストID (YouTube Studioで事前に作成)\n"
                "例: PLxxxxxxxxxxxxxxxx"
            ),
        )
        # fmt: on

        sessions_map = CommentedMap()

        for session_date in sorted(schema.sessions.root.keys()):
            rooms_data = schema.sessions.root[session_date]
            rooms_map = CommentedMap()

            for room in sorted(rooms_data.root.keys()):
                times_data = rooms_data.root[room]
                times_map = CommentedMap()

                for session_time in sorted(times_data.root.keys()):
                    entry_schema = times_data.root[session_time]
                    time_str = session_time.strftime(format="%H:%M")

                    entry = CommentedMap()
                    entry["video_id"] = entry_schema.video_id

                    # スキーマからコメントを取得して追加
                    comment = self._wrap_comment(text=entry_schema.comment)
                    entry.yaml_set_comment_before_after_key(
                        key="video_id",
                        before=comment,
                        indent=8,
                    )
                    times_map[time_str] = entry

                rooms_map[room] = times_map

            sessions_map[session_date] = rooms_map

        root["hashtags"] = schema.hashtags
        # fmt: off
        root.yaml_set_comment_before_after_key(
            key="hashtags",
            before=(
                "ハッシュタグ\n"
                "例:\n"
                "  hashtags:\n"
                "    - '#RSGT2026'\n"
                "    - '#Agile'"
            ),
        )
        # fmt: on

        root["footer"] = schema.footer
        # fmt: off
        root.yaml_set_comment_before_after_key(
            key="footer",
            before=(
                "フッター (複数行の場合はリテラルブロック `|` を使用)\n"
                "例:\n"
                "  footer: |\n"
                "    1行目\n"
                "    2行目"
            ),
        )
        # fmt: on

        root["sessions"] = sessions_map
        # fmt: off
        root.yaml_set_comment_before_after_key(
            key="sessions",
            before=(
                "セッション\n"
                "セッションごとに更新対象を制御できます (デフォルト: true):\n"
                "例:\n"
                "  sessions:\n"
                '    "2026-01-07":\n'
                '      "Hall A":\n'
                '        "10:00":\n'
                '          video_id: "abc123"\n'
                "          update_title: false\n"
                "          update_description: false"
            ),
        )
        # fmt: on

        yaml = YAML()
        yaml.default_flow_style = False
        yaml.dump(data=root, stream=output)

    @classmethod
    def _wrap_comment(cls, text: str) -> str:
        """表示幅を考慮してテキストを分かち書き単位で折り返す"""
        chunks = cls._split_into_chunks(text=text)
        lines: list[str] = []
        current_line = ""
        current_width = 0

        for chunk in chunks:
            chunk_width = cls._display_width(text=chunk)

            if current_width + chunk_width > _COMMENT_WIDTH:
                if current_line:
                    lines.append(current_line)
                current_line = chunk.lstrip()
                current_width = cls._display_width(text=current_line)
            else:
                current_line += chunk
                current_width += chunk_width

        if current_line:
            lines.append(current_line)

        return "\n".join(lines)

    @staticmethod
    def _split_into_chunks(text: str) -> list[str]:
        """テキストを折り返し可能なチャンクに分割する

        1. TITLE_SPEAKER_SEPARATOR で分割 (タイトルとスピーカーの区切り)
        2. 各セグメントをbudouxで分かち書き
        3. budouxの結果をさらにスペースで分割 (英語対応)
        """
        result: list[str] = []
        segments = text.split(sep=TITLE_SPEAKER_SEPARATOR)

        for i, segment in enumerate(iterable=segments):
            if i > 0:
                result.append(TITLE_SPEAKER_SEPARATOR)

            # budouxで分かち書き
            budoux_chunks = _get_budoux_parser().parse(sentence=segment)

            for budoux_chunk in budoux_chunks:
                if " " in budoux_chunk:
                    words = budoux_chunk.split(sep=" ")
                    for j, word in enumerate(iterable=words):
                        if j > 0:
                            result.append(" ")
                        if word:
                            result.append(word)
                else:
                    result.append(budoux_chunk)

        return result

    @staticmethod
    def _display_width(text: str) -> int:
        """テキストの表示幅を計算する"""
        width = 0
        for char in text:
            char_w = wcwidth(wc=char)
            width += char_w if char_w >= 0 else 1
        return width
