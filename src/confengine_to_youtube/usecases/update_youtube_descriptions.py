"""YouTube description更新ユースケース"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from confengine_to_youtube.usecases.dto import UpdatePreview, YouTubeUpdateResult
from confengine_to_youtube.usecases.protocols import VideoUpdateRequest

logger = logging.getLogger(name=__name__)

if TYPE_CHECKING:
    from collections.abc import Sequence
    from pathlib import Path

    from confengine_to_youtube.domain.schedule_slot import ScheduleSlot
    from confengine_to_youtube.domain.session import Session
    from confengine_to_youtube.domain.video_mapping import MappingConfig
    from confengine_to_youtube.usecases.protocols import (
        ConfEngineApiProtocol,
        MappingFileReaderProtocol,
        YouTubeApiProtocol,
    )


class UpdateYouTubeDescriptionsUseCase:
    def __init__(
        self,
        confengine_api: ConfEngineApiProtocol,
        mapping_reader: MappingFileReaderProtocol,
        youtube_api: YouTubeApiProtocol,
    ) -> None:
        self._confengine_api = confengine_api
        self._mapping_reader = mapping_reader
        self._youtube_api = youtube_api

    def execute(
        self,
        mapping_file: Path,
        *,
        dry_run: bool = False,
    ) -> YouTubeUpdateResult:
        mapping = self._mapping_reader.read(file_path=mapping_file)
        sessions, timezone = self._confengine_api.fetch_sessions(
            conf_id=mapping.conf_id,
        )
        mapping_config = mapping.to_domain(timezone=timezone)

        return self._execute(
            sessions=sessions,
            mapping_config=mapping_config,
            dry_run=dry_run,
        )

    def _execute(
        self,
        sessions: Sequence[Session],
        mapping_config: MappingConfig,
        *,
        dry_run: bool,
    ) -> YouTubeUpdateResult:
        previews: list[UpdatePreview] = []
        updated_count = 0
        no_content_count = 0
        no_mapping_count = 0
        used_slots: set[ScheduleSlot] = set()

        for session in sessions:
            if not session.has_content:
                no_content_count += 1
                continue

            mapping = mapping_config.find_mapping(slot=session.slot)

            if mapping is None:
                no_mapping_count += 1
                continue

            used_slots.add(session.slot)

            video_info = self._youtube_api.get_video_info(video_id=mapping.video_id)
            new_title = session.youtube_title
            description = session.to_youtube_description(
                hashtags=mapping_config.hashtags,
                footer=mapping_config.footer,
            )

            previews.append(
                UpdatePreview(
                    session_key=str(session.slot),
                    video_id=mapping.video_id,
                    current_title=video_info.title,
                    current_description=video_info.description,
                    new_title=str(new_title),
                    new_description=str(description),
                ),
            )

            if not dry_run:
                request = VideoUpdateRequest(
                    video_id=mapping.video_id,
                    title=str(new_title),
                    description=str(description),
                    category_id=video_info.category_id,
                )
                self._youtube_api.update_video(request=request)
                updated_count += 1
                logger.info("Updated: %s (%s)", session.title, mapping.video_id)

        unused_count = self._warn_unused_mappings(
            mapping_config=mapping_config,
            used_slots=used_slots,
        )

        return YouTubeUpdateResult(
            is_dry_run=dry_run,
            previews=tuple(previews),
            updated_count=updated_count,
            no_content_count=no_content_count,
            no_mapping_count=no_mapping_count,
            unused_mappings_count=unused_count,
        )

    def _warn_unused_mappings(
        self,
        mapping_config: MappingConfig,
        used_slots: set[ScheduleSlot],
    ) -> int:
        """未使用のマッピングを警告し、件数を返す"""
        unused = mapping_config.find_unused(used_slots=used_slots)

        for mapping in unused:
            logger.warning(
                "Unused mapping %s (%s)",
                mapping.slot,
                mapping.video_id,
            )

        return len(unused)
