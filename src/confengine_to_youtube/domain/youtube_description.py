"""YouTube説明文値オブジェクト"""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

from returns.result import Failure, Result, Success

from confengine_to_youtube.domain.errors import DescriptionValidationError
from confengine_to_youtube.domain.sealed import (
    _SEALED,
    _SealedToken,
    sealed_field,
    validate_sealed,
)


@dataclass(frozen=True)
class YouTubeDescription:
    """YouTube動画説明文 (最大5000文字)"""

    MAX_LENGTH: ClassVar[int] = 5000

    value: str
    _sealed: _SealedToken | None = sealed_field()  # noqa: RUF009

    def __post_init__(self) -> None:
        validate_sealed(instance=self, token=self._sealed)

    @classmethod
    def create(
        cls,
        value: str,
    ) -> Result[YouTubeDescription, DescriptionValidationError]:
        if len(value) > cls.MAX_LENGTH:
            msg = f"説明文は{cls.MAX_LENGTH}文字以内 (現在: {len(value)}文字)"
            return Failure(DescriptionValidationError(message=msg))
        return Success(cls(value=value, _sealed=_SEALED))

    def __str__(self) -> str:
        return self.value
