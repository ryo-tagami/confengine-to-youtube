"""YouTubeApiGateway のテスト"""

from typing import Any
from unittest.mock import MagicMock

import pytest

from confengine_to_youtube.adapters.youtube_api import YouTubeApiGateway
from confengine_to_youtube.usecases.protocols import (
    VideoNotFoundError,
    VideoUpdateRequest,
)


class MockAuthProvider:
    """テスト用の認証プロバイダー"""

    def get_credentials(self) -> Any:  # noqa: ANN401
        """モックcredentialsを返す"""
        return MagicMock()


class TestYouTubeApiGateway:
    """YouTubeApiGateway のテスト"""

    @pytest.fixture
    def mock_youtube(self) -> MagicMock:
        """モックYouTubeクライアント"""
        return MagicMock()

    @pytest.fixture
    def gateway(self, mock_youtube: MagicMock) -> YouTubeApiGateway:
        """テスト用のgateway"""
        return YouTubeApiGateway(
            auth_provider=MockAuthProvider(),
            youtube=mock_youtube,
        )

    def test_get_video_info_success(
        self,
        gateway: YouTubeApiGateway,
        mock_youtube: MagicMock,
    ) -> None:
        """動画情報を取得できる"""
        mock_youtube.videos().list().execute.return_value = {
            "items": [
                {
                    "id": "abc123",
                    "snippet": {
                        "title": "Test Video",
                        "description": "Test Description",
                        "categoryId": "28",
                    },
                },
            ],
        }

        result = gateway.get_video_info(video_id="abc123")

        assert result.video_id == "abc123"
        assert result.title == "Test Video"
        assert result.description == "Test Description"
        assert result.category_id == 28

    def test_get_video_info_not_found(
        self,
        gateway: YouTubeApiGateway,
        mock_youtube: MagicMock,
    ) -> None:
        """動画が見つからない場合は例外"""
        mock_youtube.videos().list().execute.return_value = {"items": []}

        with pytest.raises(expected_exception=VideoNotFoundError):
            gateway.get_video_info(video_id="nonexistent")

    def test_update_video(
        self,
        gateway: YouTubeApiGateway,
        mock_youtube: MagicMock,
    ) -> None:
        """動画を更新できる"""
        request = VideoUpdateRequest(
            video_id="abc123",
            title="Updated Title",
            description="Updated Description",
            category_id=28,
        )

        gateway.update_video(request=request)

        mock_youtube.videos().update.assert_called_once_with(
            part="snippet",
            body={
                "id": "abc123",
                "snippet": {
                    "title": "Updated Title",
                    "description": "Updated Description",
                    "categoryId": "28",
                },
            },
        )
