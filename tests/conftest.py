"""共通フィクスチャ"""

from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

from confengine_to_youtube.adapters.mapping_file_reader import MappingFileReader
from confengine_to_youtube.adapters.youtube_description_builder import (
    YouTubeDescriptionBuilder,
)
from confengine_to_youtube.adapters.youtube_title_builder import YouTubeTitleBuilder
from confengine_to_youtube.domain.abstract_markdown import AbstractMarkdown
from confengine_to_youtube.domain.schedule_slot import ScheduleSlot
from confengine_to_youtube.domain.session import Session, Speaker


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
        abstract=AbstractMarkdown(content=abstract),
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
        abstract=AbstractMarkdown(content="This is a sample abstract."),
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
        abstract=AbstractMarkdown(content=""),
        url="https://example.com/session/2",
    )


@pytest.fixture
def title_builder() -> YouTubeTitleBuilder:
    """YouTubeTitleBuilder のインスタンス"""
    return YouTubeTitleBuilder()


@pytest.fixture
def description_builder() -> YouTubeDescriptionBuilder:
    """YouTubeDescriptionBuilder のインスタンス"""
    return YouTubeDescriptionBuilder()


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
