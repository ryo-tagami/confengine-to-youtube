"""YouTubeDescription のテスト"""

import pytest
from returns.result import Failure, Success

from confengine_to_youtube.domain.errors import DescriptionTooLongError
from confengine_to_youtube.domain.youtube_description import YouTubeDescription


class TestYouTubeDescription:
    """YouTubeDescription のテスト"""

    def test_create_valid_description(self) -> None:
        """有効な説明文を作成できる"""
        result = YouTubeDescription.create(value="Test Description")

        assert isinstance(result, Success)
        description = result.unwrap()
        assert str(description) == "Test Description"
        assert description.value == "Test Description"

    def test_create_max_length_description(self) -> None:
        """最大長の説明文を作成できる"""
        value = "X" * YouTubeDescription.MAX_LENGTH
        result = YouTubeDescription.create(value=value)

        assert isinstance(result, Success)
        assert len(str(result.unwrap())) == YouTubeDescription.MAX_LENGTH

    def test_create_empty_description(self) -> None:
        """空の説明文を作成できる"""
        result = YouTubeDescription.create(value="")

        assert isinstance(result, Success)
        assert str(result.unwrap()) == ""

    def test_exceeds_max_length_returns_failure(self) -> None:
        """最大長超過は Failure(DescriptionTooLongError)"""
        value = "X" * (YouTubeDescription.MAX_LENGTH + 1)
        result = YouTubeDescription.create(value=value)

        assert isinstance(result, Failure)
        error = result.failure()
        assert isinstance(error, DescriptionTooLongError)
        assert error.length == YouTubeDescription.MAX_LENGTH + 1
        assert error.max_length == YouTubeDescription.MAX_LENGTH

    def test_max_length_is_5000(self) -> None:
        """最大長は5000文字"""
        assert YouTubeDescription.MAX_LENGTH == 5000

    def test_direct_instantiation_raises_typeerror(self) -> None:
        """直接インスタンス化は TypeError"""
        with pytest.raises(
            expected_exception=TypeError,
            match="Use create\\(\\) instead",
        ):
            YouTubeDescription(value="Test")
