"""スケジュールスロット値オブジェクト"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from datetime import datetime


@dataclass(frozen=True)
class ScheduleSlot:
    """カンファレンスのスケジュールスロット (時間帯 + 部屋)"""

    timeslot: datetime
    room: str

    def __str__(self) -> str:  # noqa: D105
        return f"{self.timeslot.isoformat()}_{self.room}"
