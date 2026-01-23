"""ユースケースのDTO (Data Transfer Object)"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from confengine_to_youtube.domain.errors import DomainError


@dataclass(frozen=True)
class VideoInfo:
    """ビデオ情報"""

    video_id: str
    title: str
    description: str
    category_id: int


@dataclass(frozen=True)
class VideoUpdateRequest:
    """動画更新リクエスト"""

    video_id: str
    title: str
    description: str
    category_id: int


@dataclass(frozen=True)
class VideoUpdatePreview:
    """更新プレビュー情報"""

    session_key: str
    video_id: str
    current_title: str
    current_description: str
    new_title: str
    new_description: str


@dataclass(frozen=True)
class SessionProcessError:
    """セッション処理エラー"""

    session_key: str
    video_id: str
    error: DomainError


@dataclass(frozen=True)
class VideoUpdateResult:
    """動画更新結果"""

    is_dry_run: bool
    previews: tuple[VideoUpdatePreview, ...]
    updated_count: int = 0
    no_content_count: int = 0
    no_mapping_count: int = 0
    unused_mappings_count: int = 0
    errors: tuple[SessionProcessError, ...] = ()
