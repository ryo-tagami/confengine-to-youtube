"""YouTubeDescription のテスト"""

import pytest
from returns.result import Failure, Success

from confengine_to_youtube.domain.youtube_description import YouTubeDescription


class TestYouTubeDescription:
    """YouTubeDescription のテスト"""

    def test_direct_instantiation_raises_error(self) -> None:
        """直接インスタンス化するとエラーになる"""
        with pytest.raises(
            TypeError,
            match="YouTubeDescription cannot be instantiated",
        ):
            YouTubeDescription(value="Test")

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
        description = result.unwrap()
        assert len(str(description)) == YouTubeDescription.MAX_LENGTH

    def test_create_empty_description(self) -> None:
        """空の説明文を作成できる"""
        result = YouTubeDescription.create(value="")

        assert isinstance(result, Success)
        description = result.unwrap()
        assert str(description) == ""

    def test_exceeds_max_length_returns_failure(self) -> None:
        """最大長を超える説明文はFailureを返す"""
        value = "X" * (YouTubeDescription.MAX_LENGTH + 1)
        result = YouTubeDescription.create(value=value)

        assert isinstance(result, Failure)
        assert result.failure().message == "説明文は5000文字以内 (現在: 5001文字)"

    def test_max_length_is_5000(self) -> None:
        """最大長は5000文字"""
        assert YouTubeDescription.MAX_LENGTH == 5000
