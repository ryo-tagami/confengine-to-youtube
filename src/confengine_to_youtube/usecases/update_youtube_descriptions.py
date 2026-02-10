"""YouTube description更新ユースケース"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from returns.result import Failure, Success

from confengine_to_youtube.domain.youtube_content_generator import (
    YouTubeContentGenerator,
)
from confengine_to_youtube.usecases.dto import (
    SessionProcessError,
    VideoUpdatePreview,
    VideoUpdateRequest,
    VideoUpdateResult,
)

logger = logging.getLogger(name=__name__)

if TYPE_CHECKING:
    from pathlib import Path

    from confengine_to_youtube.domain.conference_schedule import ConferenceSchedule
    from confengine_to_youtube.domain.schedule_slot import ScheduleSlot
    from confengine_to_youtube.domain.session import Session
    from confengine_to_youtube.domain.video_mapping import MappingConfig, VideoMapping
    from confengine_to_youtube.usecases.dto import VideoInfo
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
    ) -> VideoUpdateResult:
        mapping = self._mapping_reader.read(file_path=mapping_file)
        schedule = self._confengine_api.fetch_schedule(conf_id=mapping.conf_id)
        mapping_config = mapping.to_domain(timezone=schedule.timezone)

        return self._execute(
            schedule=schedule,
            mapping_config=mapping_config,
            dry_run=dry_run,
        )

    def _execute(
        self,
        schedule: ConferenceSchedule,
        mapping_config: MappingConfig,
        *,
        dry_run: bool,
    ) -> VideoUpdateResult:
        previews: list[VideoUpdatePreview] = []
        errors: list[SessionProcessError] = []
        changed_count = 0
        unchanged_count = 0
        preserved_count = 0
        no_mapping_count = 0
        used_slots: set[ScheduleSlot] = set()

        for session in schedule.sessions:
            mapping = mapping_config.find_mapping(slot=session.slot)

            if mapping is None:
                no_mapping_count += 1
                continue

            used_slots.add(session.slot)

            # 両方falseならスキップ (YouTube APIも呼ばない)
            if not mapping.update_title and not mapping.update_description:
                preserved_count += 1
                continue

            video_info = self._youtube_api.get_video_info(
                video_id=mapping.video_id,
            )

            new_title = self._resolve_title(
                session=session,
                mapping=mapping,
                video_info=video_info,
                errors=errors,
            )
            if new_title is None:
                continue

            new_description = self._resolve_description(
                session=session,
                mapping=mapping,
                mapping_config=mapping_config,
                video_info=video_info,
                errors=errors,
            )
            if new_description is None:
                continue

            preview = VideoUpdatePreview(
                session_key=str(session.slot),
                video_id=mapping.video_id,
                current_title=video_info.title,
                current_description=video_info.description,
                new_title=new_title,
                new_description=new_description,
            )
            previews.append(preview)

            if preview.has_changes:
                if not dry_run:
                    request = VideoUpdateRequest(
                        video_id=mapping.video_id,
                        title=new_title,
                        description=new_description,
                        category_id=video_info.category_id,
                    )
                    self._youtube_api.update_video(request=request)
                    logger.info(
                        "Updated: %s (%s)",
                        session.title,
                        mapping.video_id,
                    )
                changed_count += 1
            else:
                unchanged_count += 1
                if not dry_run:
                    logger.info(
                        "Skipped (unchanged): %s (%s)",
                        session.title,
                        mapping.video_id,
                    )

        unused_count = self._warn_unused_mappings(
            mapping_config=mapping_config,
            used_slots=used_slots,
        )

        return VideoUpdateResult(
            is_dry_run=dry_run,
            previews=tuple(previews),
            changed_count=changed_count,
            unchanged_count=unchanged_count,
            preserved_count=preserved_count,
            no_mapping_count=no_mapping_count,
            unused_mappings_count=unused_count,
            errors=tuple(errors),
        )

    @staticmethod
    def _resolve_title(
        session: Session,
        mapping: VideoMapping,
        video_info: VideoInfo,
        errors: list[SessionProcessError],
    ) -> str | None:
        """タイトルを解決する。フラグtrueなら生成、falseならYouTube既存値を使用。

        生成に失敗した場合はerrorsに追加しNoneを返す。
        """
        if not mapping.update_title:
            return video_info.title

        title_result = YouTubeContentGenerator.generate_title(session=session)
        match title_result:
            case Failure(error):
                errors.append(
                    SessionProcessError(
                        session_key=str(session.slot),
                        video_id=mapping.video_id,
                        error=error,
                    ),
                )
                logger.warning(
                    "Failed to process session %s: %s",
                    session.title,
                    error.message,
                )
                return None
            case Success(generated_title):
                return str(generated_title)
        raise AssertionError  # pragma: no cover

    @staticmethod
    def _resolve_description(
        session: Session,
        mapping: VideoMapping,
        mapping_config: MappingConfig,
        video_info: VideoInfo,
        errors: list[SessionProcessError],
    ) -> str | None:
        """descriptionを解決する。フラグtrueなら生成、falseならYouTube既存値を使用。

        生成に失敗した場合はerrorsに追加しNoneを返す。
        """
        if not mapping.update_description:
            return video_info.description

        desc_result = YouTubeContentGenerator.generate_description(
            session=session,
            hashtags=mapping_config.hashtags,
            footer=mapping_config.footer,
        )
        match desc_result:
            case Failure(error):
                errors.append(
                    SessionProcessError(
                        session_key=str(session.slot),
                        video_id=mapping.video_id,
                        error=error,
                    ),
                )
                logger.warning(
                    "Failed to process session %s: %s",
                    session.title,
                    error.message,
                )
                return None
            case Success(generated_desc):
                return str(generated_desc)
        raise AssertionError  # pragma: no cover

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
