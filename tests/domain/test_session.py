"""Session エンティティのテスト"""

import pytest

from confengine_to_youtube.domain.session import Session, Speaker


class TestSpeaker:
    """Speaker のテスト"""

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
        self, first_name: str, last_name: str, expected: str | None
    ) -> None:
        """full_name プロパティのテスト"""
        speaker = Speaker(first_name=first_name, last_name=last_name)
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
        self, first_name: str, last_name: str, expected: str | None
    ) -> None:
        """initial_name プロパティのテスト"""
        speaker = Speaker(first_name=first_name, last_name=last_name)
        assert speaker.initial_name == expected


class TestSession:
    """Session のテスト"""

    def test_has_content_with_abstract(self, sample_session: Session) -> None:
        """abstractがある場合はhas_contentがTrue"""
        assert sample_session.has_content is True

    def test_has_content_without_abstract(self, empty_session: Session) -> None:
        """abstractがない場合はhas_contentがFalse"""
        assert empty_session.has_content is False
