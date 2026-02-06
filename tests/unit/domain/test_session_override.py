"""SessionOverride 値オブジェクトのテスト"""

from dataclasses import FrozenInstanceError

import pytest

from confengine_to_youtube.domain.session_abstract import SessionAbstract
from confengine_to_youtube.domain.session_override import SessionOverride
from confengine_to_youtube.domain.speaker import Speaker


class TestSessionOverride:
    def test_default_values_are_none(self) -> None:
        """デフォルトではすべてのフィールドがNone"""
        override = SessionOverride()
        assert override.speakers is None
        assert override.abstract is None

    def test_with_speakers_only(self) -> None:
        """speakersのみ指定"""
        speakers = (Speaker(first_name="John", last_name="Doe"),)
        override = SessionOverride(speakers=speakers)
        assert override.speakers == speakers
        assert override.abstract is None

    def test_with_abstract_only(self) -> None:
        """abstractのみ指定"""
        abstract = SessionAbstract(content="Override abstract")
        override = SessionOverride(abstract=abstract)
        assert override.speakers is None
        assert override.abstract == abstract

    def test_with_both_fields(self) -> None:
        """両方指定"""
        speakers = (Speaker(first_name="Jane", last_name="Smith"),)
        abstract = SessionAbstract(content="Override abstract")
        override = SessionOverride(speakers=speakers, abstract=abstract)
        assert override.speakers == speakers
        assert override.abstract == abstract

    def test_frozen(self) -> None:
        """frozenであること"""
        override = SessionOverride()
        with pytest.raises(FrozenInstanceError):
            override.speakers = ()  # type: ignore[misc]
