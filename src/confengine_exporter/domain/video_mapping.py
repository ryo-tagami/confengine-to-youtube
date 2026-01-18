"""YouTube動画マッピングエンティティ"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from datetime import datetime


@dataclass
class VideoMapping:
    timeslot: datetime
    room: str
    video_id: str


@dataclass
class MappingConfig:
    mappings: list[VideoMapping]

    def find_mapping(
        self,
        timeslot: datetime,
        room: str,
    ) -> VideoMapping | None:
        for mapping in self.mappings:
            if mapping.timeslot == timeslot and mapping.room == room:
                return mapping

        return None

    def find_unused(
        self,
        used_keys: set[tuple[datetime, str]],
    ) -> list[VideoMapping]:
        return [m for m in self.mappings if (m.timeslot, m.room) not in used_keys]
