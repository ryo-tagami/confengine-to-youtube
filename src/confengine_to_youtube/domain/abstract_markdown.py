"""セッション概要 (Markdown形式) 値オブジェクト"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Never

from returns.result import Result, Success

from confengine_to_youtube.domain.sealed import (
    _SEALED,
    _SealedToken,
    sealed_field,
    validate_sealed,
)


@dataclass(frozen=True)
class AbstractMarkdown:
    """セッション概要 (Markdown形式)"""

    content: str
    _sealed: _SealedToken | None = sealed_field()  # noqa: RUF009

    def __post_init__(self) -> None:
        validate_sealed(instance=self, token=self._sealed)

    @classmethod
    def create(cls, content: str) -> Result[AbstractMarkdown, Never]:
        return Success(cls(content=content, _sealed=_SEALED))

    def __str__(self) -> str:
        return self.content
