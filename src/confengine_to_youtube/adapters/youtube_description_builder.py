"""YouTube動画説明文ビルダー"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import TYPE_CHECKING

from snakemd import Document

from confengine_to_youtube.adapters.constants import (
    ELLIPSIS,
    YOUTUBE_DESCRIPTION_MAX_LENGTH,
)
from confengine_to_youtube.adapters.youtube_title_builder import YouTubeTitleBuilder

if TYPE_CHECKING:
    from confengine_to_youtube.domain.session import Session


@dataclass(frozen=True)
class YouTubeDescriptionOptions:
    footer_text: str


class YouTubeDescriptionBuilder:
    def __init__(self, options: YouTubeDescriptionOptions) -> None:
        self.options = options

    def build(self, session: Session, hashtags: tuple[str, ...]) -> str:
        abstract = session.abstract

        # YouTube説明文の最大文字数に収まるようabstractを調整
        frame_length = self._calculate_frame_length(session=session, hashtags=hashtags)
        available = YOUTUBE_DESCRIPTION_MAX_LENGTH - frame_length

        if available < len(ELLIPSIS):
            msg = f"フレーム部分だけで文字数制限を超えています ({frame_length=})"
            raise ValueError(msg)

        if abstract and len(abstract) > available:
            # 省略記号の文字数を確保して切り詰め
            abstract = abstract[: available - len(ELLIPSIS)] + ELLIPSIS

        return self._build_document(
            session=session,
            abstract=abstract,
            hashtags=hashtags,
        )

    def _calculate_frame_length(
        self,
        session: Session,
        hashtags: tuple[str, ...],
    ) -> int:
        placeholder = "X"
        doc_with_placeholder = self._build_document(
            session=session,
            abstract=placeholder,
            hashtags=hashtags,
        )

        return len(doc_with_placeholder) - len(placeholder)

    def _build_document(
        self,
        session: Session,
        abstract: str,
        hashtags: tuple[str, ...],
    ) -> str:
        doc = Document()

        if speakers_str := YouTubeTitleBuilder.format_speakers_full(
            speakers=session.speakers
        ):
            doc.add_paragraph(text=f"Speaker: {speakers_str}")

        if abstract:
            doc.add_raw(text=abstract)

        doc.add_horizontal_rule()

        if session.url:
            doc.add_paragraph(text=session.url)

        if hashtags:
            doc.add_paragraph(text=" ".join(hashtags))

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
