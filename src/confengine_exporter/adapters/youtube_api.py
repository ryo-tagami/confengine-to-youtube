"""YouTube API Gateway"""

from __future__ import annotations

from http import HTTPStatus
from typing import TYPE_CHECKING, Any, NoReturn, Protocol, Self

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from pydantic import BaseModel, ConfigDict

if TYPE_CHECKING:
    from googleapiclient._apis.youtube.v3 import YouTubeResource


class YouTubeAuthProvider(Protocol):
    def get_credentials(self) -> Any:  # noqa: ANN401
        ...


# =============================================================================
# YouTube API スキーマ (レスポンス)
# =============================================================================


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


# =============================================================================
# YouTube API スキーマ (リクエスト)
# =============================================================================


class YouTubeSnippetUpdate(BaseModel):
    """YouTube API snippet 更新リクエスト"""

    model_config = ConfigDict(frozen=True)

    title: str
    description: str
    categoryId: str  # noqa: N815


class YouTubeVideoUpdateBody(BaseModel):
    """YouTube API videos.update リクエストボディ"""

    model_config = ConfigDict(frozen=True)

    id: str
    snippet: YouTubeSnippetUpdate


# =============================================================================
# Gateway データ型
# =============================================================================


class VideoInfo(BaseModel):
    """ビデオ情報"""

    model_config = ConfigDict(frozen=True)

    video_id: str
    title: str
    description: str
    category_id: int

    @classmethod
    def from_api_response(cls, item: YouTubeVideoItem) -> Self:
        return cls(
            video_id=item.id,
            title=item.snippet.title,
            description=item.snippet.description,
            category_id=int(item.snippet.categoryId),
        )


class VideoUpdateRequest(BaseModel):
    """動画更新リクエスト"""

    model_config = ConfigDict(frozen=True)

    video_id: str
    title: str
    description: str
    category_id: int

    def to_api_body(self) -> dict[str, Any]:
        return YouTubeVideoUpdateBody(
            id=self.video_id,
            snippet=YouTubeSnippetUpdate(
                title=self.title,
                description=self.description,
                categoryId=str(self.category_id),
            ),
        ).model_dump()


# =============================================================================
# Gateway
# =============================================================================


class YouTubeApiGateway:
    """YouTube Data API v3との通信"""

    def __init__(self, auth_provider: YouTubeAuthProvider) -> None:
        self._auth_provider = auth_provider
        self._youtube: YouTubeResource | None = None

    def _get_youtube(self) -> YouTubeResource:
        """YouTube APIクライアントを取得(遅延初期化)"""
        if self._youtube is None:
            credentials = self._auth_provider.get_credentials()
            self._youtube = build(
                serviceName="youtube", version="v3", credentials=credentials
            )
        return self._youtube

    def get_video_info(self, video_id: str) -> VideoInfo:
        youtube = self._get_youtube()
        try:
            response = youtube.videos().list(part="snippet", id=video_id).execute()
        except HttpError as e:
            self._handle_http_error(error=e, video_id=video_id)

        parsed = YouTubeVideosListResponse.model_validate(obj=response)

        if not parsed.items:
            msg = f"Video not found: {video_id}"
            raise VideoNotFoundError(msg)

        return VideoInfo.from_api_response(item=parsed.items[0])

    def update_video(self, request: VideoUpdateRequest) -> None:
        """動画のsnippetを更新"""
        youtube = self._get_youtube()
        try:
            youtube.videos().update(
                part="snippet",
                body=request.to_api_body(),
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


class YouTubeApiError(Exception):
    """YouTube API エラーの基底クラス"""


class VideoNotFoundError(YouTubeApiError):
    pass
