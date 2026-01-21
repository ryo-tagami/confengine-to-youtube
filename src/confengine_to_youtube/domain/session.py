"""セッションエンティティ"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Self

from returns.result import Result, Success

from confengine_to_youtube.domain.sealed import (
    _SEALED,
    _SealedToken,
    sealed_field,
    validate_sealed,
)

if TYPE_CHECKING:
    from typing import Never

    from confengine_to_youtube.domain.abstract_markdown import AbstractMarkdown
    from confengine_to_youtube.domain.schedule_slot import ScheduleSlot


@dataclass(frozen=True)
class Speaker:
    """スピーカー情報"""

    first_name: str
    last_name: str
    _sealed: _SealedToken | None = sealed_field()  # noqa: RUF009

    def __post_init__(self) -> None:
        validate_sealed(instance=self, token=self._sealed)

    @classmethod
    def create(
        cls,
        first_name: str,
        last_name: str,
    ) -> Result[Self, Never]:
        return Success(cls(first_name=first_name, last_name=last_name, _sealed=_SEALED))

    @property
    def full_name(self) -> str | None:
        """フルネームを取得 (例: "John Doe")

        first_name と last_name が両方空の場合は None を返す。
        """
        name = f"{self.first_name} {self.last_name}".strip()
        return name or None

    @property
    def initial_name(self) -> str | None:
        """イニシャル表記を取得

        例: "John Doe" -> "J. Doe", "Tze Chin Tang" -> "T. C. Tang"

        first_name と last_name が両方空の場合は None を返す。
        """
        if not self.first_name and not self.last_name:
            return None

        if self.first_name:
            # str.split() は空文字列を含まないため part[0] は安全
            initials = " ".join(f"{part[0]}." for part in self.first_name.split())
            return f"{initials} {self.last_name}".strip()

        return self.last_name


@dataclass(frozen=True)
class Session:
    slot: ScheduleSlot
    title: str
    track: str
    speakers: tuple[Speaker, ...]
    abstract: AbstractMarkdown
    url: str
    _sealed: _SealedToken | None = sealed_field()  # noqa: RUF009

    def __post_init__(self) -> None:
        validate_sealed(instance=self, token=self._sealed)

    @classmethod
    def create(  # noqa: PLR0913
        cls,
        slot: ScheduleSlot,
        title: str,
        track: str,
        speakers: tuple[Speaker, ...],
        abstract: AbstractMarkdown,
        url: str,
    ) -> Result[Self, Never]:
        return Success(
            cls(
                slot=slot,
                title=title,
                track=track,
                speakers=speakers,
                abstract=abstract,
                url=url,
                _sealed=_SEALED,
            ),
        )

    @property
    def has_content(self) -> bool:
        return bool(self.abstract.content)
