"""ConfEngine スキーマのテスト"""

from datetime import UTC, datetime

from confengine_exporter.adapters.confengine_schema import (
    ApiSession,
    ScheduleResponse,
    Speaker,
)


class TestSpeaker:
    """Speaker のテスト"""

    def test_create_speaker(self) -> None:
        """スピーカーを作成できる"""
        speaker = Speaker(name="Test Speaker")

        assert speaker.name == "Test Speaker"


class TestApiSession:
    """ApiSession のテスト"""

    def test_speaker_names(self) -> None:
        """speaker_names がスピーカー名のリストを返す"""
        session = ApiSession(
            timeslot=datetime(
                year=2026, month=1, day=7, hour=10, minute=0, second=0, tzinfo=UTC
            ),
            title="Test Session",
            room="Hall A",
            track="Track 1",
            url="https://example.com",
            abstract="",
            speakers=[Speaker(name="Speaker A"), Speaker(name="Speaker B")],
        )

        assert session.speaker_names == ["Speaker A", "Speaker B"]

    def test_speaker_names_filters_empty(self) -> None:
        """speaker_names は空の名前を除外する"""
        session = ApiSession(
            timeslot=datetime(
                year=2026, month=1, day=7, hour=10, minute=0, second=0, tzinfo=UTC
            ),
            title="Test Session",
            room="Hall A",
            track="Track 1",
            url="https://example.com",
            abstract="",
            speakers=[Speaker(name="Speaker A"), Speaker(name="")],
        )

        assert session.speaker_names == ["Speaker A"]

    def test_abstract_markdown_converts_html(self) -> None:
        """abstract_markdown が HTML を Markdown に変換する"""
        session = ApiSession(
            timeslot=datetime(
                year=2026, month=1, day=7, hour=10, minute=0, second=0, tzinfo=UTC
            ),
            title="Test Session",
            room="Hall A",
            track="Track 1",
            url="https://example.com",
            abstract="<p>Hello <strong>World</strong></p>",
            speakers=[],
        )

        assert session.abstract_markdown == "Hello **World**"

    def test_abstract_markdown_empty(self) -> None:
        """Abstract が空の場合は空文字列を返す"""
        session = ApiSession(
            timeslot=datetime(
                year=2026, month=1, day=7, hour=10, minute=0, second=0, tzinfo=UTC
            ),
            title="Test Session",
            room="Hall A",
            track="Track 1",
            url="https://example.com",
            abstract="",
            speakers=[],
        )

        assert session.abstract_markdown == ""


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
                                        }
                                    ]
                                }
                            ]
                        }
                    ]
                }
            ],
        }
        response = ScheduleResponse.model_validate(obj=data)

        assert len(response.conf_schedule) == 1
        assert len(response.conf_schedule[0].schedule_days) == 1
