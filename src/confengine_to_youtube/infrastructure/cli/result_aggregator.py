"""セッション処理結果の集約

ユースケースから返された未集約の SessionProcessingBatch を
YouTubeUpdateResult に変換する。

このモジュールは infrastructure 層に配置し、unsafe_perform_io の使用を
この境界に限定する (returns ライブラリの推奨パターン)。
"""

from __future__ import annotations

from returns.io import IOFailure, IOSuccess
from returns.unsafe import unsafe_perform_io

from confengine_to_youtube.usecases.dto import (
    SessionProcessingBatch,
    UpdatePreview,
    YouTubeUpdateResult,
)


def aggregate_session_results(batch: SessionProcessingBatch) -> YouTubeUpdateResult:
    """未集約のセッション処理結果を集約する

    Args:
        batch: ユースケースから返された未集約の結果

    Returns:
        集約された YouTubeUpdateResult

    """
    previews: list[UpdatePreview] = []
    errors: list[str] = []
    updated_count = 0

    for result in batch.results:
        match result:
            case IOSuccess():
                preview = unsafe_perform_io(result.unwrap())
                previews.append(preview)
                if not batch.is_dry_run and preview.error is None:
                    updated_count += 1
            case IOFailure():
                error = unsafe_perform_io(result.failure())
                errors.append(error.message)
                previews.append(
                    UpdatePreview(
                        session_key=error.session_key,
                        video_id=error.video_id,
                        current_title=None,
                        current_description=None,
                        new_title=None,
                        new_description=None,
                        error=error.message,
                    ),
                )

    return YouTubeUpdateResult(
        is_dry_run=batch.is_dry_run,
        previews=tuple(previews),
        updated_count=updated_count,
        no_content_count=batch.no_content_count,
        no_mapping_count=batch.no_mapping_count,
        unused_mappings_count=batch.unused_mappings_count,
        errors=tuple(errors),
    )
