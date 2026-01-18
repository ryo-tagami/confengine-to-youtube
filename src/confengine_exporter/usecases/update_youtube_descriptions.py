"""YouTube description更新ユースケース"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from confengine_exporter.adapters.youtube_api import (
    VideoUpdateRequest,
    YouTubeApiError,
)
from confengine_exporter.usecases.dto import UpdatePreview, YouTubeUpdateResult

logger = logging.getLogger(name=__name__)

if TYPE_CHECKING:
    from datetime import datetime
    from pathlib import Path

    from confengine_exporter.adapters.confengine_api import ConfEngineApiGateway
    from confengine_exporter.adapters.mapping_file_reader import MappingFileReader
    from confengine_exporter.adapters.youtube_api import YouTubeApiGateway
    from confengine_exporter.adapters.youtube_description_builder import (
        YouTubeDescriptionBuilder,
    )
    from confengine_exporter.domain.session import Session
    from confengine_exporter.domain.video_mapping import MappingConfig


class UpdateYouTubeDescriptionsUseCase:
    def __init__(
        self,
        confengine_api: ConfEngineApiGateway,
        mapping_reader: MappingFileReader,
        youtube_api: YouTubeApiGateway,
        description_builder: YouTubeDescriptionBuilder,
    ) -> None:
        self._confengine_api = confengine_api
        self._mapping_reader = mapping_reader
        self._youtube_api = youtube_api
        self._description_builder = description_builder

    def execute(
        self,
        conf_id: str,
        mapping_file: Path,
        *,
        dry_run: bool = False,
    ) -> YouTubeUpdateResult:
        sessions, timezone = self._confengine_api.fetch_sessions(conf_id=conf_id)
        mapping_config = self._mapping_reader.read(
            file_path=mapping_file, timezone=timezone
        )

        return self._execute(
            sessions=sessions, mapping_config=mapping_config, dry_run=dry_run
        )

    def _execute(
        self,
        sessions: list[Session],
        mapping_config: MappingConfig,
        *,
        dry_run: bool,
    ) -> YouTubeUpdateResult:
        previews: list[UpdatePreview] = []
        updated_count = 0
        no_content_count = 0
        no_mapping_count = 0
        errors: list[str] = []
        used_mappings: set[tuple[datetime, str]] = set()

        for session in sessions:
            if not session.has_content:
                no_content_count += 1
                continue

            mapping = mapping_config.find_mapping(
                timeslot=session.timeslot, room=session.room
            )

            if mapping is None:
                no_mapping_count += 1
                continue

            used_mappings.add((session.timeslot, session.room))

            session_key = f"{session.timeslot.isoformat()}_{session.room}"

            try:
                video_info = self._youtube_api.get_video_info(video_id=mapping.video_id)
                description = self._description_builder.build(session=session)

                previews.append(
                    UpdatePreview(
                        session_key=session_key,
                        video_id=mapping.video_id,
                        current_title=video_info.title,
                        new_description=description,
                    )
                )

                if not dry_run:
                    request = VideoUpdateRequest(
                        video_id=mapping.video_id,
                        title=video_info.title,
                        description=description,
                        category_id=video_info.category_id,
                    )
                    self._youtube_api.update_video(request=request)
                    updated_count += 1
                    logger.info("Updated: %s (%s)", session.title, mapping.video_id)

            except YouTubeApiError as e:
                error_msg = str(e)
                errors.append(error_msg)
                logger.exception("YouTube API error")
                previews.append(
                    UpdatePreview(
                        session_key=session_key,
                        video_id=mapping.video_id,
                        current_title=None,
                        new_description=None,
                        error=error_msg,
                    )
                )

        unused_count = self._warn_unused_mappings(
            mapping_config=mapping_config, used_mappings=used_mappings
        )

        return YouTubeUpdateResult(
            is_dry_run=dry_run,
            previews=previews,
            updated_count=updated_count,
            no_content_count=no_content_count,
            no_mapping_count=no_mapping_count,
            unused_mappings_count=unused_count,
            errors=errors,
        )

    def _warn_unused_mappings(
        self,
        mapping_config: MappingConfig,
        used_mappings: set[tuple[datetime, str]],
    ) -> int:
        """未使用のマッピングを警告し、件数を返す"""
        unused = mapping_config.find_unused(used_keys=used_mappings)

        for mapping in unused:
            logger.warning(
                "Unused mapping %s %s (%s)",
                mapping.timeslot,
                mapping.room,
                mapping.video_id,
            )

        return len(unused)
