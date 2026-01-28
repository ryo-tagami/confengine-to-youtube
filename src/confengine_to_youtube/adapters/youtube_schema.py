"""YouTube API レスポンスのPydanticスキーマ定義"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class _YouTubeBaseSchema(BaseModel):
    """YouTube API スキーマの基底クラス"""

    model_config = ConfigDict(
        frozen=True,
        alias_generator=to_camel,
        populate_by_name=True,
    )


class YouTubeSnippet(_YouTubeBaseSchema):
    """YouTube API snippet レスポンス"""

    title: str
    description: str
    # YouTube API returns categoryId as a string; Pydantic coerces it to int
    category_id: int


class YouTubeVideoItem(_YouTubeBaseSchema):
    """YouTube API video item レスポンス"""

    id: str
    snippet: YouTubeSnippet


class YouTubeVideosListResponse(_YouTubeBaseSchema):
    """YouTube API videos.list レスポンス"""

    items: list[YouTubeVideoItem]


class YouTubePlaylistItemContentDetails(_YouTubeBaseSchema):
    """プレイリストアイテムの contentDetails"""

    video_id: str


class YouTubePlaylistItemSnippet(_YouTubeBaseSchema):
    """プレイリストアイテムの snippet"""

    playlist_id: str
    position: int
    resource_id: dict[str, str]


class YouTubePlaylistItem(_YouTubeBaseSchema):
    """YouTube API playlistItems レスポンスのアイテム"""

    id: str
    content_details: YouTubePlaylistItemContentDetails
    snippet: YouTubePlaylistItemSnippet


class YouTubePlaylistItemsListResponse(_YouTubeBaseSchema):
    """YouTube API playlistItems.list レスポンス"""

    items: list[YouTubePlaylistItem]
    next_page_token: str | None = None
