"""ユースケース層のプロトコル定義

Clean Architecture の依存方向を守るため、usecases 層で Protocol を定義し、
adapters 層でこれらを実装する。
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from datetime import datetime
    from pathlib import Path
    from typing import TextIO
    from zoneinfo import ZoneInfo

    from confengine_to_youtube.domain.conference_schedule import ConferenceSchedule
    from confengine_to_youtube.domain.session_abstract import SessionAbstract
    from confengine_to_youtube.domain.video_mapping import MappingConfig
    from confengine_to_youtube.usecases.dto import (
        PlaylistItem,
        VideoInfo,
        VideoUpdateRequest,
    )


class ConfEngineApiProtocol(Protocol):  # pragma: no cover
    """ConfEngine API との通信プロトコル"""

    def fetch_schedule(self, conf_id: str) -> ConferenceSchedule:
        """カンファレンススケジュールを取得する"""
        ...


class MappingFile(Protocol):  # pragma: no cover
    """読み込み済みマッピングファイル"""

    conf_id: str

    def to_domain(self, timezone: ZoneInfo) -> MappingConfig:
        """ドメインオブジェクトに変換する"""
        ...


class MappingFileReaderProtocol(Protocol):  # pragma: no cover
    """マッピングファイル読み込みプロトコル"""

    def read(self, file_path: Path) -> MappingFile:
        """マッピングファイルを読み込む"""
        ...


class MappingWriterProtocol(Protocol):  # pragma: no cover
    """マッピングファイル書き込みプロトコル"""

    def write(
        self,
        schedule: ConferenceSchedule,
        output: TextIO,
        generated_at: datetime,
    ) -> None:
        """マッピングファイルを書き込む"""
        ...


class YouTubeApiProtocol(Protocol):  # pragma: no cover
    """YouTube API との通信プロトコル"""

    def get_video_info(self, video_id: str) -> VideoInfo:
        """動画情報を取得する"""
        ...

    def update_video(self, request: VideoUpdateRequest) -> None:
        """動画を更新する"""
        ...

    def list_playlist_items(self, playlist_id: str) -> dict[str, PlaylistItem]:
        """プレイリスト内のアイテムを取得する

        Returns:
            video_id -> PlaylistItem のマッピング

        """
        ...

    def add_to_playlist(self, playlist_id: str, video_id: str, position: int) -> None:
        """動画をプレイリストに追加する"""
        ...

    def update_playlist_item_position(
        self,
        playlist_item_id: str,
        playlist_id: str,
        video_id: str,
        position: int,
    ) -> None:
        """プレイリストアイテムの位置を更新する"""
        ...


class MarkdownConverterProtocol(Protocol):  # pragma: no cover
    """HTML から Markdown への変換プロトコル"""

    def convert(self, html: str) -> SessionAbstract:
        """HTML を Markdown に変換する"""
        ...
