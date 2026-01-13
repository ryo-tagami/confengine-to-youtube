"""セッションエンティティ"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from datetime import datetime


@dataclass
class Session:
    """カンファレンスセッション"""

    title: str
    timeslot: datetime
    room: str
    track: str
    speakers: list[str]
    abstract: str
    url: str

    @property
    def has_content(self) -> bool:
        """出力可能なコンテンツがあるかどうか"""
        return bool(self.abstract)
