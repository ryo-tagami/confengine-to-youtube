"""Session エンティティのテスト"""

from datetime import UTC, datetime

import pytest
from returns.pipeline import is_successful

from confengine_to_youtube.domain.abstract_markdown import AbstractMarkdown
from confengine_to_youtube.domain.schedule_slot import ScheduleSlot
from confengine_to_youtube.domain.session import Session, Speaker


class TestSpeaker:
    """Speaker のテスト"""

    def test_direct_instantiation_raises_error(self) -> None:
        """直接インスタンス化するとエラーになる"""
        with pytest.raises(TypeError, match="Speaker cannot be instantiated directly"):
            Speaker(first_name="John", last_name="Doe")

    def test_create_success(self) -> None:
        """createメソッドでインスタンスを作成できる"""
        result = Speaker.create(first_name="John", last_name="Doe")
        assert is_successful(result)
        speaker = result.unwrap()
        assert speaker.first_name == "John"
        assert speaker.last_name == "Doe"

    @pytest.mark.parametrize(
        ("first_name", "last_name", "expected"),
        [
            ("John", "Doe", "John Doe"),
            ("John", "", "John"),
            ("", "Doe", "Doe"),
            ("", "", None),
        ],
    )
    def test_full_name(
        self,
        first_name: str,
        last_name: str,
        expected: str | None,
    ) -> None:
        """full_name プロパティのテスト"""
        speaker = Speaker.create(first_name=first_name, last_name=last_name).unwrap()
        assert speaker.full_name == expected

    @pytest.mark.parametrize(
        ("first_name", "last_name", "expected"),
        [
            ("John", "Doe", "J. Doe"),
            ("Tze Chin", "Tang", "T. C. Tang"),
            ("John", "", "J."),
            ("", "Doe", "Doe"),
            ("", "", None),
        ],
    )
    def test_initial_name(
        self,
        first_name: str,
        last_name: str,
        expected: str | None,
    ) -> None:
        """initial_name プロパティのテスト"""
        speaker = Speaker.create(first_name=first_name, last_name=last_name).unwrap()
        assert speaker.initial_name == expected


class TestSession:
    """Session のテスト"""

    def test_direct_instantiation_raises_error(self) -> None:
        """直接インスタンス化するとエラーになる"""
        slot = ScheduleSlot.create(
            timeslot=datetime(year=2026, month=1, day=7, hour=10, minute=0, tzinfo=UTC),
            room="Hall A",
        ).unwrap()
        abstract = AbstractMarkdown.create(content="Test").unwrap()

        with pytest.raises(TypeError, match="Session cannot be instantiated directly"):
            Session(
                slot=slot,
                title="Test",
                track="Track",
                speakers=(),
                abstract=abstract,
                url="https://example.com",
            )

    def test_create_success(self) -> None:
        """createメソッドでインスタンスを作成できる"""
        slot = ScheduleSlot.create(
            timeslot=datetime(year=2026, month=1, day=7, hour=10, minute=0, tzinfo=UTC),
            room="Hall A",
        ).unwrap()
        abstract = AbstractMarkdown.create(content="Test").unwrap()

        result = Session.create(
            slot=slot,
            title="Test",
            track="Track",
            speakers=(),
            abstract=abstract,
            url="https://example.com",
        )
        assert is_successful(result)
        session = result.unwrap()
        assert session.title == "Test"

    def test_has_content_with_abstract(self, sample_session: Session) -> None:
        """abstractがある場合はhas_contentがTrue"""
        assert sample_session.has_content is True

    def test_has_content_without_abstract(self, empty_session: Session) -> None:
        """abstractがない場合はhas_contentがFalse"""
        assert empty_session.has_content is False
