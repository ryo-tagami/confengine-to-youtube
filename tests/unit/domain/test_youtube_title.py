"""YouTubeTitle のテスト"""

from returns.result import Failure, Success

from confengine_to_youtube.domain.youtube_title import YouTubeTitle


class TestYouTubeTitle:
    """YouTubeTitle のテスト"""

    def test_create_valid_title(self) -> None:
        """有効なタイトルを作成できる"""
        result = YouTubeTitle.create(value="Test Title")

        assert isinstance(result, Success)
        title = result.unwrap()
        assert str(title) == "Test Title"
        assert title.value == "Test Title"

    def test_create_max_length_title(self) -> None:
        """最大長のタイトルを作成できる"""
        value = "X" * YouTubeTitle.MAX_LENGTH
        result = YouTubeTitle.create(value=value)

        assert isinstance(result, Success)
        title = result.unwrap()
        assert len(str(title)) == YouTubeTitle.MAX_LENGTH

    def test_empty_title_returns_failure(self) -> None:
        """空のタイトルはFailureを返す"""
        result = YouTubeTitle.create(value="")

        assert isinstance(result, Failure)
        assert result.failure().message == "タイトルは必須です"

    def test_exceeds_max_length_returns_failure(self) -> None:
        """最大長を超えるタイトルはFailureを返す"""
        value = "X" * (YouTubeTitle.MAX_LENGTH + 1)
        result = YouTubeTitle.create(value=value)

        assert isinstance(result, Failure)
        assert result.failure().message == "タイトルは100文字以内 (現在: 101文字)"

    def test_max_length_is_100(self) -> None:
        """最大長は100文字"""
        assert YouTubeTitle.MAX_LENGTH == 100
