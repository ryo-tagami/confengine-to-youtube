"""YouTube API Gateway"""

from __future__ import annotations

from typing import TYPE_CHECKING, Self

from googleapiclient.discovery import build

from confengine_to_youtube.adapters.youtube_schema import (
    YouTubePlaylistItemsListResponse,
    YouTubeVideoItem,
    YouTubeVideosListResponse,
)
from confengine_to_youtube.usecases.dto import (
    PlaylistItem,
    VideoInfo,
    VideoUpdateRequest,
)
from confengine_to_youtube.usecases.errors import VideoNotFoundError

if TYPE_CHECKING:
    from googleapiclient._apis.youtube.v3 import YouTubeResource
    from googleapiclient._apis.youtube.v3.schemas import Video, VideoSnippet

    from confengine_to_youtube.adapters.protocols import YouTubeAuthProvider


def _video_info_from_api_response(item: YouTubeVideoItem) -> VideoInfo:
    """Convert API response to VideoInfo."""
    return VideoInfo(
        video_id=item.id,
        title=item.snippet.title,
        description=item.snippet.description,
        category_id=item.snippet.category_id,
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

    def __init__(self, youtube: YouTubeResource) -> None:
        self._youtube = youtube

    @classmethod
    def from_auth_provider(cls, auth_provider: YouTubeAuthProvider) -> Self:
        """認証プロバイダーからインスタンスを生成"""
        credentials = auth_provider.get_credentials()
        youtube: YouTubeResource = build(
            serviceName="youtube",
            version="v3",
            credentials=credentials,
        )
        return cls(youtube=youtube)

    def get_video_info(self, video_id: str) -> VideoInfo:
        response = self._youtube.videos().list(part="snippet", id=video_id).execute()

        parsed = YouTubeVideosListResponse.model_validate(obj=response)

        if not parsed.items:
            msg = f"Video not found: {video_id}"
            raise VideoNotFoundError(msg)

        return _video_info_from_api_response(item=parsed.items[0])

    def update_video(self, request: VideoUpdateRequest) -> None:
        """動画のsnippetを更新"""
        self._youtube.videos().update(
            part="snippet",
            body=_to_api_body(request=request),
        ).execute()

    def list_playlist_items(self, playlist_id: str) -> dict[str, PlaylistItem]:
        """プレイリスト内のアイテムを取得

        Returns:
            video_id -> PlaylistItem のマッピング

        """
        result: dict[str, PlaylistItem] = {}
        page_token: str | None = None

        while True:
            response = (
                self._youtube.playlistItems()
                .list(
                    part="snippet,contentDetails",
                    playlistId=playlist_id,
                    maxResults=50,
                    pageToken=page_token,  # type: ignore[arg-type]
                )
                .execute()
            )

            parsed = YouTubePlaylistItemsListResponse.model_validate(obj=response)

            for item in parsed.items:
                result[item.content_details.video_id] = PlaylistItem(
                    video_id=item.content_details.video_id,
                    playlist_item_id=item.id,
                    position=item.snippet.position,
                )

            if not (page_token := parsed.next_page_token):
                break

        return result

    def add_to_playlist(self, playlist_id: str, video_id: str, position: int) -> None:
        """動画をプレイリストに追加する"""
        self._youtube.playlistItems().insert(
            part="snippet",
            body={
                "snippet": {
                    "playlistId": playlist_id,
                    "position": position,
                    "resourceId": {
                        "kind": "youtube#video",
                        "videoId": video_id,
                    },
                },
            },
        ).execute()

    def update_playlist_item_position(
        self,
        playlist_item_id: str,
        playlist_id: str,
        video_id: str,
        position: int,
    ) -> None:
        """プレイリストアイテムの位置を更新する"""
        self._youtube.playlistItems().update(
            part="snippet",
            body={
                "id": playlist_item_id,
                "snippet": {
                    "playlistId": playlist_id,
                    "position": position,
                    "resourceId": {
                        "kind": "youtube#video",
                        "videoId": video_id,
                    },
                },
            },
        ).execute()
