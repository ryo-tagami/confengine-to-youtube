"""ユースケースのDTO (Data Transfer Object)"""

from dataclasses import dataclass, field


@dataclass
class UpdatePreview:
    """更新プレビュー情報"""

    session_key: str
    video_id: str
    current_title: str
    new_description: str


@dataclass
class YouTubeUpdateResult:
    """YouTube更新結果"""

    is_dry_run: bool
    previews: list[UpdatePreview]
    updated_count: int = 0
    no_content_count: int = 0
    no_mapping_count: int = 0
    unused_mappings_count: int = 0
    errors: list[str] = field(default_factory=list)
