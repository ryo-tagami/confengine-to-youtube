"""カンファレンススケジュール集約"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from zoneinfo import ZoneInfo

    from confengine_to_youtube.domain.schedule_slot import ScheduleSlot
    from confengine_to_youtube.domain.session import Session


@dataclass(frozen=True)
class ConferenceSchedule:
    """カンファレンスのスケジュール情報を集約するルートエンティティ"""

    conf_id: str
    timezone: ZoneInfo
    sessions: tuple[Session, ...]

    def __post_init__(self) -> None:
        """不変条件を検証"""
        self._validate_no_duplicate_slots()

    def _validate_no_duplicate_slots(self) -> None:
        """同一スロットに複数セッションが存在しないことを検証"""
        seen: set[ScheduleSlot] = set()

        for session in self.sessions:
            if session.slot in seen:
                msg = f"Duplicate slot detected: {session.slot}"
                raise ValueError(msg)

            seen.add(session.slot)

    def sessions_with_content(self) -> tuple[Session, ...]:
        """コンテンツのあるセッションのみ取得"""
        return tuple(s for s in self.sessions if s.has_content)
