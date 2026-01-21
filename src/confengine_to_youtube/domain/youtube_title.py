"""YouTubeタイトル値オブジェクト"""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

from returns.result import Failure, Result, Success

from confengine_to_youtube.domain.errors import TitleValidationError


@dataclass(frozen=True)
class YouTubeTitle:
    """YouTube動画タイトル (最大100文字)"""

    MAX_LENGTH: ClassVar[int] = 100

    value: str

    def __post_init__(self) -> None:
        """バリデーションを実行"""
        if not self.value:
            raise TitleValidationError(message="タイトルは必須です")
        if len(self.value) > self.MAX_LENGTH:
            msg = f"タイトルは{self.MAX_LENGTH}文字以内 (現在: {len(self.value)}文字)"
            raise TitleValidationError(message=msg)

    @classmethod
    def create(cls, value: str) -> Result[YouTubeTitle, TitleValidationError]:
        """バリデーション付きでインスタンスを作成 (Result型で返す)"""
        try:
            return Success(cls(value=value))
        except TitleValidationError as e:
            return Failure(e)

    def __str__(self) -> str:  # noqa: D105
        return self.value
