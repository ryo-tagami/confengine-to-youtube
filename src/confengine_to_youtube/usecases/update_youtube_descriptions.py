"""YouTube description更新ユースケース"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from confengine_to_youtube.usecases.dto import UpdatePreview, YouTubeUpdateResult
from confengine_to_youtube.usecases.protocols import (
    VideoUpdateRequest,
    YouTubeApiError,
)

logger = logging.getLogger(name=__name__)

if TYPE_CHECKING:
    from pathlib import Path

    from confengine_to_youtube.domain.schedule_slot import ScheduleSlot
    from confengine_to_youtube.domain.session import Session
    from confengine_to_youtube.domain.video_mapping import MappingConfig
    from confengine_to_youtube.usecases.protocols import (
        ConfEngineApiProtocol,
        DescriptionBuilderProtocol,
        MappingReaderProtocol,
        TitleBuilderProtocol,
        YouTubeApiProtocol,
    )


class UpdateYouTubeDescriptionsUseCase:
    def __init__(
        self,
        confengine_api: ConfEngineApiProtocol,
        mapping_reader: MappingReaderProtocol,
        youtube_api: YouTubeApiProtocol,
        description_builder: DescriptionBuilderProtocol,
        title_builder: TitleBuilderProtocol,
    ) -> None:
        self._confengine_api = confengine_api
        self._mapping_reader = mapping_reader
        self._youtube_api = youtube_api
        self._description_builder = description_builder
        self._title_builder = title_builder

    def execute(
        self,
        mapping_file: Path,
        *,
        dry_run: bool = False,
    ) -> YouTubeUpdateResult:
        schema = self._mapping_reader.read_schema(file_path=mapping_file)
        sessions, timezone = self._confengine_api.fetch_sessions(conf_id=schema.conf_id)
        mapping_config = schema.to_domain(timezone=timezone)

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

            session_key = str(session.slot)

            try:
                video_info = self._youtube_api.get_video_info(video_id=mapping.video_id)
                new_title = self._title_builder.build(session=session)
                description = self._description_builder.build(
                    session=session,
                    hashtags=mapping_config.hashtags,
                    footer=mapping_config.footer,
                )

                previews.append(
                    UpdatePreview(
                        session_key=session_key,
                        video_id=mapping.video_id,
                        current_title=video_info.title,
                        current_description=video_info.description,
                        new_title=str(new_title),
                        new_description=str(description),
                    )
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

            # NOTE: ValueError (タイトル/説明文の文字数超過) は意図的にキャッチしない。
            # データ不整合を示すため、処理を中断して早期に修正を促す。
            except YouTubeApiError as e:
                error_msg = str(e)
                errors.append(error_msg)
                logger.exception("YouTube API error")
                previews.append(
                    UpdatePreview(
                        session_key=session_key,
                        video_id=mapping.video_id,
                        current_title=None,
                        current_description=None,
                        new_title=None,
                        new_description=None,
                        error=error_msg,
                    )
                )

        unused_count = self._warn_unused_mappings(
            mapping_config=mapping_config, used_slots=used_slots
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
