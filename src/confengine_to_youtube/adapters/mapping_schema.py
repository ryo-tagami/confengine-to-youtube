"""マッピングファイルのPydanticスキーマ定義

MappingFileReaderとMappingFileWriterで共有される。
"""

from __future__ import annotations

from datetime import date, datetime, time
from typing import TYPE_CHECKING, Self

from pydantic import BaseModel, ConfigDict, Field, RootModel, model_validator

from confengine_to_youtube.adapters.youtube_title_builder import YouTubeTitleBuilder
from confengine_to_youtube.domain.schedule_slot import ScheduleSlot
from confengine_to_youtube.domain.video_mapping import MappingConfig, VideoMapping

if TYPE_CHECKING:
    from zoneinfo import ZoneInfo

    from confengine_to_youtube.domain.session import Session

# Reader用スキーマ


class SessionEntrySchema(BaseModel):
    """セッションエントリのスキーマ (Reader用)"""

    model_config = ConfigDict(frozen=True)

    # YouTube video IDの形式は公式に文書化されていないためバリデーションしない
    video_id: str


class TimeSlotsSchema(RootModel[dict[time, SessionEntrySchema]]):
    """時刻 -> セッションエントリのマッピング"""

    model_config = ConfigDict(frozen=True)

    @model_validator(mode="before")
    @classmethod
    def parse_time_keys(cls, data: dict[str | time, object]) -> dict[time, object]:
        return {
            k if isinstance(k, time) else time.fromisoformat(k): v
            for k, v in data.items()
        }


class RoomSlotsSchema(RootModel[dict[str, TimeSlotsSchema]]):
    """部屋名 -> 時刻マッピングのマッピング"""

    model_config = ConfigDict(frozen=True)


class DateSlotsSchema(RootModel[dict[date, RoomSlotsSchema]]):
    """日付 -> 部屋マッピングのマッピング"""

    model_config = ConfigDict(frozen=True)

    @model_validator(mode="before")
    @classmethod
    def parse_date_keys(
        cls, data: dict[str | date | datetime, object]
    ) -> dict[date, object]:
        # datetimeはdateのサブクラスなので、先にdatetimeをチェックする
        result: dict[date, object] = {}

        for k, v in data.items():
            if isinstance(k, datetime):
                key = k.date()
            elif isinstance(k, date):
                key = k
            else:
                key = date.fromisoformat(k)

            result[key] = v

        return result


class MappingFileSchema(BaseModel):
    """マッピングファイルのルートスキーマ (Reader用)"""

    model_config = ConfigDict(frozen=True)

    hashtags: list[str] = Field(default_factory=list)
    footer: str = ""
    sessions: DateSlotsSchema

    def to_domain(self, timezone: ZoneInfo) -> MappingConfig:
        """ドメインオブジェクトに変換"""
        mappings: list[VideoMapping] = []

        for parsed_date, rooms in self.sessions.root.items():
            for room, times in rooms.root.items():
                for parsed_time, session in times.root.items():
                    slot = ScheduleSlot(
                        timeslot=datetime.combine(
                            date=parsed_date,
                            time=parsed_time,
                            tzinfo=timezone,
                        ),
                        room=room,
                    )
                    mappings.append(
                        VideoMapping(
                            slot=slot,
                            video_id=session.video_id,
                        )
                    )

        return MappingConfig(
            mappings=mappings,
            hashtags=tuple(self.hashtags),
            footer=self.footer,
        )


# Writer用スキーマ


class SessionEntryWithComment(SessionEntrySchema):
    """セッションエントリのスキーマ (Writer用: コメント情報付き)

    commentフィールドはYAML出力時にはコメントとして出力され、
    フィールドとしては出力されない。
    """

    comment: str


class TimeSlotsWithCommentSchema(RootModel[dict[time, SessionEntryWithComment]]):
    """時刻 -> セッションエントリのマッピング (Writer用)"""

    model_config = ConfigDict(frozen=True)


class RoomSlotsWithCommentSchema(RootModel[dict[str, TimeSlotsWithCommentSchema]]):
    """部屋名 -> 時刻マッピングのマッピング (Writer用)"""

    model_config = ConfigDict(frozen=True)


class DateSlotsWithCommentSchema(RootModel[dict[date, RoomSlotsWithCommentSchema]]):
    """日付 -> 部屋マッピングのマッピング (Writer用)"""

    model_config = ConfigDict(frozen=True)


class MappingFileWithCommentSchema(BaseModel):
    """マッピングファイルのルートスキーマ (Writer用)"""

    model_config = ConfigDict(frozen=True)

    hashtags: list[str] = Field(default_factory=list)
    footer: str = ""
    sessions: DateSlotsWithCommentSchema

    @classmethod
    def from_sessions(
        cls,
        sessions: list[Session],
    ) -> Self:
        """Sessionリストからマッピングファイルのテンプレートを生成する。

        hashtagsとfooterは空で初期化される。
        生成されたYAMLファイルをユーザーが手動で編集することを想定している。
        """
        date_slots: dict[date, RoomSlotsWithCommentSchema] = {}

        for session in sessions:
            session_date = session.slot.timeslot.date()
            session_time = session.slot.timeslot.time()
            room = session.slot.room

            if speakers_str := YouTubeTitleBuilder.format_speakers_full(
                speakers=session.speakers
            ):
                comment = YouTubeTitleBuilder.combine(
                    title=session.title,
                    speaker_part=speakers_str,
                )
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

        return cls(
            hashtags=[],
            footer="",
            sessions=DateSlotsWithCommentSchema(root=date_slots),
        )
