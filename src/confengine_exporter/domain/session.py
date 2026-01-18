"""セッションエンティティ"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from datetime import datetime


@dataclass(frozen=True)
class Session:
    title: str
    timeslot: datetime
    room: str
    track: str
    speakers: list[str]
    abstract: str
    url: str

    @property
    def has_content(self) -> bool:
        return bool(self.abstract)
