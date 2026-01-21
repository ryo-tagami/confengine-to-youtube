"""YouTube API Gateway"""

from __future__ import annotations

from typing import TYPE_CHECKING

from googleapiclient.discovery import build
from pydantic import BaseModel, ConfigDict
from returns.io import IOResult, impure_safe

from confengine_to_youtube.usecases.protocols import VideoInfo, VideoUpdateRequest

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


class VideoNotFoundError(Exception):
    """動画が見つからない場合のエラー"""

    def __init__(self, video_id: str) -> None:
        super().__init__(f"Video not found: {video_id}")
        self.video_id = video_id


@impure_safe
def _get_video_info(youtube: YouTubeResource, video_id: str) -> VideoInfo:
    response = youtube.videos().list(part="snippet", id=video_id).execute()
    parsed = YouTubeVideosListResponse.model_validate(obj=response)

    if not parsed.items:
        raise VideoNotFoundError(video_id)

    return _video_info_from_api_response(item=parsed.items[0])


@impure_safe
def _update_video(youtube: YouTubeResource, request: VideoUpdateRequest) -> None:
    youtube.videos().update(
        part="snippet",
        body=_to_api_body(request=request),
    ).execute()


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
                serviceName="youtube",
                version="v3",
                credentials=credentials,
            )
        else:
            self._youtube = youtube

    def get_video_info(self, video_id: str) -> IOResult[VideoInfo, Exception]:
        """動画情報を取得する"""
        return _get_video_info(youtube=self._youtube, video_id=video_id)

    def update_video(
        self,
        request: VideoUpdateRequest,
    ) -> IOResult[None, Exception]:
        """動画のsnippetを更新"""
        return _update_video(youtube=self._youtube, request=request)
