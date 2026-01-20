"""YouTube動画タイトルビルダーのテスト"""

from datetime import UTC, datetime

from confengine_to_youtube.adapters.youtube_title_builder import YouTubeTitleBuilder
from confengine_to_youtube.domain.abstract_markdown import AbstractMarkdown
from confengine_to_youtube.domain.schedule_slot import ScheduleSlot
from confengine_to_youtube.domain.session import Session, Speaker
from confengine_to_youtube.domain.youtube_title import YouTubeTitle


class TestYouTubeTitleBuilder:
    """YouTubeTitleBuilder のテスト"""

    def test_build_basic(self, sample_session: Session) -> None:
        """基本的なタイトル生成"""
        builder = YouTubeTitleBuilder()
        title = builder.build(session=sample_session)

        assert str(title) == "Sample Session - Speaker A, Speaker B"

    def test_build_single_speaker(self) -> None:
        """単一スピーカーの場合"""
        session = Session(
            slot=ScheduleSlot(
                timeslot=datetime(year=2026, month=1, day=7, hour=10, tzinfo=UTC),
                room="Hall A",
            ),
            title="Test Session",
            track="Track 1",
            speakers=(Speaker(first_name="John", last_name="Doe"),),
            abstract=AbstractMarkdown(content="Some abstract"),
            url="https://example.com",
        )
        builder = YouTubeTitleBuilder()
        title = builder.build(session=session)

        assert str(title) == "Test Session - John Doe"

    def test_build_no_speakers(self, empty_session: Session) -> None:
        """スピーカーがいない場合"""
        builder = YouTubeTitleBuilder()
        title = builder.build(session=empty_session)

        assert str(title) == "Empty Session"

    def test_build_speakers_with_empty_names(self) -> None:
        """全スピーカーが空の名前の場合はタイトルのみ"""
        session = Session(
            slot=ScheduleSlot(
                timeslot=datetime(year=2026, month=1, day=7, hour=10, tzinfo=UTC),
                room="Hall A",
            ),
            title="Test Session",
            track="Track 1",
            speakers=(Speaker(first_name="", last_name=""),),
            abstract=AbstractMarkdown(content="Some abstract"),
            url="https://example.com",
        )
        builder = YouTubeTitleBuilder()
        title = builder.build(session=session)

        assert str(title) == "Test Session"

    def test_build_multiple_speakers(self) -> None:
        """複数スピーカーの場合"""
        session = Session(
            slot=ScheduleSlot(
                timeslot=datetime(year=2026, month=1, day=7, hour=10, tzinfo=UTC),
                room="Hall A",
            ),
            title="Panel Discussion",
            track="Track 1",
            speakers=(
                Speaker(first_name="John", last_name="Doe"),
                Speaker(first_name="Jane", last_name="Smith"),
                Speaker(first_name="Bob", last_name="Wilson"),
            ),
            abstract=AbstractMarkdown(content="Some abstract"),
            url="https://example.com",
        )
        builder = YouTubeTitleBuilder()
        title = builder.build(session=session)

        assert str(title) == "Panel Discussion - John Doe, Jane Smith, Bob Wilson"

    def test_build_exactly_100_chars(self) -> None:
        """ちょうど100文字の場合"""
        # "X" * 80 + " - " (3) + "John Doe" (8) = 91文字 → 9文字追加で100文字
        title_text = "X" * 89  # 89 + " - " (3) + "John Doe" (8) = 100
        session = Session(
            slot=ScheduleSlot(
                timeslot=datetime(year=2026, month=1, day=7, hour=10, tzinfo=UTC),
                room="Hall A",
            ),
            title=title_text,
            track="Track 1",
            speakers=(Speaker(first_name="John", last_name="Doe"),),
            abstract=AbstractMarkdown(content="Some abstract"),
            url="https://example.com",
        )
        builder = YouTubeTitleBuilder()
        title = builder.build(session=session)

        assert len(str(title)) == YouTubeTitle.MAX_LENGTH
        assert str(title) == f"{title_text} - John Doe"

    def test_build_101_chars_uses_initials(self) -> None:
        """101文字でイニシャル化される"""
        # 90文字のタイトル + " - " (3) + "John Doe" (8) = 101文字
        title_text = "X" * 90
        session = Session(
            slot=ScheduleSlot(
                timeslot=datetime(year=2026, month=1, day=7, hour=10, tzinfo=UTC),
                room="Hall A",
            ),
            title=title_text,
            track="Track 1",
            speakers=(Speaker(first_name="John", last_name="Doe"),),
            abstract=AbstractMarkdown(content="Some abstract"),
            url="https://example.com",
        )
        builder = YouTubeTitleBuilder()
        title = builder.build(session=session)

        # イニシャル表記で収まる: 90 + " - " (3) + "J. Doe" (6) = 99文字
        assert len(str(title)) <= YouTubeTitle.MAX_LENGTH
        assert str(title) == f"{title_text} - J. Doe"

    def test_build_long_title_with_initials_fits(self) -> None:
        """イニシャル表記で収まる場合"""
        # 91文字のタイトル + " - " (3) + "J. Doe" (6) = 100文字
        title_text = "X" * 91
        session = Session(
            slot=ScheduleSlot(
                timeslot=datetime(year=2026, month=1, day=7, hour=10, tzinfo=UTC),
                room="Hall A",
            ),
            title=title_text,
            track="Track 1",
            speakers=(Speaker(first_name="John", last_name="Doe"),),
            abstract=AbstractMarkdown(content="Some abstract"),
            url="https://example.com",
        )
        builder = YouTubeTitleBuilder()
        title = builder.build(session=session)

        assert len(str(title)) == YouTubeTitle.MAX_LENGTH
        assert str(title) == f"{title_text} - J. Doe"

    def test_build_long_title_uses_last_name_only(self) -> None:
        """イニシャル表記でも収まらない場合はラストネームのみ"""
        # 92文字のタイトル + " - " (3) + "J. Doe" (6) = 101文字 → ラストネームのみ
        title_text = "X" * 92
        session = Session(
            slot=ScheduleSlot(
                timeslot=datetime(year=2026, month=1, day=7, hour=10, tzinfo=UTC),
                room="Hall A",
            ),
            title=title_text,
            track="Track 1",
            speakers=(Speaker(first_name="John", last_name="Doe"),),
            abstract=AbstractMarkdown(content="Some abstract"),
            url="https://example.com",
        )
        builder = YouTubeTitleBuilder()
        title = builder.build(session=session)

        # ラストネームのみ: 92 + " - " (3) + "Doe" (3) = 98文字
        assert len(str(title)) <= YouTubeTitle.MAX_LENGTH
        assert str(title) == f"{title_text} - Doe"

    def test_build_long_title_truncates(self) -> None:
        """ラストネームのみでも収まらない場合はタイトルを切り詰め"""
        # 95文字のタイトル + " - " (3) + "Doe" (3) = 101文字
        title_text = "X" * 95
        session = Session(
            slot=ScheduleSlot(
                timeslot=datetime(year=2026, month=1, day=7, hour=10, tzinfo=UTC),
                room="Hall A",
            ),
            title=title_text,
            track="Track 1",
            speakers=(Speaker(first_name="John", last_name="Doe"),),
            abstract=AbstractMarkdown(content="Some abstract"),
            url="https://example.com",
        )
        builder = YouTubeTitleBuilder()
        title = builder.build(session=session)

        assert len(str(title)) == YouTubeTitle.MAX_LENGTH
        # 100 - " - " (3) - "Doe" (3) - "..." (3) = 91文字
        assert str(title) == f"{'X' * 91}... - Doe"

    def test_build_very_long_speaker_is_truncated(self) -> None:
        """ラストネームだけで100文字を超える場合"""
        # ラストネーム101文字 → 100文字に切り詰め
        session = Session(
            slot=ScheduleSlot(
                timeslot=datetime(year=2026, month=1, day=7, hour=10, tzinfo=UTC),
                room="Hall A",
            ),
            title="Short",
            track="Track 1",
            speakers=(Speaker(first_name="V", last_name="W" * 101),),
            abstract=AbstractMarkdown(content="Some abstract"),
            url="https://example.com",
        )
        builder = YouTubeTitleBuilder()
        title = builder.build(session=session)

        assert len(str(title)) == YouTubeTitle.MAX_LENGTH
        # ラストネーム自体が切り詰められる (97文字 + "...")
        assert str(title) == "W" * 97 + "..."

    def test_build_speaker_without_first_name(self) -> None:
        """ファーストネームがないスピーカー"""
        session = Session(
            slot=ScheduleSlot(
                timeslot=datetime(year=2026, month=1, day=7, hour=10, tzinfo=UTC),
                room="Hall A",
            ),
            title="Test Session",
            track="Track 1",
            speakers=(Speaker(first_name="", last_name="Doe"),),
            abstract=AbstractMarkdown(content="Some abstract"),
            url="https://example.com",
        )
        builder = YouTubeTitleBuilder()
        title = builder.build(session=session)

        assert str(title) == "Test Session - Doe"

    def test_build_speaker_without_last_name(self) -> None:
        """ラストネームがないスピーカー"""
        session = Session(
            slot=ScheduleSlot(
                timeslot=datetime(year=2026, month=1, day=7, hour=10, tzinfo=UTC),
                room="Hall A",
            ),
            title="Test Session",
            track="Track 1",
            speakers=(Speaker(first_name="John", last_name=""),),
            abstract=AbstractMarkdown(content="Some abstract"),
            url="https://example.com",
        )
        builder = YouTubeTitleBuilder()
        title = builder.build(session=session)

        assert str(title) == "Test Session - John"

    def test_title_only_truncated_when_long(self) -> None:
        """スピーカーなしで長いタイトルは切り詰められる"""
        long_title = "X" * 150
        session = Session(
            slot=ScheduleSlot(
                timeslot=datetime(year=2026, month=1, day=7, hour=10, tzinfo=UTC),
                room="Hall A",
            ),
            title=long_title,
            track="Track 1",
            speakers=(),
            abstract=AbstractMarkdown(content="Some abstract"),
            url="https://example.com",
        )
        builder = YouTubeTitleBuilder()
        title = builder.build(session=session)

        assert len(str(title)) == YouTubeTitle.MAX_LENGTH
        assert str(title) == "X" * 97 + "..."

    def test_build_multi_word_first_name(self) -> None:
        """複合ファーストネームの場合、各単語がイニシャル化される"""
        session = Session(
            slot=ScheduleSlot(
                timeslot=datetime(year=2026, month=1, day=7, hour=10, tzinfo=UTC),
                room="Hall A",
            ),
            title="Test Session",
            track="Track 1",
            speakers=(Speaker(first_name="Tze Chin", last_name="Tang"),),
            abstract=AbstractMarkdown(content="Some abstract"),
            url="https://example.com",
        )
        builder = YouTubeTitleBuilder()
        title = builder.build(session=session)

        # フルネームで収まる場合はフルネーム
        assert str(title) == "Test Session - Tze Chin Tang"

    def test_build_multi_word_first_name_uses_initials(self) -> None:
        """複合ファーストネームでイニシャル化が必要な場合"""
        # 85文字のタイトル + " - " (3) + "Tze Chin Tang" (13) = 101文字 → イニシャル化
        title_text = "X" * 85
        session = Session(
            slot=ScheduleSlot(
                timeslot=datetime(year=2026, month=1, day=7, hour=10, tzinfo=UTC),
                room="Hall A",
            ),
            title=title_text,
            track="Track 1",
            speakers=(Speaker(first_name="Tze Chin", last_name="Tang"),),
            abstract=AbstractMarkdown(content="Some abstract"),
            url="https://example.com",
        )
        builder = YouTubeTitleBuilder()
        title = builder.build(session=session)

        # イニシャル表記: 85 + " - " (3) + "T. C. Tang" (10) = 98文字
        assert len(str(title)) <= YouTubeTitle.MAX_LENGTH
        assert str(title) == f"{title_text} - T. C. Tang"
