from datetime import datetime
from io import StringIO
from unittest.mock import MagicMock, patch
from zoneinfo import ZoneInfo

import pytest

from confengine_to_youtube.adapters.mapping_file_writer import MappingFileWriter
from confengine_to_youtube.domain.abstract_markdown import AbstractMarkdown
from confengine_to_youtube.domain.schedule_slot import ScheduleSlot
from confengine_to_youtube.domain.session import Session, Speaker
from confengine_to_youtube.usecases.generate_mapping import (
    GenerateMappingResult,
    GenerateMappingUseCase,
)

JST = ZoneInfo(key="Asia/Tokyo")


class TestGenerateMappingUseCase:
    @pytest.fixture
    def sessions(self) -> list[Session]:
        return [
            Session(
                slot=ScheduleSlot(
                    timeslot=datetime(
                        year=2026, month=1, day=7, hour=10, minute=0, tzinfo=JST
                    ),
                    room="Hall A",
                ),
                title="Session 1",
                track="Track 1",
                speakers=(Speaker(first_name="Speaker", last_name="A"),),
                abstract=AbstractMarkdown(content="Abstract 1"),
                url="https://example.com/1",
            ),
            Session(
                slot=ScheduleSlot(
                    timeslot=datetime(
                        year=2026, month=1, day=7, hour=11, minute=0, tzinfo=JST
                    ),
                    room="Hall A",
                ),
                title="Session 2",
                track="Track 1",
                speakers=(Speaker(first_name="Speaker", last_name="B"),),
                abstract=AbstractMarkdown(content="Abstract 2"),
                url="https://example.com/2",
            ),
        ]

    @pytest.fixture
    def mock_confengine_api(self, sessions: list[Session]) -> MagicMock:
        mock = MagicMock()
        mock.fetch_sessions.return_value = (sessions, JST)
        return mock

    @pytest.fixture
    def usecase(self, mock_confengine_api: MagicMock) -> GenerateMappingUseCase:
        return GenerateMappingUseCase(
            confengine_api=mock_confengine_api,
            mapping_writer=MappingFileWriter(),
        )

    def test_execute_writes_yaml_content(self, usecase: GenerateMappingUseCase) -> None:
        fixed_now = datetime(
            year=2026, month=1, day=19, hour=10, minute=30, second=0, tzinfo=JST
        )
        with patch(
            target="confengine_to_youtube.usecases.generate_mapping.datetime"
        ) as mock_datetime:
            mock_datetime.now.return_value = fixed_now
            output = StringIO()
            result = usecase.execute(conf_id="test-conf", output=output)
            yaml_content = output.getvalue()

        assert isinstance(result, GenerateMappingResult)
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

    def test_execute_returns_session_count(
        self, usecase: GenerateMappingUseCase
    ) -> None:
        output = StringIO()
        result = usecase.execute(conf_id="test-conf", output=output)

        assert result.session_count == 2

    def test_execute_calls_confengine_api(
        self, usecase: GenerateMappingUseCase, mock_confengine_api: MagicMock
    ) -> None:
        output = StringIO()
        usecase.execute(conf_id="test-conf", output=output)

        mock_confengine_api.fetch_sessions.assert_called_once_with(conf_id="test-conf")

    def test_execute_with_empty_sessions(self, mock_confengine_api: MagicMock) -> None:
        mock_confengine_api.fetch_sessions.return_value = ([], JST)
        usecase = GenerateMappingUseCase(
            confengine_api=mock_confengine_api,
            mapping_writer=MappingFileWriter(),
        )

        fixed_now = datetime(
            year=2026, month=1, day=19, hour=10, minute=30, second=0, tzinfo=JST
        )
        with patch(
            target="confengine_to_youtube.usecases.generate_mapping.datetime"
        ) as mock_datetime:
            mock_datetime.now.return_value = fixed_now
            output = StringIO()
            result = usecase.execute(conf_id="test-conf", output=output)
            yaml_content = output.getvalue()

        assert result.session_count == 0
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
