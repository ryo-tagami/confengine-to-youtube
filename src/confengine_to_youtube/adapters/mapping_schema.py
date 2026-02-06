"""マッピングファイルのPydanticスキーマ定義

MappingFileReaderとMappingFileWriterで共有される。
"""

from __future__ import annotations

from datetime import date, datetime, time
from typing import TYPE_CHECKING, Self

from pydantic import BaseModel, ConfigDict, Field, RootModel, model_validator

from confengine_to_youtube.domain.constants import TITLE_SPEAKER_SEPARATOR
from confengine_to_youtube.domain.schedule_slot import ScheduleSlot
from confengine_to_youtube.domain.session_abstract import SessionAbstract
from confengine_to_youtube.domain.session_override import SessionOverride
from confengine_to_youtube.domain.speaker import Speaker
from confengine_to_youtube.domain.video_mapping import MappingConfig, VideoMapping

if TYPE_CHECKING:
    from zoneinfo import ZoneInfo

    from confengine_to_youtube.domain.conference_schedule import ConferenceSchedule

# Reader用スキーマ


class SpeakerOverrideSchema(BaseModel):
    """スピーカーオーバーライドのスキーマ (Reader用)"""

    model_config = ConfigDict(frozen=True)

    first_name: str = ""
    last_name: str = ""


class SessionEntrySchema(BaseModel):
    """セッションエントリのスキーマ (Reader用)"""

    model_config = ConfigDict(frozen=True)

    # YouTube video IDの形式は公式に文書化されていないためバリデーションしない
    video_id: str
    speakers: list[SpeakerOverrideSchema] | None = None
    abstract: str | None = None


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
        cls,
        data: dict[str | date | datetime, object],
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


class MappingFileBaseSchema(BaseModel):
    """マッピングファイルの共通基底スキーマ"""

    model_config = ConfigDict(frozen=True)

    conf_id: str
    hashtags: list[str] = Field(default_factory=list)
    footer: str = ""


class MappingFileSchema(MappingFileBaseSchema):
    """マッピングファイルのルートスキーマ (Reader用)"""

    playlist_id: str
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
                            override=_build_session_override(entry=session),
                        ),
                    )

        return MappingConfig(
            conf_id=self.conf_id,
            playlist_id=self.playlist_id,
            mappings=frozenset(mappings),
            hashtags=tuple(self.hashtags),
            footer=self.footer,
        )


def _build_session_override(entry: SessionEntrySchema) -> SessionOverride | None:
    """SessionEntrySchemaからSessionOverrideを構築する

    speakers/abstractがどちらもNoneの場合はNoneを返す。
    """
    if entry.speakers is None and entry.abstract is None:
        return None

    speakers = (
        tuple(
            Speaker(first_name=s.first_name, last_name=s.last_name)
            for s in entry.speakers
        )
        if entry.speakers is not None
        else None
    )
    abstract = (
        SessionAbstract(content=entry.abstract) if entry.abstract is not None else None
    )

    return SessionOverride(speakers=speakers, abstract=abstract)


# Writer用スキーマ


class SessionEntryWithComment(SessionEntrySchema):
    """セッションエントリのスキーマ (Writer用: コメント情報付き)

    commentフィールドはYAML出力時にはコメントとして出力され、
    フィールドとしては出力されない。
    has_contentがFalseの場合、speakers/abstractのプレースホルダーが生成される。
    """

    comment: str
    has_content: bool = True


class TimeSlotsWithCommentSchema(RootModel[dict[time, SessionEntryWithComment]]):
    """時刻 -> セッションエントリのマッピング (Writer用)"""

    model_config = ConfigDict(frozen=True)


class RoomSlotsWithCommentSchema(RootModel[dict[str, TimeSlotsWithCommentSchema]]):
    """部屋名 -> 時刻マッピングのマッピング (Writer用)"""

    model_config = ConfigDict(frozen=True)


class DateSlotsWithCommentSchema(RootModel[dict[date, RoomSlotsWithCommentSchema]]):
    """日付 -> 部屋マッピングのマッピング (Writer用)"""

    model_config = ConfigDict(frozen=True)


class MappingFileWithCommentSchema(MappingFileBaseSchema):
    """マッピングファイルのルートスキーマ (Writer用)"""

    playlist_id: str = ""
    sessions: DateSlotsWithCommentSchema

    @classmethod
    def from_conference_schedule(
        cls,
        schedule: ConferenceSchedule,
    ) -> Self:
        """ConferenceScheduleからマッピングファイルのテンプレートを生成する。

        hashtagsとfooterは空で初期化される。
        生成されたYAMLファイルをユーザーが手動で編集することを想定している。
        """
        date_slots: dict[date, RoomSlotsWithCommentSchema] = {}

        for session in schedule.sessions:
            session_date = session.slot.timeslot.date()
            session_time = session.slot.timeslot.time()
            room = session.slot.room

            if session.speakers_full:
                comment = (
                    f"{session.title}{TITLE_SPEAKER_SEPARATOR}{session.speakers_full}"
                )
            else:
                comment = session.title

            room_slots = date_slots.setdefault(
                session_date,
                RoomSlotsWithCommentSchema(root={}),
            ).root
            time_slots = room_slots.setdefault(
                room,
                TimeSlotsWithCommentSchema(root={}),
            ).root

            time_slots[session_time] = SessionEntryWithComment(
                video_id="",
                comment=comment,
                has_content=session.has_content,
            )

        return cls(
            conf_id=schedule.conf_id,
            hashtags=[],
            footer="",
            sessions=DateSlotsWithCommentSchema(root=date_slots),
        )
