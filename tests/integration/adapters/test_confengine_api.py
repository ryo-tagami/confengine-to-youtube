"""ConfEngine API Gateway のテスト"""

from datetime import datetime
from unittest.mock import create_autospec
from zoneinfo import ZoneInfo

from confengine_to_youtube.adapters.confengine_api import ConfEngineApiGateway
from confengine_to_youtube.adapters.markdown_converter import MarkdownConverter
from confengine_to_youtube.adapters.protocols import HttpClientProtocol
from confengine_to_youtube.domain.session_abstract import SessionAbstract
from confengine_to_youtube.domain.speaker import Speaker


class TestConfEngineApiGateway:
    """ConfEngineApiGateway のテスト"""

    def test_fetch_schedule(self, jst: ZoneInfo) -> None:
        """APIからスケジュールを取得できる"""
        mock_http_client = create_autospec(HttpClientProtocol, spec_set=True)
        mock_http_client.get_json.return_value = {
            "conf_timezone": "Asia/Tokyo",
            "conf_schedule": [
                {
                    "schedule_days": [
                        {
                            "sessions": [
                                {
                                    "1234567890": [
                                        {
                                            "timeslot": "2026-01-07 10:00:00",
                                            "title": "Test Session",
                                            "room": "Hall A",
                                            "track": "Track 1",
                                            "url": "https://example.com",
                                            "abstract": "<p>Test</p>",
                                            "speakers": [
                                                {
                                                    "name": "Speaker A",
                                                    "first_name": "Speaker",
                                                    "last_name": "A",
                                                },
                                            ],
                                        },
                                    ],
                                },
                            ],
                        },
                    ],
                },
            ],
        }

        gateway = ConfEngineApiGateway(
            http_client=mock_http_client,
            markdown_converter=MarkdownConverter(),
        )
        schedule = gateway.fetch_schedule(conf_id="test-conf")

        assert schedule.conf_id == "test-conf"
        assert schedule.timezone == jst
        assert len(schedule.sessions) == 1
        session = schedule.sessions[0]

        # 全フィールドのマッピングを検証

        assert session.title == "Test Session"
        assert session.slot.timeslot == datetime(
            year=2026,
            month=1,
            day=7,
            hour=10,
            minute=0,
            second=0,
            tzinfo=jst,
        )
        assert session.slot.room == "Hall A"
        assert session.track == "Track 1"
        assert session.speakers == (Speaker(first_name="Speaker", last_name="A"),)
        assert session.abstract == SessionAbstract(content="Test")
        assert session.url == "https://example.com"

        # 正しいURLでAPIが呼ばれたことを検証
        mock_http_client.get_json.assert_called_once_with(
            url="https://confengine.com/api/v3/conferences/test-conf/schedule",
        )

    def test_sessions_sorted_by_timeslot_and_room(self) -> None:
        """セッションがtimeslotとroomでソートされる"""
        mock_http_client = create_autospec(HttpClientProtocol, spec_set=True)
        mock_http_client.get_json.return_value = {
            "conf_timezone": "Asia/Tokyo",
            "conf_schedule": [
                {
                    "schedule_days": [
                        {
                            "sessions": [
                                {
                                    "1": [
                                        {
                                            "timeslot": "2026-01-07 11:00:00",
                                            "title": "Session B",
                                            "room": "Hall A",
                                            "track": "Track 1",
                                            "url": "https://example.com",
                                            "abstract": "",
                                            "speakers": [],
                                        },
                                        {
                                            "timeslot": "2026-01-07 10:00:00",
                                            "title": "Session A",
                                            "room": "Hall B",
                                            "track": "Track 1",
                                            "url": "https://example.com",
                                            "abstract": "",
                                            "speakers": [],
                                        },
                                        {
                                            "timeslot": "2026-01-07 10:00:00",
                                            "title": "Session C",
                                            "room": "Hall A",
                                            "track": "Track 1",
                                            "url": "https://example.com",
                                            "abstract": "",
                                            "speakers": [],
                                        },
                                    ],
                                },
                            ],
                        },
                    ],
                },
            ],
        }

        gateway = ConfEngineApiGateway(
            http_client=mock_http_client,
            markdown_converter=MarkdownConverter(),
        )
        schedule = gateway.fetch_schedule(conf_id="test-conf")

        assert len(schedule.sessions) == 3
        assert schedule.sessions[0].title == "Session C"  # 10:00, Hall A
        assert schedule.sessions[1].title == "Session A"  # 10:00, Hall B
        assert schedule.sessions[2].title == "Session B"  # 11:00, Hall A
