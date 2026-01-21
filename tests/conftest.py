"""共通フィクスチャ"""

from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest
from returns.io import IOResult  # noqa: TC002
from returns.unsafe import unsafe_perform_io

from confengine_to_youtube.adapters.mapping_file_reader import MappingFileReader
from confengine_to_youtube.adapters.youtube_description_builder import (
    YouTubeDescriptionBuilder,
)
from confengine_to_youtube.adapters.youtube_title_builder import YouTubeTitleBuilder
from confengine_to_youtube.domain.abstract_markdown import AbstractMarkdown
from confengine_to_youtube.domain.schedule_slot import ScheduleSlot
from confengine_to_youtube.domain.session import Session, Speaker


def extract_io_success[T](io_result: IOResult[T, Exception]) -> T:
    """テスト用: IOResultから成功値を取り出す

    is_successful() で成功を確認した後に呼び出すこと。
    失敗時は UnwrapFailedError が発生する。
    """
    return unsafe_perform_io(io_result.unwrap())


def create_session(  # noqa: PLR0913
    title: str,
    speakers: Sequence[tuple[str, str]],
    abstract: str,
    timeslot: datetime,
    room: str,
    url: str,
) -> Session:
    """テスト用Sessionを作成するヘルパー"""
    return Session.create(
        slot=ScheduleSlot.create(timeslot=timeslot, room=room).unwrap(),
        title=title,
        track="Track 1",
        speakers=tuple(
            Speaker.create(first_name=first, last_name=last).unwrap()
            for first, last in speakers
        ),
        abstract=AbstractMarkdown.create(content=abstract).unwrap(),
        url=url,
    ).unwrap()


@pytest.fixture
def sample_session() -> Session:
    """テスト用のセッション"""
    return Session.create(
        slot=ScheduleSlot.create(
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
        ).unwrap(),
        title="Sample Session",
        track="Track 1",
        speakers=(
            Speaker.create(first_name="Speaker", last_name="A").unwrap(),
            Speaker.create(first_name="Speaker", last_name="B").unwrap(),
        ),
        abstract=AbstractMarkdown.create(content="This is a sample abstract.").unwrap(),
        url="https://example.com/session/1",
    ).unwrap()


@pytest.fixture
def empty_session() -> Session:
    """abstractが空のセッション"""
    return Session.create(
        slot=ScheduleSlot.create(
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
        ).unwrap(),
        title="Empty Session",
        track="Track 1",
        speakers=(),
        abstract=AbstractMarkdown.create(content="").unwrap(),
        url="https://example.com/session/2",
    ).unwrap()


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
