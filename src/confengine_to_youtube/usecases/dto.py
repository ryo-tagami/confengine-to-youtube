"""ユースケースのDTO (Data Transfer Object)"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from confengine_to_youtube.domain.errors import DomainError
    from confengine_to_youtube.domain.schedule_slot import ScheduleSlot


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

    @property
    def has_title_changes(self) -> bool:
        """タイトルに変更があるかどうか"""
        return self.current_title != self.new_title

    @property
    def has_description_changes(self) -> bool:
        """説明に変更があるかどうか"""
        return self.current_description != self.new_description

    @property
    def has_changes(self) -> bool:
        """タイトルまたは説明に変更があるかどうか"""
        return self.has_title_changes or self.has_description_changes


@dataclass(frozen=True)
class SessionProcessError:
    """セッション処理エラー"""

    session_key: str
    video_id: str
    error: DomainError


@dataclass(frozen=True)
class PlaylistItem:
    """プレイリストアイテム"""

    video_id: str
    playlist_item_id: str
    position: int


class PlaylistOperationType(Enum):
    """プレイリスト操作の種類"""

    ADD = auto()
    REORDER = auto()
    UNCHANGED = auto()
    MOVE_TO_END = auto()


@dataclass(frozen=True)
class PlaylistVideoOperation:
    """プレイリスト操作の情報"""

    video_id: str
    title: str
    operation: PlaylistOperationType
    position: int
    slot: ScheduleSlot | None = None


@dataclass(frozen=True)
class PlaylistSyncResult:
    """プレイリスト同期結果"""

    is_dry_run: bool
    playlist_id: str
    added_count: int
    reordered_count: int
    unchanged_count: int
    moved_to_end_count: int
    operations: tuple[PlaylistVideoOperation, ...]


@dataclass(frozen=True)
class VideoUpdateResult:
    """動画更新結果"""

    is_dry_run: bool
    previews: tuple[VideoUpdatePreview, ...]
    changed_count: int = 0
    unchanged_count: int = 0
    preserved_count: int = 0
    no_mapping_count: int = 0
    unused_mappings_count: int = 0
    errors: tuple[SessionProcessError, ...] = ()
