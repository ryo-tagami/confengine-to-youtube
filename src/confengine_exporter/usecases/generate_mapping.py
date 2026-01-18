"""マッピングファイル雛形生成ユースケース"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import TextIO

    from confengine_exporter.adapters.confengine_api import ConfEngineApiGateway
    from confengine_exporter.adapters.mapping_file_writer import MappingFileWriter


@dataclass
class GenerateMappingResult:
    session_count: int


class GenerateMappingUseCase:
    def __init__(
        self,
        confengine_api: ConfEngineApiGateway,
        mapping_writer: MappingFileWriter,
    ) -> None:
        self._confengine_api = confengine_api
        self._mapping_writer = mapping_writer

    def execute(self, conf_id: str, output: TextIO) -> GenerateMappingResult:
        sessions, timezone = self._confengine_api.fetch_sessions(conf_id=conf_id)

        self._mapping_writer.write(
            sessions=sessions,
            output=output,
            conf_id=conf_id,
            generated_at=datetime.now(tz=timezone),
        )

        return GenerateMappingResult(session_count=len(sessions))
