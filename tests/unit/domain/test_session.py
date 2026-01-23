"""Session エンティティのテスト"""

from datetime import UTC, datetime

import pytest

from confengine_to_youtube.domain.session import Session
from tests.conftest import create_session

TIMESLOT = datetime(year=2026, month=1, day=7, hour=10, tzinfo=UTC)
ROOM = "Hall A"
ABSTRACT = "Some abstract"
URL = "https://example.com"


class TestSession:
    """Session のテスト"""

    def test_empty_title_raises_value_error(self) -> None:
        """タイトルが空の場合は ValueError を発生"""
        with pytest.raises(ValueError, match="Session title must not be empty"):
            create_session(
                title="",
                speakers=[],
                abstract=ABSTRACT,
                timeslot=TIMESLOT,
                room=ROOM,
                url=URL,
            )

    def test_has_content_with_abstract(self, sample_session: Session) -> None:
        """abstractがある場合はhas_contentがTrue"""
        assert sample_session.has_content is True

    def test_has_content_without_abstract(self, empty_session: Session) -> None:
        """abstractがない場合はhas_contentがFalse"""
        assert empty_session.has_content is False

    def test_speakers_full(self) -> None:
        """speakers_full プロパティのテスト"""
        session = create_session(
            title="Test",
            speakers=[("John", "Doe"), ("Jane", "Smith")],
            abstract=ABSTRACT,
            timeslot=TIMESLOT,
            room=ROOM,
            url=URL,
        )
        assert session.speakers_full == "John Doe, Jane Smith"

    def test_speakers_initials(self) -> None:
        """speakers_initials プロパティのテスト"""
        session = create_session(
            title="Test",
            speakers=[("John", "Doe"), ("Jane", "Smith")],
            abstract=ABSTRACT,
            timeslot=TIMESLOT,
            room=ROOM,
            url=URL,
        )
        assert session.speakers_initials == "J. Doe, J. Smith"

    def test_speakers_last_name(self) -> None:
        """speakers_last_name プロパティのテスト"""
        session = create_session(
            title="Test",
            speakers=[("John", "Doe"), ("Jane", "Smith")],
            abstract=ABSTRACT,
            timeslot=TIMESLOT,
            room=ROOM,
            url=URL,
        )
        assert session.speakers_last_name == "Doe, Smith"
