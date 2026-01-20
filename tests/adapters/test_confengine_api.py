"""ConfEngine API Gateway のテスト"""

from datetime import datetime
from unittest.mock import MagicMock
from zoneinfo import ZoneInfo

from confengine_to_youtube.adapters.confengine_api import ConfEngineApiGateway
from confengine_to_youtube.domain.session import Speaker


class TestConfEngineApiGateway:
    """ConfEngineApiGateway のテスト"""

    def test_fetch_sessions(self) -> None:
        """APIからセッションを取得できる"""
        mock_http_client = MagicMock()
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
                                                }
                                            ],
                                        }
                                    ]
                                }
                            ]
                        }
                    ]
                }
            ],
        }

        gateway = ConfEngineApiGateway(http_client=mock_http_client)
        sessions, timezone = gateway.fetch_sessions(conf_id="test-conf")

        assert len(sessions) == 1
        session = sessions[0]

        # 全フィールドのマッピングを検証
        jst = ZoneInfo(key="Asia/Tokyo")
        assert timezone == jst

        assert session.title == "Test Session"
        assert session.timeslot == datetime(
            year=2026, month=1, day=7, hour=10, minute=0, second=0, tzinfo=jst
        )
        assert session.room == "Hall A"
        assert session.track == "Track 1"
        assert session.speakers == [Speaker(first_name="Speaker", last_name="A")]
        assert session.abstract == "Test"
        assert session.url == "https://example.com"

        # 正しいURLでAPIが呼ばれたことを検証
        mock_http_client.get_json.assert_called_once_with(
            url="https://confengine.com/api/v3/conferences/test-conf/schedule"
        )

    def test_sessions_sorted_by_timeslot_and_room(self) -> None:
        """セッションがtimeslotとroomでソートされる"""
        mock_http_client = MagicMock()
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
                                    ]
                                }
                            ]
                        }
                    ]
                }
            ],
        }

        gateway = ConfEngineApiGateway(http_client=mock_http_client)
        sessions, _ = gateway.fetch_sessions(conf_id="test-conf")

        assert len(sessions) == 3
        assert sessions[0].title == "Session C"  # 10:00, Hall A
        assert sessions[1].title == "Session A"  # 10:00, Hall B
        assert sessions[2].title == "Session B"  # 11:00, Hall A
