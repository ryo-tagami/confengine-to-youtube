from datetime import datetime
from io import StringIO
from zoneinfo import ZoneInfo

import pytest
from returns.pipeline import is_successful
from returns.unsafe import unsafe_perform_io

from confengine_to_youtube.adapters.mapping_file_writer import MappingFileWriter
from confengine_to_youtube.domain.session import Session
from confengine_to_youtube.usecases.deps import GenerateMappingDeps
from confengine_to_youtube.usecases.generate_mapping import (
    GenerateMappingResult,
    generate_mapping,
)
from confengine_to_youtube.usecases.protocols import ConfEngineApiProtocol
from tests.conftest import create_session
from tests.integration.usecases.conftest import create_mock_confengine_api


class TestGenerateMapping:
    @pytest.fixture
    def fixed_clock(self, jst: ZoneInfo) -> datetime:
        """テスト用の固定時刻"""
        return datetime(
            year=2026,
            month=1,
            day=19,
            hour=10,
            minute=30,
            second=0,
            tzinfo=jst,
        )

    @pytest.fixture
    def sessions(self, jst: ZoneInfo) -> tuple[Session, ...]:
        return (
            create_session(
                title="Session 1",
                speakers=[("Speaker", "A")],
                abstract="Abstract 1",
                timeslot=datetime(
                    year=2026,
                    month=1,
                    day=7,
                    hour=10,
                    minute=0,
                    tzinfo=jst,
                ),
                room="Hall A",
                url="https://example.com/1",
            ),
            create_session(
                title="Session 2",
                speakers=[("Speaker", "B")],
                abstract="Abstract 2",
                timeslot=datetime(
                    year=2026,
                    month=1,
                    day=7,
                    hour=11,
                    minute=0,
                    tzinfo=jst,
                ),
                room="Hall A",
                url="https://example.com/2",
            ),
        )

    @pytest.fixture
    def mock_confengine_api(
        self,
        sessions: tuple[Session, ...],
        jst: ZoneInfo,
    ) -> ConfEngineApiProtocol:
        return create_mock_confengine_api(sessions=sessions, timezone=jst)

    @pytest.fixture
    def deps(
        self,
        mock_confengine_api: ConfEngineApiProtocol,
        fixed_clock: datetime,
    ) -> GenerateMappingDeps:
        return GenerateMappingDeps(
            confengine_api=mock_confengine_api,
            mapping_writer=MappingFileWriter(),
            clock=lambda: fixed_clock,
        )

    def test_execute_writes_yaml_content(self, deps: GenerateMappingDeps) -> None:
        """YAMLコンテンツが正しく生成される"""
        output = StringIO()
        result = generate_mapping(conf_id="test-conf", output=output)(deps)

        assert is_successful(result)
        mapping_result = unsafe_perform_io(result.unwrap())

        yaml_content = output.getvalue()

        assert isinstance(mapping_result, GenerateMappingResult)
        expected = (
            "# ConfEngine Mapping Template\n"
            "# Generated: 2026-01-19T10:30:00+09:00\n"
            "conf_id: test-conf\n"
            "# ハッシュタグ\n"
            "# 例:\n"
            "#   hashtags:\n"
            "#     - '#RSGT2026'\n"
            "#     - '#Agile'\n"
            "hashtags: []\n"
            "# フッター (複数行の場合はリテラルブロック `|` を使用)\n"
            "# 例:\n"
            "#   footer: |\n"
            "#     1行目\n"
            "#     2行目\n"
            "footer: ''\n"
            "sessions:\n"
            "  2026-01-07:\n"
            "    Hall A:\n"
            "      10:00:\n"
            "        # Session 1 - Speaker A\n"
            "        video_id: ''\n"
            "      11:00:\n"
            "        # Session 2 - Speaker B\n"
            "        video_id: ''\n"
        )
        assert yaml_content == expected

    def test_execute_returns_session_count(self, deps: GenerateMappingDeps) -> None:
        output = StringIO()
        result = generate_mapping(conf_id="test-conf", output=output)(deps)

        assert is_successful(result)
        mapping_result = unsafe_perform_io(result.unwrap())
        assert mapping_result.session_count == 2

    def test_execute_calls_confengine_api(
        self,
        deps: GenerateMappingDeps,
        mock_confengine_api: ConfEngineApiProtocol,
    ) -> None:
        output = StringIO()
        generate_mapping(conf_id="test-conf", output=output)(deps)

        mock_confengine_api.fetch_sessions.assert_called_once_with(conf_id="test-conf")  # type: ignore[attr-defined]

    def test_execute_with_empty_sessions(
        self,
        fixed_clock: datetime,
        jst: ZoneInfo,
    ) -> None:
        """セッションが空の場合も正しく生成される"""
        mock_confengine_api = create_mock_confengine_api(sessions=(), timezone=jst)
        deps = GenerateMappingDeps(
            confengine_api=mock_confengine_api,
            mapping_writer=MappingFileWriter(),
            clock=lambda: fixed_clock,
        )

        output = StringIO()
        result = generate_mapping(conf_id="test-conf", output=output)(deps)

        assert is_successful(result)
        mapping_result = unsafe_perform_io(result.unwrap())
        yaml_content = output.getvalue()

        assert mapping_result.session_count == 0
        expected = (
            "# ConfEngine Mapping Template\n"
            "# Generated: 2026-01-19T10:30:00+09:00\n"
            "conf_id: test-conf\n"
            "# ハッシュタグ\n"
            "# 例:\n"
            "#   hashtags:\n"
            "#     - '#RSGT2026'\n"
            "#     - '#Agile'\n"
            "hashtags: []\n"
            "# フッター (複数行の場合はリテラルブロック `|` を使用)\n"
            "# 例:\n"
            "#   footer: |\n"
            "#     1行目\n"
            "#     2行目\n"
            "footer: ''\n"
            "sessions: {}\n"
        )
        assert yaml_content == expected
