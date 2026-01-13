"""エクスポートユースケースのテスト"""

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from confengine_exporter.adapters.file_writer import SessionFileWriter
from confengine_exporter.adapters.markdown_builder import (
    MarkdownOptions,
    SessionMarkdownBuilder,
)
from confengine_exporter.domain.session import Session
from confengine_exporter.usecases.export_sessions import ExportSessionsUseCase


@pytest.fixture
def mock_api_gateway() -> MagicMock:
    """テスト用の API Gateway モック"""
    return MagicMock()


@pytest.fixture
def markdown_builder() -> SessionMarkdownBuilder:
    """テスト用の Markdown ビルダー"""
    return SessionMarkdownBuilder(options=MarkdownOptions(hashtags="", footer_text=""))


@pytest.fixture
def file_writer(tmp_path: Path) -> SessionFileWriter:
    """テスト用のファイルライター"""
    return SessionFileWriter(output_dir=tmp_path)


class TestExportSessionsUseCase:
    """ExportSessionsUseCase のテスト"""

    def test_execute_exports_sessions(
        self,
        mock_api_gateway: MagicMock,
        markdown_builder: SessionMarkdownBuilder,
        file_writer: SessionFileWriter,
        sample_session: Session,
    ) -> None:
        """セッションがエクスポートされる"""
        mock_api_gateway.fetch_sessions.return_value = [sample_session]

        usecase = ExportSessionsUseCase(
            api_gateway=mock_api_gateway,
            markdown_builder=markdown_builder,
            file_writer=file_writer,
        )

        result = usecase.execute(conf_id="test-conf")

        assert result.exported_count == 1
        assert result.output_dir == str(file_writer.output_dir)
        mock_api_gateway.fetch_sessions.assert_called_once_with(conf_id="test-conf")

        files = list(file_writer.output_dir.glob("*.md"))
        assert len(files) == 1

        expected = (
            "# Sample Session\n"
            "\n"
            "Speaker: Speaker A, Speaker B\n"
            "\n"
            "This is a sample abstract.\n"
            "\n"
            "***\n"
            "\n"
            "https://example.com/session/1\n"
            "\n"
            "***"
        )
        assert files[0].read_text() == expected

    def test_execute_skips_empty_sessions(
        self,
        mock_api_gateway: MagicMock,
        markdown_builder: SessionMarkdownBuilder,
        file_writer: SessionFileWriter,
        sample_session: Session,
        empty_session: Session,
    ) -> None:
        """has_content=False のセッションはスキップされる"""
        mock_api_gateway.fetch_sessions.return_value = [sample_session, empty_session]

        usecase = ExportSessionsUseCase(
            api_gateway=mock_api_gateway,
            markdown_builder=markdown_builder,
            file_writer=file_writer,
        )

        result = usecase.execute(conf_id="test-conf")

        assert result.exported_count == 1

        files = list(file_writer.output_dir.glob("*.md"))
        assert len(files) == 1

    def test_execute_returns_zero_when_no_content(
        self,
        mock_api_gateway: MagicMock,
        markdown_builder: SessionMarkdownBuilder,
        file_writer: SessionFileWriter,
        empty_session: Session,
    ) -> None:
        """コンテンツのあるセッションがない場合は0を返す"""
        mock_api_gateway.fetch_sessions.return_value = [empty_session]

        usecase = ExportSessionsUseCase(
            api_gateway=mock_api_gateway,
            markdown_builder=markdown_builder,
            file_writer=file_writer,
        )

        result = usecase.execute(conf_id="test-conf")

        assert result.exported_count == 0

        files = list(file_writer.output_dir.glob("*.md"))
        assert len(files) == 0
