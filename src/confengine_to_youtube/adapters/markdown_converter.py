"""HTML から Markdown への変換アダプター"""

from __future__ import annotations

import re

from markdownify import markdownify

from confengine_to_youtube.domain.session_abstract import SessionAbstract


class MarkdownConverter:
    """HTML から Markdown への変換"""

    def convert(self, html: str) -> SessionAbstract:
        """HTML を Markdown に変換する"""
        if not html:
            return SessionAbstract(content="")

        text = markdownify(html=html, heading_style="ATX", strip=["script", "style"])
        text = text.strip()
        text = re.sub(pattern=r"\n{3,}", repl="\n\n", string=text)

        return SessionAbstract(content=text)
