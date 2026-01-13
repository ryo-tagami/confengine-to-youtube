"""セッションMarkdownビルダー"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from snakemd import Document

if TYPE_CHECKING:
    from confengine_exporter.domain.session import Session


@dataclass
class MarkdownOptions:
    """Markdown生成オプション"""

    hashtags: str
    footer_text: str


class SessionMarkdownBuilder:
    """セッション情報からMarkdownを生成"""

    def __init__(self, options: MarkdownOptions) -> None:
        self.options = options

    def build(self, session: Session) -> str:
        """セッションからMarkdownを生成"""
        doc = Document()

        # タイトル
        if session.title:
            doc.add_heading(text=session.title, level=1)

        # 登壇者名
        if session.speakers:
            speakers_str = ", ".join(session.speakers)
            doc.add_paragraph(f"Speaker: {speakers_str}")

        # 本文 - abstract
        doc.add_raw(session.abstract)

        # 区切り線
        doc.add_horizontal_rule()

        # ConfEngineへのリンク
        if session.url:
            doc.add_paragraph(session.url)

        # ハッシュタグ
        if self.options.hashtags:
            doc.add_paragraph(self.options.hashtags)

        # 区切り線
        doc.add_horizontal_rule()

        # 末尾に固定文言
        if self.options.footer_text:
            doc.add_paragraph(self.options.footer_text)

        return str(doc)
