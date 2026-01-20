"""セッションエンティティ"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from confengine_to_youtube.domain.abstract_markdown import AbstractMarkdown
    from confengine_to_youtube.domain.schedule_slot import ScheduleSlot


@dataclass(frozen=True)
class Speaker:
    """スピーカー情報"""

    first_name: str
    last_name: str

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
            initials = " ".join(f"{part[0]}." for part in self.first_name.split())
            return f"{initials} {self.last_name}".strip()

        return self.last_name


@dataclass(frozen=True)
class Session:
    slot: ScheduleSlot
    title: str
    track: str
    speakers: list[Speaker]
    abstract: AbstractMarkdown
    url: str

    @property
    def has_content(self) -> bool:
        return bool(self.abstract.content)
