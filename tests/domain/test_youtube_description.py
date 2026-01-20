"""YouTubeDescription のテスト"""

import pytest

from confengine_to_youtube.domain.youtube_description import YouTubeDescription


class TestYouTubeDescription:
    """YouTubeDescription のテスト"""

    def test_create_valid_description(self) -> None:
        """有効な説明文を作成できる"""
        description = YouTubeDescription(value="Test Description")

        assert str(description) == "Test Description"
        assert description.value == "Test Description"

    def test_create_max_length_description(self) -> None:
        """最大長の説明文を作成できる"""
        value = "X" * YouTubeDescription.MAX_LENGTH
        description = YouTubeDescription(value=value)

        assert len(str(description)) == YouTubeDescription.MAX_LENGTH

    def test_create_empty_description(self) -> None:
        """空の説明文を作成できる"""
        description = YouTubeDescription(value="")

        assert str(description) == ""

    def test_exceeds_max_length_raises_error(self) -> None:
        """最大長を超える説明文はエラー"""
        value = "X" * (YouTubeDescription.MAX_LENGTH + 1)

        with pytest.raises(expected_exception=ValueError, match="5000文字以内"):
            YouTubeDescription(value=value)

    def test_max_length_is_5000(self) -> None:
        """最大長は5000文字"""
        assert YouTubeDescription.MAX_LENGTH == 5000
