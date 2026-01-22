"""ユースケースのDTO (Data Transfer Object)"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class UpdatePreview:
    """更新プレビュー情報"""

    session_key: str
    video_id: str
    current_title: str
    current_description: str
    new_title: str
    new_description: str


@dataclass(frozen=True)
class YouTubeUpdateResult:
    """YouTube更新結果"""

    is_dry_run: bool
    previews: tuple[UpdatePreview, ...]
    updated_count: int = 0
    no_content_count: int = 0
    no_mapping_count: int = 0
    unused_mappings_count: int = 0
