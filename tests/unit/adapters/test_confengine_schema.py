"""ConfEngine スキーマのテスト"""

from confengine_to_youtube.adapters.confengine_schema import (
    ScheduleResponse,
    Speaker,
)


class TestSpeaker:
    """Speaker のテスト"""

    def test_create_speaker(self) -> None:
        """スピーカーを作成できる"""
        speaker = Speaker(first_name="Test", last_name="Speaker")

        assert speaker.first_name == "Test"
        assert speaker.last_name == "Speaker"


class TestScheduleResponse:
    """ScheduleResponse のテスト"""

    def test_parse_response(self) -> None:
        """APIレスポンスをパースできる"""
        data = {
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
        response = ScheduleResponse.model_validate(obj=data)

        assert len(response.conf_schedule) == 1
        assert len(response.conf_schedule[0].schedule_days) == 1
