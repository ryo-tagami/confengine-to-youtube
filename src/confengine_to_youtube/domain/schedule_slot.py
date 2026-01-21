"""スケジュールスロット値オブジェクト"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Never

from returns.result import Result, Success

from confengine_to_youtube.domain.sealed import (
    _SEALED,
    _SealedToken,
    sealed_field,
    validate_sealed,
)

if TYPE_CHECKING:
    from datetime import datetime


@dataclass(frozen=True)
class ScheduleSlot:
    """カンファレンスのスケジュールスロット (時間帯 + 部屋)"""

    timeslot: datetime
    room: str
    _sealed: _SealedToken | None = sealed_field()  # noqa: RUF009

    def __post_init__(self) -> None:
        validate_sealed(instance=self, token=self._sealed)

    @classmethod
    def create(cls, timeslot: datetime, room: str) -> Result[ScheduleSlot, Never]:
        return Success(cls(timeslot=timeslot, room=room, _sealed=_SEALED))

    def __str__(self) -> str:
        return f"{self.timeslot.isoformat()}_{self.room}"
