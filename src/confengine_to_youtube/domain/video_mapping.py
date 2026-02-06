"""YouTube動画マッピングエンティティ"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from confengine_to_youtube.domain.schedule_slot import ScheduleSlot
    from confengine_to_youtube.domain.session_override import SessionOverride


@dataclass(frozen=True)
class VideoMapping:
    slot: ScheduleSlot
    video_id: str
    override: SessionOverride | None = None


@dataclass(frozen=True)
class MappingConfig:
    conf_id: str
    playlist_id: str
    mappings: frozenset[VideoMapping]
    hashtags: tuple[str, ...]
    footer: str

    def find_mapping(self, slot: ScheduleSlot) -> VideoMapping | None:
        # 線形検索だが、セッション数は通常数百以下のため実用上問題なし
        for mapping in self.mappings:
            if mapping.slot == slot:
                return mapping

        return None

    def find_unused(self, used_slots: set[ScheduleSlot]) -> frozenset[VideoMapping]:
        return frozenset(m for m in self.mappings if m.slot not in used_slots)
