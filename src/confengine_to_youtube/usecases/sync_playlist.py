"""プレイリスト同期ユースケース"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from confengine_to_youtube.usecases.dto import (
    PlaylistOperationType,
    PlaylistSyncResult,
    PlaylistVideoOperation,
)

logger = logging.getLogger(name=__name__)

if TYPE_CHECKING:
    from pathlib import Path

    from confengine_to_youtube.domain.conference_schedule import ConferenceSchedule
    from confengine_to_youtube.domain.video_mapping import MappingConfig
    from confengine_to_youtube.usecases.protocols import (
        ConfEngineApiProtocol,
        MappingFileReaderProtocol,
        YouTubeApiProtocol,
    )


class SyncPlaylistUseCase:
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
        dry_run: bool,
    ) -> PlaylistSyncResult:
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
    ) -> PlaylistSyncResult:
        """プレイリストに動画を同期する

        1. プレイリスト内の全アイテムを取得
        2. セッション順で動画をループし、追加または位置更新
        3. マッピングにない動画を末尾に移動
        """
        playlist_id = mapping_config.playlist_id

        # プレイリスト内の既存アイテムを取得
        existing_items = self._youtube_api.list_playlist_items(playlist_id=playlist_id)

        operations: list[PlaylistVideoOperation] = []
        added_count = 0
        reordered_count = 0
        unchanged_count = 0
        moved_to_end_count = 0

        # マッピングされた動画のvideo_idを追跡
        mapped_video_ids: set[str] = set()

        # セッションは既にソート済み (日付→時間→ルーム)
        position = 0
        for session in schedule.sessions:
            mapping = mapping_config.find_mapping(slot=session.slot)
            if mapping is None:
                continue

            video_id = mapping.video_id
            mapped_video_ids.add(video_id)

            existing_item = existing_items.get(video_id)

            if existing_item is None:
                # 新規追加
                operations.append(
                    PlaylistVideoOperation(
                        video_id=video_id,
                        title=session.title,
                        operation=PlaylistOperationType.ADD,
                        position=position,
                        slot=session.slot,
                    ),
                )
                added_count += 1
                if not dry_run:
                    self._youtube_api.add_to_playlist(
                        playlist_id=playlist_id,
                        video_id=video_id,
                        position=position,
                    )
                    logger.info(
                        "Added to playlist: %s (%s) at position %d",
                        session.title,
                        video_id,
                        position,
                    )
                    # 追加後に position が変わるため再取得
                    existing_items = self._youtube_api.list_playlist_items(
                        playlist_id=playlist_id,
                    )
            elif existing_item.position != position:
                # 位置更新
                operations.append(
                    PlaylistVideoOperation(
                        video_id=video_id,
                        title=session.title,
                        operation=PlaylistOperationType.REORDER,
                        position=position,
                        slot=session.slot,
                    ),
                )
                reordered_count += 1
                if not dry_run:
                    self._youtube_api.update_playlist_item_position(
                        playlist_item_id=existing_item.playlist_item_id,
                        playlist_id=playlist_id,
                        video_id=video_id,
                        position=position,
                    )
                    logger.info(
                        "Reordered in playlist: %s (%s) to position %d",
                        session.title,
                        video_id,
                        position,
                    )
                    # 移動後に他の動画の position が変わるため再取得
                    existing_items = self._youtube_api.list_playlist_items(
                        playlist_id=playlist_id,
                    )
            else:
                # 変更なし
                operations.append(
                    PlaylistVideoOperation(
                        video_id=video_id,
                        title=session.title,
                        operation=PlaylistOperationType.UNCHANGED,
                        position=position,
                        slot=session.slot,
                    ),
                )
                unchanged_count += 1

            position += 1

        # マッピングにない動画を末尾に移動。元の位置順でソート
        unmapped_items = sorted(
            [
                item
                for item in existing_items.values()
                if item.video_id not in mapped_video_ids
            ],
            key=lambda item: item.position,
        )

        for item in unmapped_items:
            video_id = item.video_id
            if item.position != position:
                operations.append(
                    PlaylistVideoOperation(
                        video_id=video_id,
                        title=f"(unmapped: {video_id})",
                        operation=PlaylistOperationType.MOVE_TO_END,
                        position=position,
                    ),
                )
                moved_to_end_count += 1
                if not dry_run:
                    self._youtube_api.update_playlist_item_position(
                        playlist_item_id=item.playlist_item_id,
                        playlist_id=playlist_id,
                        video_id=video_id,
                        position=position,
                    )
                    logger.info(
                        "Moved to end: %s at position %d",
                        video_id,
                        position,
                    )
            else:
                # マッピングなしの動画がすでに正しい位置にある
                operations.append(
                    PlaylistVideoOperation(
                        video_id=video_id,
                        title=f"(unmapped: {video_id})",
                        operation=PlaylistOperationType.UNCHANGED,
                        position=position,
                    ),
                )
                unchanged_count += 1
            position += 1

        return PlaylistSyncResult(
            is_dry_run=dry_run,
            playlist_id=playlist_id,
            added_count=added_count,
            reordered_count=reordered_count,
            unchanged_count=unchanged_count,
            moved_to_end_count=moved_to_end_count,
            operations=tuple(operations),
        )
