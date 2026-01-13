"""セッションエクスポートユースケース"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from confengine_exporter.adapters.confengine_api import ConfEngineApiGateway
    from confengine_exporter.adapters.file_writer import SessionFileWriter
    from confengine_exporter.adapters.markdown_builder import SessionMarkdownBuilder


@dataclass
class ExportResult:
    """エクスポート結果"""

    exported_count: int
    output_dir: str


class ExportSessionsUseCase:
    """セッションをエクスポートするユースケース"""

    def __init__(
        self,
        api_gateway: ConfEngineApiGateway,
        markdown_builder: SessionMarkdownBuilder,
        file_writer: SessionFileWriter,
    ) -> None:
        self.api_gateway = api_gateway
        self.markdown_builder = markdown_builder
        self.file_writer = file_writer

    def execute(self, conf_id: str) -> ExportResult:
        """セッションをエクスポート"""
        # APIからセッション取得
        sessions = self.api_gateway.fetch_sessions(conf_id=conf_id)

        # 各セッションをファイルに出力
        count = 0

        for session in sessions:
            if not session.has_content:
                continue

            markdown = self.markdown_builder.build(session=session)
            self.file_writer.write(session=session, content=markdown)

            count += 1

        return ExportResult(
            exported_count=count,
            output_dir=str(self.file_writer.output_dir),
        )
