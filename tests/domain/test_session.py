"""Session エンティティのテスト"""

from confengine_to_youtube.domain.session import Session, Speaker


class TestSpeaker:
    """Speaker のテスト"""

    def test_full_name_with_both_names(self) -> None:
        """first_name と last_name が両方ある場合"""
        speaker = Speaker(first_name="John", last_name="Doe")
        assert speaker.full_name == "John Doe"

    def test_full_name_with_first_name_only(self) -> None:
        """first_name のみの場合"""
        speaker = Speaker(first_name="John", last_name="")
        assert speaker.full_name == "John"

    def test_full_name_with_last_name_only(self) -> None:
        """last_name のみの場合"""
        speaker = Speaker(first_name="", last_name="Doe")
        assert speaker.full_name == "Doe"

    def test_full_name_with_empty_names(self) -> None:
        """両方空の場合は None を返す"""
        speaker = Speaker(first_name="", last_name="")
        assert speaker.full_name is None

    def test_initial_name_with_both_names(self) -> None:
        """first_name と last_name が両方ある場合のイニシャル表記"""
        speaker = Speaker(first_name="John", last_name="Doe")
        assert speaker.initial_name == "J. Doe"

    def test_initial_name_with_multi_part_first_name(self) -> None:
        """複数パートの first_name の場合"""
        speaker = Speaker(first_name="Tze Chin", last_name="Tang")
        assert speaker.initial_name == "T. C. Tang"

    def test_initial_name_with_first_name_only(self) -> None:
        """first_name のみの場合"""
        speaker = Speaker(first_name="John", last_name="")
        assert speaker.initial_name == "J."

    def test_initial_name_with_last_name_only(self) -> None:
        """last_name のみの場合"""
        speaker = Speaker(first_name="", last_name="Doe")
        assert speaker.initial_name == "Doe"

    def test_initial_name_with_empty_names(self) -> None:
        """両方空の場合は None を返す"""
        speaker = Speaker(first_name="", last_name="")
        assert speaker.initial_name is None


class TestSession:
    """Session のテスト"""

    def test_has_content_with_abstract(self, sample_session: Session) -> None:
        """abstractがある場合はhas_contentがTrue"""
        assert sample_session.has_content is True

    def test_has_content_without_abstract(self, empty_session: Session) -> None:
        """abstractがない場合はhas_contentがFalse"""
        assert empty_session.has_content is False
