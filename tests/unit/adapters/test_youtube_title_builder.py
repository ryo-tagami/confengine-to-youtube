"""YouTube動画タイトルビルダーのテスト"""

from datetime import UTC, datetime

import pytest

from confengine_to_youtube.adapters.youtube_title_builder import YouTubeTitleBuilder
from confengine_to_youtube.domain.session import Session
from confengine_to_youtube.domain.youtube_title import YouTubeTitle
from tests.conftest import create_session

TIMESLOT = datetime(year=2026, month=1, day=7, hour=10, tzinfo=UTC)
ROOM = "Hall A"
ABSTRACT = "Some abstract"
URL = "https://example.com"


class TestYouTubeTitleBuilder:
    """YouTubeTitleBuilder のテスト"""

    def test_build_basic(
        self,
        sample_session: Session,
        title_builder: YouTubeTitleBuilder,
    ) -> None:
        """基本的なタイトル生成"""
        title = title_builder.build(session=sample_session)

        assert str(title) == "Sample Session - Speaker A, Speaker B"

    def test_build_single_speaker(self, title_builder: YouTubeTitleBuilder) -> None:
        """単一スピーカーの場合"""
        session = create_session(
            title="Test Session",
            speakers=[("John", "Doe")],
            abstract=ABSTRACT,
            timeslot=TIMESLOT,
            room=ROOM,
            url=URL,
        )
        title = title_builder.build(session=session)

        assert str(title) == "Test Session - John Doe"

    def test_build_no_speakers(
        self,
        empty_session: Session,
        title_builder: YouTubeTitleBuilder,
    ) -> None:
        """スピーカーがいない場合"""
        title = title_builder.build(session=empty_session)

        assert str(title) == "Empty Session"

    def test_build_speakers_with_empty_names(
        self,
        title_builder: YouTubeTitleBuilder,
    ) -> None:
        """全スピーカーが空の名前の場合はタイトルのみ"""
        session = create_session(
            title="Test Session",
            speakers=[("", "")],
            abstract=ABSTRACT,
            timeslot=TIMESLOT,
            room=ROOM,
            url=URL,
        )
        title = title_builder.build(session=session)

        assert str(title) == "Test Session"

    def test_build_multiple_speakers(self, title_builder: YouTubeTitleBuilder) -> None:
        """複数スピーカーの場合"""
        session = create_session(
            title="Panel Discussion",
            speakers=[("John", "Doe"), ("Jane", "Smith"), ("Bob", "Wilson")],
            abstract=ABSTRACT,
            timeslot=TIMESLOT,
            room=ROOM,
            url=URL,
        )
        title = title_builder.build(session=session)

        assert str(title) == "Panel Discussion - John Doe, Jane Smith, Bob Wilson"

    @pytest.mark.parametrize(
        ("title_length", "expected_str"),
        [
            # 89文字: ちょうど100文字に収まる → フルネーム
            (89, "X" * 89 + " - John Doe"),
            # 90文字: 101文字になる → イニシャル化 (99文字)
            (90, "X" * 90 + " - J. Doe"),
            # 91文字: イニシャルでちょうど100文字
            (91, "X" * 91 + " - J. Doe"),
            # 92文字: イニシャルでも101文字 → ラストネームのみ (98文字)
            (92, "X" * 92 + " - Doe"),
            # 95文字: ラストネームでも101文字 → タイトル切り詰め (100文字)
            (95, "X" * 91 + "... - Doe"),
        ],
        ids=[
            "exactly_100_chars_fullname",
            "101_chars_uses_initials",
            "initials_fits_exactly_100",
            "last_name_only",
            "title_truncated",
        ],
    )
    def test_build_title_length_boundaries(
        self,
        title_builder: YouTubeTitleBuilder,
        title_length: int,
        expected_str: str,
    ) -> None:
        """タイトル長の境界値テスト

        100文字制限に対して、スピーカー名の表示形式が段階的に変化する:
        1. フルネーム (John Doe)
        2. イニシャル (J. Doe)
        3. ラストネームのみ (Doe)
        4. タイトル切り詰め (XXX... - Doe)
        """
        session = create_session(
            title="X" * title_length,
            speakers=[("John", "Doe")],
            abstract=ABSTRACT,
            timeslot=TIMESLOT,
            room=ROOM,
            url=URL,
        )
        title = title_builder.build(session=session)

        assert len(str(title)) <= YouTubeTitle.MAX_LENGTH
        assert str(title) == expected_str

    def test_build_very_long_speaker_is_truncated(
        self,
        title_builder: YouTubeTitleBuilder,
    ) -> None:
        """ラストネームだけで100文字を超える場合"""
        # ラストネーム101文字 → 100文字に切り詰め
        session = create_session(
            title="Short",
            speakers=[("V", "W" * 101)],
            abstract=ABSTRACT,
            timeslot=TIMESLOT,
            room=ROOM,
            url=URL,
        )
        title = title_builder.build(session=session)

        assert len(str(title)) == YouTubeTitle.MAX_LENGTH
        # ラストネーム自体が切り詰められる (97文字 + "...")
        assert str(title) == "W" * 97 + "..."

    def test_build_speaker_without_first_name(
        self,
        title_builder: YouTubeTitleBuilder,
    ) -> None:
        """ファーストネームがないスピーカー"""
        session = create_session(
            title="Test Session",
            speakers=[("", "Doe")],
            abstract=ABSTRACT,
            timeslot=TIMESLOT,
            room=ROOM,
            url=URL,
        )
        title = title_builder.build(session=session)

        assert str(title) == "Test Session - Doe"

    def test_build_speaker_without_last_name(
        self,
        title_builder: YouTubeTitleBuilder,
    ) -> None:
        """ラストネームがないスピーカー"""
        session = create_session(
            title="Test Session",
            speakers=[("John", "")],
            abstract=ABSTRACT,
            timeslot=TIMESLOT,
            room=ROOM,
            url=URL,
        )
        title = title_builder.build(session=session)

        assert str(title) == "Test Session - John"

    def test_title_only_truncated_when_long(
        self,
        title_builder: YouTubeTitleBuilder,
    ) -> None:
        """スピーカーなしで長いタイトルは切り詰められる"""
        long_title = "X" * 150
        session = create_session(
            title=long_title,
            speakers=[],
            abstract=ABSTRACT,
            timeslot=TIMESLOT,
            room=ROOM,
            url=URL,
        )
        title = title_builder.build(session=session)

        assert len(str(title)) == YouTubeTitle.MAX_LENGTH
        assert str(title) == "X" * 97 + "..."

    def test_build_multi_word_first_name(
        self,
        title_builder: YouTubeTitleBuilder,
    ) -> None:
        """複合ファーストネームの場合、各単語がイニシャル化される"""
        session = create_session(
            title="Test Session",
            speakers=[("Tze Chin", "Tang")],
            abstract=ABSTRACT,
            timeslot=TIMESLOT,
            room=ROOM,
            url=URL,
        )
        title = title_builder.build(session=session)

        # フルネームで収まる場合はフルネーム
        assert str(title) == "Test Session - Tze Chin Tang"

    def test_build_multi_word_first_name_uses_initials(
        self,
        title_builder: YouTubeTitleBuilder,
    ) -> None:
        """複合ファーストネームでイニシャル化が必要な場合"""
        # 85文字のタイトル + " - " (3) + "Tze Chin Tang" (13) = 101文字 → イニシャル化
        title_text = "X" * 85
        session = create_session(
            title=title_text,
            speakers=[("Tze Chin", "Tang")],
            abstract=ABSTRACT,
            timeslot=TIMESLOT,
            room=ROOM,
            url=URL,
        )
        title = title_builder.build(session=session)

        # イニシャル表記: 85 + " - " (3) + "T. C. Tang" (10) = 98文字
        assert len(str(title)) <= YouTubeTitle.MAX_LENGTH
        assert str(title) == f"{title_text} - T. C. Tang"
