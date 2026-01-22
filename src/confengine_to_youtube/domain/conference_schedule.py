"""カンファレンススケジュール集約"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from zoneinfo import ZoneInfo

    from confengine_to_youtube.domain.session import Session


@dataclass(frozen=True)
class ConferenceSchedule:
    """カンファレンスのスケジュール情報を集約するルートエンティティ"""

    conf_id: str
    timezone: ZoneInfo
    sessions: tuple[Session, ...]
