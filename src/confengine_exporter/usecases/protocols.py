"""ユースケース層のプロトコル定義

Clean Architecture の依存方向を守るため、usecases 層で Protocol を定義し、
adapters 層でこれらを実装する。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from datetime import datetime
    from pathlib import Path
    from typing import TextIO
    from zoneinfo import ZoneInfo

    from confengine_exporter.domain.session import Session
    from confengine_exporter.domain.video_mapping import MappingConfig


# =============================================================================
# 例外クラス
# =============================================================================


class YouTubeApiError(Exception):
    """YouTube API エラーの基底クラス"""


class VideoNotFoundError(YouTubeApiError):
    """動画が見つからないエラー"""


class MappingFileError(Exception):
    """マッピングファイル読み込みエラー"""


# =============================================================================
# データ型
# =============================================================================


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


# =============================================================================
# Protocols
# =============================================================================


class ConfEngineApiProtocol(Protocol):  # pragma: no cover
    """ConfEngine API との通信プロトコル"""

    def fetch_sessions(self, conf_id: str) -> tuple[list[Session], ZoneInfo]:
        """セッション一覧を取得する"""
        ...


class MappingReaderProtocol(Protocol):  # pragma: no cover
    """マッピングファイル読み込みプロトコル"""

    def read(self, file_path: Path, timezone: ZoneInfo) -> MappingConfig:
        """マッピングファイルを読み込む"""
        ...


class MappingWriterProtocol(Protocol):  # pragma: no cover
    """マッピングファイル書き込みプロトコル"""

    def write(
        self,
        sessions: list[Session],
        output: TextIO,
        conf_id: str,
        generated_at: datetime,
        hashtags: list[str] | None,
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


class DescriptionBuilderProtocol(Protocol):  # pragma: no cover
    """YouTube 説明文ビルダープロトコル"""

    def build(self, session: Session, hashtags: tuple[str, ...]) -> str:
        """説明文を生成する"""
        ...


class TitleBuilderProtocol(Protocol):  # pragma: no cover
    """YouTube タイトルビルダープロトコル"""

    def build(self, session: Session) -> str:
        """タイトルを生成する"""
        ...
