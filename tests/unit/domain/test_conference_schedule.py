"""ConferenceSchedule 集約のテスト"""

from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from confengine_to_youtube.domain.conference_schedule import ConferenceSchedule
from confengine_to_youtube.domain.schedule_slot import ScheduleSlot
from confengine_to_youtube.domain.session import Session
from confengine_to_youtube.domain.session_abstract import SessionAbstract
from confengine_to_youtube.domain.speaker import Speaker
from tests.conftest import create_session


class TestConferenceSchedule:
    """ConferenceSchedule のテスト"""

    def test_create_with_valid_sessions(self, jst: ZoneInfo) -> None:
        """有効なセッションで作成できる"""
        sessions = (
            Session(
                slot=ScheduleSlot(
                    timeslot=datetime(
                        year=2026, month=1, day=7, hour=10, minute=0, tzinfo=jst
                    ),
                    room="Hall A",
                ),
                title="Session 1",
                track="Track 1",
                speakers=(Speaker(first_name="Speaker", last_name="A"),),
                abstract=SessionAbstract(content="Abstract 1"),
                url="https://example.com/1",
            ),
            Session(
                slot=ScheduleSlot(
                    timeslot=datetime(
                        year=2026, month=1, day=7, hour=11, minute=0, tzinfo=jst
                    ),
                    room="Hall A",
                ),
                title="Session 2",
                track="Track 1",
                speakers=(Speaker(first_name="Speaker", last_name="B"),),
                abstract=SessionAbstract(content="Abstract 2"),
                url="https://example.com/2",
            ),
        )

        schedule = ConferenceSchedule(
            conf_id="test-conf",
            timezone=jst,
            sessions=sessions,
        )

        assert schedule.conf_id == "test-conf"
        assert len(schedule.sessions) == 2

    def test_duplicate_slots_raises_error(self, jst: ZoneInfo) -> None:
        """同一スロットに複数セッションがある場合はエラー"""
        slot_time = datetime(year=2026, month=1, day=7, hour=10, minute=0, tzinfo=jst)
        sessions = (
            Session(
                slot=ScheduleSlot(timeslot=slot_time, room="Hall A"),
                title="Session 1",
                track="Track 1",
                speakers=(Speaker(first_name="Speaker", last_name="A"),),
                abstract=SessionAbstract(content="Abstract 1"),
                url="https://example.com/1",
            ),
            Session(
                slot=ScheduleSlot(timeslot=slot_time, room="Hall A"),
                title="Session 2",
                track="Track 1",
                speakers=(Speaker(first_name="Speaker", last_name="B"),),
                abstract=SessionAbstract(content="Abstract 2"),
                url="https://example.com/2",
            ),
        )

        with pytest.raises(ValueError, match=r"Duplicate slot detected: .+_Hall A"):
            ConferenceSchedule(
                conf_id="test-conf",
                timezone=jst,
                sessions=sessions,
            )

    def test_empty_sessions_is_valid(self) -> None:
        """セッションが空でも作成できる"""
        schedule = ConferenceSchedule(
            conf_id="test-conf",
            timezone=ZoneInfo(key="UTC"),
            sessions=(),
        )

        assert schedule.conf_id == "test-conf"
        assert len(schedule.sessions) == 0


class TestSessionsWithContent:
    """sessions_with_content() のテスト"""

    def test_returns_only_sessions_with_content(self, jst: ZoneInfo) -> None:
        """コンテンツのあるセッションのみ返す"""
        session_with_content = create_session(
            title="Session with content",
            speakers=[("Speaker", "A")],
            abstract="This has content",
            timeslot=datetime(year=2026, month=1, day=7, hour=10, minute=0, tzinfo=jst),
            room="Hall A",
            url="https://example.com/1",
        )
        session_without_content = create_session(
            title="Session without content",
            speakers=[("Speaker", "B")],
            abstract="",
            timeslot=datetime(year=2026, month=1, day=7, hour=11, minute=0, tzinfo=jst),
            room="Hall A",
            url="https://example.com/2",
        )
        schedule = ConferenceSchedule(
            conf_id="test-conf",
            timezone=jst,
            sessions=(session_with_content, session_without_content),
        )

        result = schedule.sessions_with_content()

        assert result == (session_with_content,)

    def test_returns_empty_tuple_when_no_content(self, jst: ZoneInfo) -> None:
        """全セッションにコンテンツがない場合は空タプルを返す"""
        session_without_content = create_session(
            title="Session without content",
            speakers=[],
            abstract="",
            timeslot=datetime(year=2026, month=1, day=7, hour=10, minute=0, tzinfo=jst),
            room="Hall A",
            url="https://example.com/1",
        )
        schedule = ConferenceSchedule(
            conf_id="test-conf",
            timezone=jst,
            sessions=(session_without_content,),
        )

        result = schedule.sessions_with_content()

        assert result == ()

    def test_returns_all_sessions_when_all_have_content(self, jst: ZoneInfo) -> None:
        """全セッションにコンテンツがある場合は全て返す"""
        session1 = create_session(
            title="Session 1",
            speakers=[],
            abstract="Content 1",
            timeslot=datetime(year=2026, month=1, day=7, hour=10, minute=0, tzinfo=jst),
            room="Hall A",
            url="https://example.com/1",
        )
        session2 = create_session(
            title="Session 2",
            speakers=[],
            abstract="Content 2",
            timeslot=datetime(year=2026, month=1, day=7, hour=11, minute=0, tzinfo=jst),
            room="Hall A",
            url="https://example.com/2",
        )
        schedule = ConferenceSchedule(
            conf_id="test-conf",
            timezone=jst,
            sessions=(session1, session2),
        )

        result = schedule.sessions_with_content()

        assert result == (session1, session2)
