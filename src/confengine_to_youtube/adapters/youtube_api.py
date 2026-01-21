"""YouTube API Gateway"""

from __future__ import annotations

from http import HTTPStatus
from typing import TYPE_CHECKING, NoReturn

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from pydantic import BaseModel, ConfigDict

from confengine_to_youtube.usecases.protocols import (
    VideoInfo,
    VideoNotFoundError,
    VideoUpdateRequest,
    YouTubeApiError,
)

if TYPE_CHECKING:
    from googleapiclient._apis.youtube.v3 import YouTubeResource
    from googleapiclient._apis.youtube.v3.schemas import Video, VideoSnippet

    from confengine_to_youtube.adapters.protocols import YouTubeAuthProvider


class YouTubeSnippet(BaseModel):
    """YouTube API snippet レスポンス"""

    model_config = ConfigDict(frozen=True)

    title: str
    description: str
    categoryId: str  # noqa: N815 # APIは文字列で返す


class YouTubeVideoItem(BaseModel):
    """YouTube API video item レスポンス"""

    model_config = ConfigDict(frozen=True)

    id: str
    snippet: YouTubeSnippet


class YouTubeVideosListResponse(BaseModel):
    """YouTube API videos.list レスポンス"""

    model_config = ConfigDict(frozen=True)

    items: list[YouTubeVideoItem]


def _video_info_from_api_response(item: YouTubeVideoItem) -> VideoInfo:
    """Convert API response to VideoInfo."""
    return VideoInfo(
        video_id=item.id,
        title=item.snippet.title,
        description=item.snippet.description,
        category_id=int(item.snippet.categoryId),
    )


def _to_api_body(request: VideoUpdateRequest) -> Video:
    """Convert VideoUpdateRequest to API request body."""
    snippet: VideoSnippet = {
        "title": request.title,
        "description": request.description,
        "categoryId": str(request.category_id),
    }
    return {"id": request.video_id, "snippet": snippet}


class YouTubeApiGateway:
    """YouTube Data API v3との通信"""

    def __init__(
        self,
        auth_provider: YouTubeAuthProvider,
        youtube: YouTubeResource | None,
    ) -> None:
        if youtube is None:
            credentials = auth_provider.get_credentials()
            self._youtube: YouTubeResource = build(
                serviceName="youtube", version="v3", credentials=credentials
            )
        else:
            self._youtube = youtube

    def get_video_info(self, video_id: str) -> VideoInfo:
        # NOTE: HttpError のみキャッチし、ネットワークエラー等はそのまま上位に伝播させる
        # (ユーザーが原因を理解できるため、変換不要)
        try:
            response = (
                self._youtube.videos().list(part="snippet", id=video_id).execute()
            )
        except HttpError as e:
            self._handle_http_error(error=e, video_id=video_id)

        parsed = YouTubeVideosListResponse.model_validate(obj=response)

        if not parsed.items:
            msg = f"Video not found: {video_id}"
            raise VideoNotFoundError(msg)

        return _video_info_from_api_response(item=parsed.items[0])

    def update_video(self, request: VideoUpdateRequest) -> None:
        """動画のsnippetを更新"""
        # NOTE: ネットワークエラー等の扱いは get_video_info 参照
        try:
            self._youtube.videos().update(
                part="snippet",
                body=_to_api_body(request=request),
            ).execute()
        except HttpError as e:
            self._handle_http_error(error=e, video_id=request.video_id)

    def _handle_http_error(self, error: HttpError, video_id: str) -> NoReturn:
        """HttpErrorをドメイン例外に変換して送出"""
        status = error.resp.status

        if status == HTTPStatus.NOT_FOUND:
            msg = f"Video not found: {video_id}"
            raise VideoNotFoundError(msg) from error

        if status == HTTPStatus.UNAUTHORIZED:
            msg = "YouTube API authentication failed. Please re-authenticate."
            raise YouTubeApiError(msg) from error

        if status == HTTPStatus.FORBIDDEN:
            msg = "YouTube API access forbidden. Check quota or permissions."
            raise YouTubeApiError(msg) from error

        if status == HTTPStatus.TOO_MANY_REQUESTS:
            msg = "YouTube API rate limit exceeded. Please try again later."
            raise YouTubeApiError(msg) from error

        msg = f"YouTube API error (HTTP {status}): {error}"
        raise YouTubeApiError(msg) from error
