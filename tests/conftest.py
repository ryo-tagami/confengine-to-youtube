"""共通フィクスチャ"""

from datetime import UTC, datetime

import pytest

from confengine_exporter.domain.session import Session, Speaker


@pytest.fixture
def sample_session() -> Session:
    """テスト用のセッション"""
    return Session(
        title="Sample Session",
        timeslot=datetime(
            year=2026, month=1, day=7, hour=10, minute=0, second=0, tzinfo=UTC
        ),
        room="Hall A",
        track="Track 1",
        speakers=[
            Speaker(first_name="Speaker", last_name="A"),
            Speaker(first_name="Speaker", last_name="B"),
        ],
        abstract="This is a sample abstract.",
        url="https://example.com/session/1",
    )


@pytest.fixture
def empty_session() -> Session:
    """abstractが空のセッション"""
    return Session(
        title="Empty Session",
        timeslot=datetime(
            year=2026, month=1, day=7, hour=9, minute=0, second=0, tzinfo=UTC
        ),
        room="Hall A",
        track="Track 1",
        speakers=[],
        abstract="",
        url="https://example.com/session/2",
    )
