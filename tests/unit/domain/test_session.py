"""Session エンティティのテスト"""

from datetime import UTC, datetime

import pytest

from confengine_to_youtube.domain.session import Session
from confengine_to_youtube.domain.session_abstract import SessionAbstract
from confengine_to_youtube.domain.session_override import SessionOverride
from confengine_to_youtube.domain.speaker import Speaker
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


class TestApplyOverride:
    """Session.apply_override() のテスト"""

    def test_override_speakers_only(self) -> None:
        """speakersのみオーバーライド"""
        session = create_session(
            title="Test",
            speakers=[("John", "Doe")],
            abstract=ABSTRACT,
            timeslot=TIMESLOT,
            room=ROOM,
            url=URL,
        )
        override = SessionOverride(
            speakers=(Speaker(first_name="Jane", last_name="Smith"),),
        )
        result = session.apply_override(override=override)

        assert result.speakers == (Speaker(first_name="Jane", last_name="Smith"),)
        assert result.abstract == session.abstract
        assert result.title == session.title
        assert result.track == session.track
        assert result.slot == session.slot
        assert result.url == session.url

    def test_override_abstract_only(self) -> None:
        """abstractのみオーバーライド"""
        session = create_session(
            title="Test",
            speakers=[("John", "Doe")],
            abstract=ABSTRACT,
            timeslot=TIMESLOT,
            room=ROOM,
            url=URL,
        )
        override = SessionOverride(
            abstract=SessionAbstract(content="New abstract"),
        )
        result = session.apply_override(override=override)

        assert result.speakers == session.speakers
        assert result.abstract == SessionAbstract(content="New abstract")

    def test_override_both(self) -> None:
        """Speakers と abstract 両方オーバーライド"""
        session = create_session(
            title="Test",
            speakers=[("John", "Doe")],
            abstract=ABSTRACT,
            timeslot=TIMESLOT,
            room=ROOM,
            url=URL,
        )
        new_speakers = (Speaker(first_name="Jane", last_name="Smith"),)
        new_abstract = SessionAbstract(content="New abstract")
        override = SessionOverride(speakers=new_speakers, abstract=new_abstract)
        result = session.apply_override(override=override)

        assert result.speakers == new_speakers
        assert result.abstract == new_abstract

    def test_override_none_fields_no_change(self) -> None:
        """Noneフィールドは変更しない"""
        session = create_session(
            title="Test",
            speakers=[("John", "Doe")],
            abstract=ABSTRACT,
            timeslot=TIMESLOT,
            room=ROOM,
            url=URL,
        )
        override = SessionOverride()
        result = session.apply_override(override=override)

        assert result.speakers == session.speakers
        assert result.abstract == session.abstract

    def test_override_empty_abstract_to_content(self) -> None:
        """空abstractをコンテンツありに変更するとhas_contentがTrueになる"""
        session = create_session(
            title="Test",
            speakers=[],
            abstract="",
            timeslot=TIMESLOT,
            room=ROOM,
            url=URL,
        )
        assert session.has_content is False

        override = SessionOverride(
            abstract=SessionAbstract(content="Now has content"),
        )
        result = session.apply_override(override=override)

        assert result.has_content is True
