"""共通フィクスチャ"""

from datetime import UTC, datetime

import pytest

from confengine_to_youtube.domain.abstract_markdown import AbstractMarkdown
from confengine_to_youtube.domain.schedule_slot import ScheduleSlot
from confengine_to_youtube.domain.session import Session, Speaker


@pytest.fixture
def sample_session() -> Session:
    """テスト用のセッション"""
    return Session(
        slot=ScheduleSlot(
            timeslot=datetime(
                year=2026, month=1, day=7, hour=10, minute=0, second=0, tzinfo=UTC
            ),
            room="Hall A",
        ),
        title="Sample Session",
        track="Track 1",
        speakers=[
            Speaker(first_name="Speaker", last_name="A"),
            Speaker(first_name="Speaker", last_name="B"),
        ],
        abstract=AbstractMarkdown(content="This is a sample abstract."),
        url="https://example.com/session/1",
    )


@pytest.fixture
def empty_session() -> Session:
    """abstractが空のセッション"""
    return Session(
        slot=ScheduleSlot(
            timeslot=datetime(
                year=2026, month=1, day=7, hour=9, minute=0, second=0, tzinfo=UTC
            ),
            room="Hall A",
        ),
        title="Empty Session",
        track="Track 1",
        speakers=[],
        abstract=AbstractMarkdown(content=""),
        url="https://example.com/session/2",
    )
