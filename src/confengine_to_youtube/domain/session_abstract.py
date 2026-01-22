"""セッション概要値オブジェクト"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SessionAbstract:
    """セッション概要 (Markdown形式のテキストを保持)"""

    content: str

    def __str__(self) -> str:  # noqa: D105
        return self.content
