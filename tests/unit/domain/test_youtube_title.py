"""YouTubeTitle のテスト"""

import pytest
from returns.result import Failure, Success

from confengine_to_youtube.domain.errors import TitleEmptyError, TitleTooLongError
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
        assert len(str(result.unwrap())) == YouTubeTitle.MAX_LENGTH

    def test_empty_title_returns_failure(self) -> None:
        """空のタイトルは Failure(TitleEmptyError)"""
        result = YouTubeTitle.create(value="")

        assert isinstance(result, Failure)
        assert isinstance(result.failure(), TitleEmptyError)

    def test_exceeds_max_length_returns_failure(self) -> None:
        """最大長超過は Failure(TitleTooLongError)"""
        value = "X" * (YouTubeTitle.MAX_LENGTH + 1)
        result = YouTubeTitle.create(value=value)

        assert isinstance(result, Failure)
        error = result.failure()
        assert isinstance(error, TitleTooLongError)
        assert error.length == YouTubeTitle.MAX_LENGTH + 1
        assert error.max_length == YouTubeTitle.MAX_LENGTH

    def test_max_length_is_100(self) -> None:
        """最大長は100文字"""
        assert YouTubeTitle.MAX_LENGTH == 100

    def test_direct_instantiation_raises_typeerror(self) -> None:
        """直接インスタンス化は TypeError"""
        with pytest.raises(
            expected_exception=TypeError,
            match="Use create\\(\\) instead",
        ):
            YouTubeTitle(value="Test")
