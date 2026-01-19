"""YouTube動画説明文ビルダー"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import TYPE_CHECKING

from snakemd import Document

from confengine_exporter.adapters.constants import (
    ELLIPSIS,
    YOUTUBE_DESCRIPTION_MAX_LENGTH,
)

if TYPE_CHECKING:
    from confengine_exporter.domain.session import Session


@dataclass(frozen=True)
class YouTubeDescriptionOptions:
    hashtags: str
    footer_text: str


class YouTubeDescriptionBuilder:
    def __init__(self, options: YouTubeDescriptionOptions) -> None:
        self.options = options

    def build(self, session: Session) -> str:
        abstract = session.abstract

        # YouTube説明文の最大文字数に収まるようabstractを調整
        frame_length = self._calculate_frame_length(session=session)
        available = YOUTUBE_DESCRIPTION_MAX_LENGTH - frame_length

        if available < len(ELLIPSIS):
            msg = f"フレーム部分だけで文字数制限を超えています ({frame_length=})"
            raise ValueError(msg)

        if abstract and len(abstract) > available:
            # 省略記号の文字数を確保して切り詰め
            abstract = abstract[: available - len(ELLIPSIS)] + ELLIPSIS

        return self._build_document(session=session, abstract=abstract)

    def _calculate_frame_length(self, session: Session) -> int:
        placeholder = "X"
        doc_with_placeholder = self._build_document(
            session=session, abstract=placeholder
        )

        return len(doc_with_placeholder) - len(placeholder)

    def _build_document(self, session: Session, abstract: str) -> str:
        doc = Document()

        if session.speakers:
            speakers_str = ", ".join(session.speakers)
            doc.add_paragraph(text=f"Speaker: {speakers_str}")

        if abstract:
            doc.add_raw(text=abstract)

        doc.add_horizontal_rule()

        if session.url:
            doc.add_paragraph(text=session.url)

        if self.options.hashtags:
            doc.add_paragraph(text=self.options.hashtags)

        doc.add_horizontal_rule()

        if self.options.footer_text:
            doc.add_paragraph(text=self.options.footer_text)

        return self._sanitize_for_youtube(text=str(doc))

    def _sanitize_for_youtube(self, text: str) -> str:
        """YouTube description で無効な文字を置換

        YouTubeは < > を許可しないため、これらを置換する。
        - <URL> パターンはURLだけを残す
        - 残りの < は U+2039 (SINGLE LEFT-POINTING ANGLE QUOTATION MARK) に置換
        - > は U+203A (SINGLE RIGHT-POINTING ANGLE QUOTATION MARK) に置換
        """
        # URLを囲む山括弧を除去
        text = re.sub(pattern=r"<(https?://[^>]+)>", repl=r"\1", string=text)
        # 残りの < > を置換
        return text.replace("<", "\u2039").replace(">", "\u203a")
