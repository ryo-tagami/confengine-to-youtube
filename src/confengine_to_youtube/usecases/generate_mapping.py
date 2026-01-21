"""マッピングファイル雛形生成ユースケース"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from returns.context import RequiresContextIOResultE
from returns.io import IOResult

from confengine_to_youtube.usecases.deps import GenerateMappingDeps

if TYPE_CHECKING:
    from typing import TextIO

    from confengine_to_youtube.domain.session import Session


@dataclass(frozen=True)
class GenerateMappingResult:
    session_count: int


def generate_mapping(
    conf_id: str,
    output: TextIO,
) -> RequiresContextIOResultE[GenerateMappingResult, GenerateMappingDeps]:
    """マッピングファイル雛形を生成する"""
    return RequiresContextIOResultE[GenerateMappingResult, GenerateMappingDeps](
        lambda deps: _execute(deps=deps, conf_id=conf_id, output=output),
    )


def _execute(
    deps: GenerateMappingDeps,
    conf_id: str,
    output: TextIO,
) -> IOResult[GenerateMappingResult, Exception]:
    """メインの実行ロジック"""
    return IOResult.do(
        result
        for (sessions, _timezone) in deps.confengine_api.fetch_sessions(
            conf_id=conf_id,
        )
        for result in _write_mapping(
            deps=deps,
            sessions=sessions,
            conf_id=conf_id,
            output=output,
        )
    )


def _write_mapping(
    deps: GenerateMappingDeps,
    sessions: tuple[Session, ...],
    conf_id: str,
    output: TextIO,
) -> IOResult[GenerateMappingResult, Exception]:
    """マッピングファイルを書き込み、結果を返す"""
    return deps.mapping_writer.write(
        sessions=sessions,
        output=output,
        conf_id=conf_id,
        generated_at=deps.clock(),
    ).map(lambda _: GenerateMappingResult(session_count=len(sessions)))
