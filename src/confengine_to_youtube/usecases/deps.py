"""ユースケース層の依存関係型定義"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable
    from datetime import datetime

    from confengine_to_youtube.usecases.protocols import (
        ConfEngineApiProtocol,
        DescriptionBuilderProtocol,
        MappingFileReaderProtocol,
        MappingWriterProtocol,
        TitleBuilderProtocol,
        YouTubeApiProtocol,
    )


@dataclass(frozen=True)
class UpdateYouTubeDeps:
    """UpdateYouTubeDescriptionsの依存関係"""

    confengine_api: ConfEngineApiProtocol
    mapping_reader: MappingFileReaderProtocol
    youtube_api: YouTubeApiProtocol
    description_builder: DescriptionBuilderProtocol
    title_builder: TitleBuilderProtocol


@dataclass(frozen=True)
class GenerateMappingDeps:
    """GenerateMappingの依存関係"""

    confengine_api: ConfEngineApiProtocol
    mapping_writer: MappingWriterProtocol
    clock: Callable[[], datetime]
