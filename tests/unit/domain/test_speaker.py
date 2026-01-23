"""Speaker 値オブジェクトのテスト"""

import pytest

from confengine_to_youtube.domain.speaker import Speaker


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
        self,
        first_name: str,
        last_name: str,
        expected: str | None,
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
        self,
        first_name: str,
        last_name: str,
        expected: str | None,
    ) -> None:
        """initial_name プロパティのテスト"""
        speaker = Speaker(first_name=first_name, last_name=last_name)
        assert speaker.initial_name == expected
