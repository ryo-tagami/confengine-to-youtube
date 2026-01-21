"""YouTube description更新ユースケース"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from returns.context import RequiresContextIOResultE
from returns.io import IOResult, IOSuccess

from confengine_to_youtube.usecases.deps import UpdateYouTubeDeps
from confengine_to_youtube.usecases.dto import (
    SessionProcessingBatch,
    SessionProcessingError,
    UpdatePreview,
)
from confengine_to_youtube.usecases.protocols import VideoInfo, VideoUpdateRequest

logger = logging.getLogger(name=__name__)

if TYPE_CHECKING:
    from pathlib import Path

    from confengine_to_youtube.domain.schedule_slot import ScheduleSlot
    from confengine_to_youtube.domain.session import Session
    from confengine_to_youtube.domain.video_mapping import MappingConfig, VideoMapping
    from confengine_to_youtube.domain.youtube_description import YouTubeDescription
    from confengine_to_youtube.domain.youtube_title import YouTubeTitle


def update_youtube_descriptions(
    mapping_file: Path,
    *,
    dry_run: bool,
) -> RequiresContextIOResultE[SessionProcessingBatch, UpdateYouTubeDeps]:
    """YouTube説明文を更新する

    Returns:
        SessionProcessingBatch: 未集約のセッション処理結果。
        CLI層で aggregate_session_results() を使って YouTubeUpdateResult に変換する。

    """
    return RequiresContextIOResultE[SessionProcessingBatch, UpdateYouTubeDeps](
        lambda deps: _execute(deps=deps, mapping_file=mapping_file, dry_run=dry_run),
    )


def _execute(
    deps: UpdateYouTubeDeps,
    mapping_file: Path,
    *,
    dry_run: bool,
) -> IOResult[SessionProcessingBatch, Exception]:
    """メインの実行ロジック"""
    return IOResult.do(
        _process_sessions(
            deps=deps,
            sessions=sessions,
            mapping_config=mapping.to_domain(timezone=timezone),
            dry_run=dry_run,
        )
        for mapping in deps.mapping_reader.read(file_path=mapping_file)
        for (sessions, timezone) in deps.confengine_api.fetch_sessions(
            conf_id=mapping.conf_id,
        )
    )


def _process_sessions(
    deps: UpdateYouTubeDeps,
    sessions: tuple[Session, ...],
    mapping_config: MappingConfig,
    *,
    dry_run: bool,
) -> SessionProcessingBatch:
    """全セッションを処理 (未集約の結果を返す)"""
    # 1. コンテンツなしセッションを除外
    content_sessions = tuple(session for session in sessions if session.has_content)
    no_content_count = len(sessions) - len(content_sessions)

    # 2. マッピングを付与し、マッピングなしを分離
    sessions_with_mapping = tuple(
        (session, mapping_config.find_mapping(slot=session.slot))
        for session in content_sessions
    )
    processable = tuple(
        (session, mapping)
        for session, mapping in sessions_with_mapping
        if mapping is not None
    )
    no_mapping_count = len(sessions_with_mapping) - len(processable)

    # 3. 処理可能なセッションを処理
    results = tuple(
        _process_session(
            deps=deps,
            session=session,
            mapping=mapping,
            mapping_config=mapping_config,
            dry_run=dry_run,
        )
        for session, mapping in processable
    )

    # 4. 使用済みスロットから未使用マッピングを計算
    used_slots = frozenset(session.slot for session, _ in processable)
    unused_count = _warn_unused_mappings(
        mapping_config=mapping_config,
        used_slots=used_slots,
    )

    return SessionProcessingBatch(
        results=results,
        no_content_count=no_content_count,
        no_mapping_count=no_mapping_count,
        unused_mappings_count=unused_count,
        is_dry_run=dry_run,
    )


def _process_session(
    deps: UpdateYouTubeDeps,
    session: Session,
    mapping: VideoMapping,
    mapping_config: MappingConfig,
    *,
    dry_run: bool,
) -> IOResult[UpdatePreview, SessionProcessingError]:
    """単一セッションを処理"""
    session_key = str(session.slot)

    def to_error(message: str) -> SessionProcessingError:
        return SessionProcessingError(
            session_key=session_key,
            video_id=mapping.video_id,
            message=message,
        )

    # 動画情報を取得 → タイトル生成 → 説明文生成 → プレビュー作成
    return IOResult.do(
        preview
        for video_info in deps.youtube_api.get_video_info(
            video_id=mapping.video_id,
        ).alt(lambda e: to_error(str(e)))
        for new_title in IOResult.from_result(
            deps.title_builder.build(session=session).alt(
                lambda e: to_error(e.message),
            ),
        )
        for description in IOResult.from_result(
            deps.description_builder.build(
                session=session,
                hashtags=mapping_config.hashtags,
                footer=mapping_config.footer,
            ).alt(lambda e: to_error(e.message)),
        )
        for preview in _create_preview_and_update(
            deps=deps,
            session=session,
            mapping=mapping,
            video_info=video_info,
            new_title=new_title,
            description=description,
            dry_run=dry_run,
        )
    )


def _create_preview_and_update(  # noqa: PLR0913
    deps: UpdateYouTubeDeps,
    session: Session,
    mapping: VideoMapping,
    video_info: VideoInfo,
    new_title: YouTubeTitle,
    description: YouTubeDescription,
    *,
    dry_run: bool,
) -> IOResult[UpdatePreview, SessionProcessingError]:
    """プレビューを作成し、必要に応じて更新を実行"""
    session_key = str(session.slot)
    preview = UpdatePreview(
        session_key=session_key,
        video_id=mapping.video_id,
        current_title=video_info.title,
        current_description=video_info.description,
        new_title=str(new_title),
        new_description=str(description),
    )

    if dry_run:
        return IOSuccess(preview)

    request = VideoUpdateRequest(
        video_id=mapping.video_id,
        title=str(new_title),
        description=str(description),
        category_id=video_info.category_id,
    )

    def on_update_success(_: None) -> UpdatePreview:
        return _log_and_return_preview(
            session=session,
            mapping=mapping,
            preview=preview,
        )

    return (
        deps.youtube_api.update_video(request=request)
        .alt(
            lambda e: SessionProcessingError(
                session_key=session_key,
                video_id=mapping.video_id,
                message=str(e),
            ),
        )
        .map(on_update_success)
    )


def _log_and_return_preview(
    session: Session,
    mapping: VideoMapping,
    preview: UpdatePreview,
) -> UpdatePreview:
    """ログを出力してプレビューを返す"""
    logger.info("Updated: %s (%s)", session.title, mapping.video_id)
    return preview


def _warn_unused_mappings(
    mapping_config: MappingConfig,
    used_slots: frozenset[ScheduleSlot],
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
