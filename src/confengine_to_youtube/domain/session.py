"""セッションエンティティ"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from confengine_to_youtube.domain.schedule_slot import ScheduleSlot
    from confengine_to_youtube.domain.session_abstract import SessionAbstract
    from confengine_to_youtube.domain.speaker import Speaker


@dataclass(frozen=True)
class Session:
    slot: ScheduleSlot
    title: str
    track: str
    speakers: tuple[Speaker, ...]
    abstract: SessionAbstract
    url: str

    def __post_init__(self) -> None:
        """タイトルが空でないことを検証"""
        if not self.title:
            msg = "Session title must not be empty"
            raise ValueError(msg)

    @property
    def has_content(self) -> bool:
        return bool(self.abstract.content)

    @property
    def speakers_full(self) -> str:
        """スピーカー部分をフルネームで生成"""
        return ", ".join(s.full_name for s in self.speakers if s.full_name)

    @property
    def speakers_initials(self) -> str:
        """スピーカー部分をイニシャル表記で生成"""
        return ", ".join(s.initial_name for s in self.speakers if s.initial_name)

    @property
    def speakers_last_name(self) -> str:
        """スピーカー部分をラストネームのみで生成"""
        return ", ".join(s.last_name for s in self.speakers if s.last_name)
