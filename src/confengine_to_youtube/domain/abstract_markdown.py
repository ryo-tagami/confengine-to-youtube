"""セッション概要 (Markdown形式) 値オブジェクト"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AbstractMarkdown:
    """セッション概要 (Markdown形式)"""

    content: str

    def __str__(self) -> str:  # noqa: D105
        return self.content
