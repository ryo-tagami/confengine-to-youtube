"""YouTubeTitle のテスト"""

import pytest

from confengine_to_youtube.domain.youtube_title import YouTubeTitle


class TestYouTubeTitle:
    """YouTubeTitle のテスト"""

    def test_create_valid_title(self) -> None:
        """有効なタイトルを作成できる"""
        title = YouTubeTitle(value="Test Title")

        assert str(title) == "Test Title"
        assert title.value == "Test Title"

    def test_create_max_length_title(self) -> None:
        """最大長のタイトルを作成できる"""
        value = "X" * YouTubeTitle.MAX_LENGTH
        title = YouTubeTitle(value=value)

        assert len(str(title)) == YouTubeTitle.MAX_LENGTH

    def test_empty_title_raises_error(self) -> None:
        """空のタイトルはエラー"""
        with pytest.raises(expected_exception=ValueError, match="タイトルは必須です"):
            YouTubeTitle(value="")

    def test_exceeds_max_length_raises_error(self) -> None:
        """最大長を超えるタイトルはエラー"""
        value = "X" * (YouTubeTitle.MAX_LENGTH + 1)

        with pytest.raises(expected_exception=ValueError, match="100文字以内"):
            YouTubeTitle(value=value)

    def test_max_length_is_100(self) -> None:
        """最大長は100文字"""
        assert YouTubeTitle.MAX_LENGTH == 100
