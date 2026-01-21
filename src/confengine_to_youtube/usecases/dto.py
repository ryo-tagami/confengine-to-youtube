"""ユースケースのDTO (Data Transfer Object)"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from returns.io import IOResult


@dataclass(frozen=True)
class SessionProcessingError(Exception):
    """セッション処理エラー"""

    session_key: str
    video_id: str
    message: str


@dataclass(frozen=True)
class UpdatePreview:
    """更新プレビュー情報"""

    session_key: str
    video_id: str
    current_title: str | None  # エラー時はNone
    current_description: str | None  # エラー時はNone
    new_title: str | None  # エラー時はNone
    new_description: str | None  # エラー時はNone
    error: str | None = None  # エラーメッセージ


@dataclass(frozen=True)
class SessionProcessingBatch:
    """セッション処理バッチ (未集約)

    ユースケースから返される中間結果。
    CLI層で集約して YouTubeUpdateResult に変換する。
    """

    results: tuple[IOResult[UpdatePreview, SessionProcessingError], ...]
    no_content_count: int
    no_mapping_count: int
    unused_mappings_count: int
    is_dry_run: bool


@dataclass(frozen=True)
class YouTubeUpdateResult:
    """YouTube更新結果 (集約済み)"""

    is_dry_run: bool
    previews: tuple[UpdatePreview, ...]
    updated_count: int = 0
    no_content_count: int = 0
    no_mapping_count: int = 0
    unused_mappings_count: int = 0
    errors: tuple[str, ...] = ()
