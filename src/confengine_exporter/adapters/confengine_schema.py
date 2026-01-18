"""ConfEngine APIレスポンススキーマ"""

from __future__ import annotations

import re
from datetime import datetime  # noqa: TC003

from markdownify import markdownify as md
from pydantic import BaseModel, computed_field


class Speaker(BaseModel):
    """スピーカー情報"""

    name: str


class ApiSession(BaseModel):
    """APIレスポンスのセッション"""

    timeslot: datetime
    title: str
    room: str
    track: str
    url: str
    abstract: str
    speakers: list[Speaker]

    @computed_field  # type: ignore[prop-decorator]
    @property
    def speaker_names(self) -> list[str]:
        """スピーカー名のリストを取得"""
        return [s.name for s in self.speakers if s.name]

    @computed_field  # type: ignore[prop-decorator]
    @property
    def abstract_markdown(self) -> str:
        """abstractをMarkdownに変換"""
        if not self.abstract:
            return ""

        text = md(html=self.abstract, heading_style="ATX", strip=["script", "style"])
        text = text.strip()
        text = text.replace("\\n", "\n")
        text = re.sub(pattern=r"\n{3,}", repl="\n\n", string=text)

        return text  # noqa: RET504


# スロット開始時刻 (Unixタイムスタンプ) をキーとしたセッション辞書
type SlotSessions = dict[str, list[ApiSession]]


class ScheduleDay(BaseModel):
    """スケジュール日"""

    sessions: list[SlotSessions]


class DayData(BaseModel):
    """日付データ"""

    schedule_days: list[ScheduleDay]


class ScheduleResponse(BaseModel):
    """APIレスポンス"""

    conf_timezone: str
    conf_schedule: list[DayData]
