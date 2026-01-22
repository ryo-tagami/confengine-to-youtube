"""共通フィクスチャ"""

from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

from confengine_to_youtube.adapters.mapping_file_reader import MappingFileReader
from confengine_to_youtube.domain.schedule_slot import ScheduleSlot
from confengine_to_youtube.domain.session import Session, Speaker
from confengine_to_youtube.domain.session_abstract import SessionAbstract


def create_session(  # noqa: PLR0913
    title: str,
    speakers: Sequence[tuple[str, str]],
    abstract: str,
    timeslot: datetime,
    room: str,
    url: str,
) -> Session:
    """テスト用Sessionを作成するヘルパー"""
    return Session(
        slot=ScheduleSlot(timeslot=timeslot, room=room),
        title=title,
        track="Track 1",
        speakers=tuple(
            Speaker(first_name=first, last_name=last) for first, last in speakers
        ),
        abstract=SessionAbstract(content=abstract),
        url=url,
    )


@pytest.fixture
def sample_session() -> Session:
    """テスト用のセッション"""
    return Session(
        slot=ScheduleSlot(
            timeslot=datetime(
                year=2026,
                month=1,
                day=7,
                hour=10,
                minute=0,
                second=0,
                tzinfo=UTC,
            ),
            room="Hall A",
        ),
        title="Sample Session",
        track="Track 1",
        speakers=(
            Speaker(first_name="Speaker", last_name="A"),
            Speaker(first_name="Speaker", last_name="B"),
        ),
        abstract=SessionAbstract(content="This is a sample abstract."),
        url="https://example.com/session/1",
    )


@pytest.fixture
def empty_session() -> Session:
    """abstractが空のセッション"""
    return Session(
        slot=ScheduleSlot(
            timeslot=datetime(
                year=2026,
                month=1,
                day=7,
                hour=9,
                minute=0,
                second=0,
                tzinfo=UTC,
            ),
            room="Hall A",
        ),
        title="Empty Session",
        track="Track 1",
        speakers=(),
        abstract=SessionAbstract(content=""),
        url="https://example.com/session/2",
    )


@pytest.fixture
def jst() -> ZoneInfo:
    """日本標準時のタイムゾーン"""
    return ZoneInfo(key="Asia/Tokyo")


@pytest.fixture
def mapping_reader() -> MappingFileReader:
    """MappingFileReader のインスタンス"""
    return MappingFileReader()


def write_yaml_file(tmp_path: Path, content: str, filename: str) -> Path:
    """テスト用YAMLファイルを作成するヘルパー"""
    yaml_file = tmp_path / filename
    yaml_file.write_text(data=content, encoding="utf-8")
    return yaml_file
