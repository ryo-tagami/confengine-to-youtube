"""YouTubeタイトル値オブジェクト"""

from __future__ import annotations

from dataclasses import InitVar, dataclass
from typing import TYPE_CHECKING, ClassVar, final

from returns.result import Failure, Result, Success

from confengine_to_youtube.domain._sentinel import SENTINEL, Sentinel
from confengine_to_youtube.domain.errors import TitleEmptyError, TitleTooLongError

if TYPE_CHECKING:
    from confengine_to_youtube.domain.errors import TitleError


@final
@dataclass(frozen=True)
class YouTubeTitle:
    """YouTube動画タイトル (最大100文字)

    このクラスは直接インスタンス化できない。
    create() スマートコンストラクタを使用すること。
    """

    MAX_LENGTH: ClassVar[int] = 100

    value: str
    _token: InitVar[Sentinel | None] = None

    def __post_init__(self, _token: Sentinel | None) -> None:  # noqa: D105
        if _token is not SENTINEL:
            msg = "Do not instantiate YouTubeTitle() directly. Use create() instead."
            raise TypeError(msg)

    def __str__(self) -> str:  # noqa: D105
        return self.value

    @classmethod
    def create(cls, value: str) -> Result[YouTubeTitle, TitleError]:
        """スマートコンストラクタ"""
        if not value:
            return Failure(TitleEmptyError())

        if len(value) > cls.MAX_LENGTH:
            return Failure(
                TitleTooLongError(length=len(value), max_length=cls.MAX_LENGTH),
            )

        return Success(cls(value=value, _token=SENTINEL))
