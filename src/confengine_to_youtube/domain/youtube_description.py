"""YouTube説明文値オブジェクト"""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

from returns.result import Failure, Result, Success

from confengine_to_youtube.domain.errors import DescriptionValidationError


@dataclass(frozen=True)
class YouTubeDescription:
    """YouTube動画説明文 (最大5000文字)"""

    MAX_LENGTH: ClassVar[int] = 5000

    value: str

    def __post_init__(self) -> None:
        """バリデーションを実行"""
        if len(self.value) > self.MAX_LENGTH:
            msg = f"説明文は{self.MAX_LENGTH}文字以内 (現在: {len(self.value)}文字)"
            raise DescriptionValidationError(message=msg)

    @classmethod
    def create(
        cls,
        value: str,
    ) -> Result[YouTubeDescription, DescriptionValidationError]:
        """バリデーション付きでインスタンスを作成 (Result型で返す)"""
        try:
            return Success(cls(value=value))
        except DescriptionValidationError as e:
            return Failure(e)

    def __str__(self) -> str:  # noqa: D105
        return self.value
