"""マッピングファイルのPydanticスキーマ定義

MappingFileReaderとMappingFileWriterで共有される。
"""

from __future__ import annotations

from datetime import date, datetime, time
from typing import TYPE_CHECKING, Self

from pydantic import BaseModel, RootModel, model_validator

from confengine_exporter.domain.video_mapping import MappingConfig, VideoMapping

if TYPE_CHECKING:
    from zoneinfo import ZoneInfo

    from confengine_exporter.domain.session import Session

# Reader用スキーマ


class SessionEntrySchema(BaseModel):
    """セッションエントリのスキーマ (Reader用)"""

    video_id: str


class TimeSlotsSchema(RootModel[dict[time, SessionEntrySchema]]):
    """時刻 -> セッションエントリのマッピング"""

    @model_validator(mode="before")
    @classmethod
    def parse_time_keys(cls, data: dict[str, object]) -> dict[time, object]:
        result = {}
        for k, v in data.items():
            if isinstance(k, time):
                result[k] = v
            else:
                result[time.fromisoformat(k)] = v
        return result


class RoomSlotsSchema(RootModel[dict[str, TimeSlotsSchema]]):
    """部屋名 -> 時刻マッピングのマッピング"""


class DateSlotsSchema(RootModel[dict[date, RoomSlotsSchema]]):
    """日付 -> 部屋マッピングのマッピング"""

    @model_validator(mode="before")
    @classmethod
    def parse_date_keys(cls, data: dict[str, object]) -> dict[date, object]:
        result = {}
        for k, v in data.items():
            if isinstance(k, date):
                result[k] = v
            else:
                result[date.fromisoformat(k)] = v
        return result


class MappingFileSchema(BaseModel):
    """マッピングファイルのルートスキーマ (Reader用)"""

    sessions: DateSlotsSchema

    def to_domain(self, timezone: ZoneInfo) -> MappingConfig:
        """ドメインオブジェクトに変換"""
        mappings: list[VideoMapping] = []

        for parsed_date, rooms in self.sessions.root.items():
            for room, times in rooms.root.items():
                for parsed_time, session in times.root.items():
                    timeslot = datetime.combine(
                        date=parsed_date,
                        time=parsed_time,
                        tzinfo=timezone,
                    )
                    mappings.append(
                        VideoMapping(
                            timeslot=timeslot,
                            room=room,
                            video_id=session.video_id,
                        )
                    )

        return MappingConfig(mappings=mappings)


# Writer用スキーマ


class SessionEntryWithComment(SessionEntrySchema):
    """セッションエントリのスキーマ (Writer用: コメント情報付き)

    commentフィールドはYAML出力時にはコメントとして出力され、
    フィールドとしては出力されない。
    """

    comment: str = ""


class TimeSlotsWithCommentSchema(RootModel[dict[time, SessionEntryWithComment]]):
    """時刻 -> セッションエントリのマッピング (Writer用)"""


class RoomSlotsWithCommentSchema(RootModel[dict[str, TimeSlotsWithCommentSchema]]):
    """部屋名 -> 時刻マッピングのマッピング (Writer用)"""


class DateSlotsWithCommentSchema(RootModel[dict[date, RoomSlotsWithCommentSchema]]):
    """日付 -> 部屋マッピングのマッピング (Writer用)"""


class MappingFileWithCommentSchema(BaseModel):
    """マッピングファイルのルートスキーマ (Writer用)"""

    sessions: DateSlotsWithCommentSchema

    @classmethod
    def from_sessions(cls, sessions: list[Session]) -> Self:
        """Sessionリストからスキーマを構築"""
        date_slots: dict[date, RoomSlotsWithCommentSchema] = {}

        for session in sessions:
            session_date = session.timeslot.date()
            session_time = session.timeslot.time()
            room = session.room
            if session.speakers:
                comment = f"{session.title} / {', '.join(session.speakers)}"
            else:
                comment = session.title

            room_slots = date_slots.setdefault(
                session_date, RoomSlotsWithCommentSchema(root={})
            ).root
            time_slots = room_slots.setdefault(
                room, TimeSlotsWithCommentSchema(root={})
            ).root

            # 重複チェック
            if session_time in time_slots:
                existing = time_slots[session_time]
                msg = (
                    f"Duplicate session detected: "
                    f"{session_date} {session_time.strftime(format='%H:%M')} {room}\n"
                    f"  Existing: {existing.comment}\n"
                    f"  New: {comment}"
                )
                raise ValueError(msg)

            time_slots[session_time] = SessionEntryWithComment(
                video_id="",
                comment=comment,
            )

        return cls(sessions=DateSlotsWithCommentSchema(root=date_slots))
