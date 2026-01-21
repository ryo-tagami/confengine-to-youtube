"""YouTubeApiGateway のテスト"""

from typing import Any
from unittest.mock import MagicMock

import pytest
from googleapiclient.errors import HttpError
from httplib2 import Response
from returns.pipeline import is_successful
from returns.unsafe import unsafe_perform_io

from confengine_to_youtube.adapters.youtube_api import (
    VideoNotFoundError,
    YouTubeApiGateway,
)
from confengine_to_youtube.usecases.protocols import VideoUpdateRequest


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

        assert is_successful(result)
        video_info = unsafe_perform_io(result.unwrap())
        assert video_info.video_id == "abc123"
        assert video_info.title == "Test Video"
        assert video_info.description == "Test Description"
        assert video_info.category_id == 28

    def test_get_video_info_not_found(
        self,
        gateway: YouTubeApiGateway,
        mock_youtube: MagicMock,
    ) -> None:
        """動画が見つからない場合はIOFailureを返す"""
        mock_youtube.videos().list().execute.return_value = {"items": []}

        result = gateway.get_video_info(video_id="nonexistent")

        assert not is_successful(result)
        error = unsafe_perform_io(result.failure())
        assert isinstance(error, VideoNotFoundError)
        assert error.video_id == "nonexistent"

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

        result = gateway.update_video(request=request)

        assert is_successful(result)
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

    @pytest.mark.parametrize("status", [404, 401, 403, 429, 500])
    def test_get_video_info_http_error(
        self,
        gateway: YouTubeApiGateway,
        mock_youtube: MagicMock,
        status: int,
    ) -> None:
        """HTTPエラーがIOFailureで返される"""
        http_error = HttpError(
            resp=Response(info={"status": str(status)}),
            content=b"error",
        )
        mock_youtube.videos().list().execute.side_effect = http_error

        result = gateway.get_video_info(video_id="abc123")

        assert not is_successful(result)
        error = unsafe_perform_io(result.failure())
        assert isinstance(error, HttpError)

    @pytest.mark.parametrize(
        "status",
        [404, 401, 403, 429, 500],
    )
    def test_update_video_http_error(
        self,
        gateway: YouTubeApiGateway,
        mock_youtube: MagicMock,
        status: int,
    ) -> None:
        """update_videoでHTTPエラーがIOFailureで返される"""
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

        result = gateway.update_video(request=request)

        assert not is_successful(result)
        error = unsafe_perform_io(result.failure())
        assert isinstance(error, Exception)

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
