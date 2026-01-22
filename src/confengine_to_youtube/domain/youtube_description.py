"""YouTube説明文値オブジェクト"""

from __future__ import annotations

import re
from dataclasses import InitVar, dataclass
from typing import ClassVar, final

from returns.result import Failure, Result, Success

from confengine_to_youtube.domain._sentinel import SENTINEL, Sentinel
from confengine_to_youtube.domain.errors import DescriptionTooLongError


@final
@dataclass(frozen=True)
class YouTubeDescription:
    """YouTube動画説明文 (最大5000文字)

    このクラスは直接インスタンス化できない。
    create() スマートコンストラクタを使用すること。
    """

    MAX_LENGTH: ClassVar[int] = 5000

    value: str
    _token: InitVar[Sentinel | None] = None

    def __post_init__(self, _token: Sentinel | None) -> None:  # noqa: D105
        if _token is not SENTINEL:
            msg = (
                "Do not instantiate YouTubeDescription() directly. "
                "Use create() instead."
            )
            raise TypeError(msg)

    def __str__(self) -> str:  # noqa: D105
        return self.value

    @classmethod
    def create(cls, value: str) -> Result[YouTubeDescription, DescriptionTooLongError]:
        """スマートコンストラクタ"""
        if len(value) > cls.MAX_LENGTH:
            return Failure(
                DescriptionTooLongError(length=len(value), max_length=cls.MAX_LENGTH),
            )

        return Success(cls(value=value, _token=SENTINEL))

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
