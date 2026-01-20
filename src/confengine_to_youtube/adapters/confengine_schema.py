"""ConfEngine APIレスポンススキーマ"""

from __future__ import annotations

from datetime import datetime  # noqa: TC003

from pydantic import BaseModel, ConfigDict


class Speaker(BaseModel):
    """スピーカー情報"""

    model_config = ConfigDict(frozen=True)

    first_name: str
    last_name: str


class ApiSession(BaseModel):
    """APIレスポンスのセッション"""

    model_config = ConfigDict(frozen=True)

    timeslot: datetime
    title: str
    room: str
    track: str
    url: str
    abstract: str
    speakers: list[Speaker]


# スロット開始時刻 (Unixタイムスタンプ) をキーとしたセッション辞書
type SlotSessions = dict[str, list[ApiSession]]


class ScheduleDay(BaseModel):
    """スケジュール日"""

    model_config = ConfigDict(frozen=True)

    sessions: list[SlotSessions]


class DayData(BaseModel):
    """日付データ"""

    model_config = ConfigDict(frozen=True)

    schedule_days: list[ScheduleDay]


class ScheduleResponse(BaseModel):
    """APIレスポンス"""

    model_config = ConfigDict(frozen=True)

    conf_timezone: str
    conf_schedule: list[DayData]
