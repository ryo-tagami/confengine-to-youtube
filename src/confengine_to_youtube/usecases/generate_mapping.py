"""マッピングファイル雛形生成ユースケース"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable
    from datetime import datetime
    from typing import TextIO

    from confengine_to_youtube.usecases.protocols import (
        ConfEngineApiProtocol,
        MappingWriterProtocol,
    )


@dataclass(frozen=True)
class GenerateMappingResult:
    session_count: int


class GenerateMappingUseCase:
    def __init__(
        self,
        confengine_api: ConfEngineApiProtocol,
        mapping_writer: MappingWriterProtocol,
        clock: Callable[[], datetime],
    ) -> None:
        self._confengine_api = confengine_api
        self._mapping_writer = mapping_writer
        self._clock = clock

    def execute(
        self,
        conf_id: str,
        output: TextIO,
    ) -> GenerateMappingResult:
        schedule = self._confengine_api.fetch_schedule(conf_id=conf_id)

        self._mapping_writer.write(
            sessions=schedule.sessions,
            output=output,
            conf_id=schedule.conf_id,
            generated_at=self._clock(),
        )

        return GenerateMappingResult(session_count=len(schedule.sessions))
