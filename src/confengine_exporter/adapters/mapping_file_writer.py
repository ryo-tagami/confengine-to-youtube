from __future__ import annotations

from typing import TYPE_CHECKING

import budoux
from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedMap
from wcwidth import wcwidth

from confengine_exporter.adapters.mapping_schema import MappingFileWithCommentSchema

if TYPE_CHECKING:
    from datetime import datetime
    from typing import TextIO

    from confengine_exporter.domain.session import Session

# コメント行の最大幅 (80文字 - インデント8文字 - "# " 2文字 = 70文字)
_COMMENT_WIDTH = 70

# 日本語分かち書きパーサー
_BUDOUX_PARSER = budoux.load_default_japanese_parser()


class MappingFileWriter:
    def write(
        self,
        sessions: list[Session],
        output: TextIO,
        conf_id: str,
        generated_at: datetime,
    ) -> None:
        schema = MappingFileWithCommentSchema.from_sessions(sessions=sessions)

        self._schema_to_yaml(
            schema=schema,
            output=output,
            conf_id=conf_id,
            generated_at=generated_at,
        )

    def _schema_to_yaml(
        self,
        schema: MappingFileWithCommentSchema,
        output: TextIO,
        conf_id: str,
        generated_at: datetime,
    ) -> None:
        """PydanticスキーマをコメントつきYAMLとしてファイルに書き込む"""
        root = CommentedMap()
        root.yaml_set_start_comment(
            comment=f"ConfEngine Mapping Template\n"
            f"Conference: {conf_id}\n"
            f"Generated: {generated_at.isoformat()}"
        )

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

        root["sessions"] = sessions_map

        yaml = YAML()
        yaml.default_flow_style = False
        yaml.dump(data=root, stream=output)

    def _wrap_comment(self, text: str) -> str:
        """表示幅を考慮してテキストを分かち書き単位で折り返す"""
        chunks = self._split_into_chunks(text=text)
        lines: list[str] = []
        current_line = ""
        current_width = 0

        for chunk in chunks:
            chunk_width = self._display_width(text=chunk)

            if current_width + chunk_width > _COMMENT_WIDTH:
                if current_line:
                    lines.append(current_line)
                current_line = chunk.lstrip()
                current_width = self._display_width(text=current_line)
            else:
                current_line += chunk
                current_width += chunk_width

        if current_line:
            lines.append(current_line)

        return "\n".join(lines)

    def _split_into_chunks(self, text: str) -> list[str]:
        """テキストを折り返し可能なチャンクに分割する

        1. " / " で分割 (タイトルとスピーカーの区切り)
        2. 各セグメントをbudouxで分かち書き
        3. budouxの結果をさらにスペースで分割 (英語対応)
        """
        result: list[str] = []
        segments = text.split(sep=" / ")

        for i, segment in enumerate(iterable=segments):
            if i > 0:
                result.append(" / ")

            # budouxで分かち書き
            budoux_chunks = _BUDOUX_PARSER.parse(sentence=segment)

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

    def _display_width(self, text: str) -> int:
        """テキストの表示幅を計算する"""
        width = 0
        for char in text:
            char_w = wcwidth(wc=char)
            width += char_w if char_w >= 0 else 1
        return width
