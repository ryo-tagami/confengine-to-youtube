"""YouTube説明文値オブジェクト"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import ClassVar


@dataclass(frozen=True)
class YouTubeDescription:
    """YouTube動画説明文 (最大5000文字)"""

    MAX_LENGTH: ClassVar[int] = 5000

    value: str

    def __post_init__(self) -> None:  # noqa: D105
        if len(self.value) > self.MAX_LENGTH:
            msg = f"説明文は{self.MAX_LENGTH}文字以内 (現在: {len(self.value)}文字)"
            raise ValueError(msg)

    def __str__(self) -> str:  # noqa: D105
        return self.value

    @staticmethod
    def sanitize_for_youtube(text: str) -> str:
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
