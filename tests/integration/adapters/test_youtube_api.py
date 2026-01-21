"""YouTubeApiGateway のテスト"""

from typing import Any
from unittest.mock import MagicMock

import pytest
from googleapiclient.errors import HttpError
from httplib2 import Response

from confengine_to_youtube.adapters.youtube_api import YouTubeApiGateway
from confengine_to_youtube.usecases.protocols import (
    VideoNotFoundError,
    VideoUpdateRequest,
    YouTubeApiError,
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
        self, gateway: YouTubeApiGateway, mock_youtube: MagicMock
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
                }
            ]
        }

        result = gateway.get_video_info(video_id="abc123")

        assert result.video_id == "abc123"
        assert result.title == "Test Video"
        assert result.description == "Test Description"
        assert result.category_id == 28

    def test_get_video_info_not_found(
        self, gateway: YouTubeApiGateway, mock_youtube: MagicMock
    ) -> None:
        """動画が見つからない場合は例外"""
        mock_youtube.videos().list().execute.return_value = {"items": []}

        with pytest.raises(expected_exception=VideoNotFoundError):
            gateway.get_video_info(video_id="nonexistent")

    def test_update_video(
        self, gateway: YouTubeApiGateway, mock_youtube: MagicMock
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

    @pytest.mark.parametrize(
        ("status", "expected_exception", "expected_message"),
        [
            (404, VideoNotFoundError, "Video not found"),
            (401, YouTubeApiError, "authentication failed"),
            (403, YouTubeApiError, "access forbidden"),
            (429, YouTubeApiError, "rate limit"),
            (500, YouTubeApiError, "HTTP 500"),
        ],
    )
    def test_get_video_info_http_error(
        self,
        gateway: YouTubeApiGateway,
        mock_youtube: MagicMock,
        status: int,
        expected_exception: type[Exception],
        expected_message: str,
    ) -> None:
        """HTTPエラーが適切なドメイン例外に変換される"""
        http_error = HttpError(
            resp=Response(info={"status": str(status)}),
            content=b"error",
        )
        mock_youtube.videos().list().execute.side_effect = http_error

        with pytest.raises(
            expected_exception=expected_exception, match=expected_message
        ):
            gateway.get_video_info(video_id="abc123")

    @pytest.mark.parametrize(
        ("status", "expected_exception"),
        [
            (404, VideoNotFoundError),
            (401, YouTubeApiError),
            (403, YouTubeApiError),
            (429, YouTubeApiError),
            (500, YouTubeApiError),
        ],
    )
    def test_update_video_http_error(
        self,
        gateway: YouTubeApiGateway,
        mock_youtube: MagicMock,
        status: int,
        expected_exception: type[Exception],
    ) -> None:
        """update_videoでHTTPエラーが適切に処理される"""
        http_error = HttpError(
            resp=Response(info={"status": str(status)}),
            content=b"error",
        )
        mock_youtube.videos().update().execute.side_effect = http_error

        request = VideoUpdateRequest(
            video_id="abc123",
            title="Title",
            description="Desc",
            category_id=28,
        )

        with pytest.raises(expected_exception=expected_exception):
            gateway.update_video(request=request)

        # セットアップ時にも update() が呼ばれるため assert_called_with を使用
        mock_youtube.videos().update.assert_called_with(
            part="snippet",
            body={
                "id": "abc123",
                "snippet": {
                    "title": "Title",
                    "description": "Desc",
                    "categoryId": "28",
                },
            },
        )
