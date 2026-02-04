"""YouTubeContentGenerator ドメインサービスのテスト"""

from datetime import UTC, datetime

import pytest
from returns.result import Failure, Success

from confengine_to_youtube.domain.errors import FrameOverflowError
from confengine_to_youtube.domain.session import Session
from confengine_to_youtube.domain.youtube_content_generator import (
    YouTubeContentGenerator,
)
from confengine_to_youtube.domain.youtube_description import YouTubeDescription
from confengine_to_youtube.domain.youtube_title import YouTubeTitle
from tests.conftest import create_session

TIMESLOT = datetime(year=2026, month=1, day=7, hour=10, tzinfo=UTC)
ROOM = "Hall A"
ABSTRACT = "Some abstract"
URL = "https://example.com"


class TestGenerateTitle:
    """YouTubeContentGenerator.generate_title のテスト"""

    def test_basic(self, sample_session: Session) -> None:
        """基本的なタイトル生成"""
        result = YouTubeContentGenerator.generate_title(session=sample_session)

        assert isinstance(result, Success)
        assert str(result.unwrap()) == "Sample Session - Speaker A, Speaker B"

    def test_single_speaker(self) -> None:
        """単一スピーカーの場合"""
        session = create_session(
            title="Test Session",
            speakers=[("John", "Doe")],
            abstract=ABSTRACT,
            timeslot=TIMESLOT,
            room=ROOM,
            url=URL,
        )
        result = YouTubeContentGenerator.generate_title(session=session)

        assert isinstance(result, Success)
        assert str(result.unwrap()) == "Test Session - John Doe"

    def test_no_speakers(self, empty_session: Session) -> None:
        """スピーカーがいない場合"""
        result = YouTubeContentGenerator.generate_title(session=empty_session)

        assert isinstance(result, Success)
        assert str(result.unwrap()) == "Empty Session"

    def test_speakers_with_empty_names(self) -> None:
        """全スピーカーが空の名前の場合はタイトルのみ"""
        session = create_session(
            title="Test Session",
            speakers=[("", "")],
            abstract=ABSTRACT,
            timeslot=TIMESLOT,
            room=ROOM,
            url=URL,
        )
        result = YouTubeContentGenerator.generate_title(session=session)

        assert isinstance(result, Success)
        assert str(result.unwrap()) == "Test Session"

    def test_multiple_speakers(self) -> None:
        """複数スピーカーの場合"""
        session = create_session(
            title="Panel Discussion",
            speakers=[("John", "Doe"), ("Jane", "Smith"), ("Bob", "Wilson")],
            abstract=ABSTRACT,
            timeslot=TIMESLOT,
            room=ROOM,
            url=URL,
        )
        result = YouTubeContentGenerator.generate_title(session=session)

        assert isinstance(result, Success)
        title = result.unwrap()
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
    def test_title_length_boundaries(
        self,
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
        result = YouTubeContentGenerator.generate_title(session=session)

        assert isinstance(result, Success)
        title = result.unwrap()
        assert len(str(title)) <= YouTubeTitle.MAX_LENGTH
        assert str(title) == expected_str

    def test_very_long_speaker_is_truncated(self) -> None:
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
        result = YouTubeContentGenerator.generate_title(session=session)

        assert isinstance(result, Success)
        title = result.unwrap()
        assert len(str(title)) == YouTubeTitle.MAX_LENGTH
        # ラストネーム自体が切り詰められる (97文字 + "...")
        assert str(title) == "W" * 97 + "..."

    @pytest.mark.parametrize(
        ("last_name_length", "expected_str"),
        [
            # available == 0: reserved = 3(" - ") + 94 + 3("...") = 100
            # → スピーカー名のみ返す (94文字)
            (94, "W" * 94),
            # available == 1: reserved = 3(" - ") + 93 + 3("...") = 99
            # → タイトル1文字 + "..." + " - " + スピーカー名 (100文字)
            (93, "X..." + " - " + "W" * 93),
        ],
        ids=[
            "available_zero_returns_speaker_only",
            "available_one_truncates_title",
        ],
    )
    def test_truncation_available_boundary(
        self,
        last_name_length: int,
        expected_str: str,
    ) -> None:
        """_truncate_title_keeping_speaker の available 境界値テスト

        タイトルが長くスピーカーのラストネームも長い場合、
        available (タイトルに使える文字数) の境界で動作が変わる:
        - available == 0: スピーカー名のみ返す
        - available == 1: タイトル1文字+省略記号+スピーカー名
        """
        session = create_session(
            title="X" * 10,
            speakers=[("V", "W" * last_name_length)],
            abstract=ABSTRACT,
            timeslot=TIMESLOT,
            room=ROOM,
            url=URL,
        )
        result = YouTubeContentGenerator.generate_title(session=session)

        assert isinstance(result, Success)
        title = result.unwrap()
        assert len(str(title)) <= YouTubeTitle.MAX_LENGTH
        assert str(title) == expected_str

    def test_speaker_without_first_name(self) -> None:
        """ファーストネームがないスピーカー"""
        session = create_session(
            title="Test Session",
            speakers=[("", "Doe")],
            abstract=ABSTRACT,
            timeslot=TIMESLOT,
            room=ROOM,
            url=URL,
        )
        result = YouTubeContentGenerator.generate_title(session=session)

        assert isinstance(result, Success)
        assert str(result.unwrap()) == "Test Session - Doe"

    def test_speaker_without_last_name(self) -> None:
        """ラストネームがないスピーカー"""
        session = create_session(
            title="Test Session",
            speakers=[("John", "")],
            abstract=ABSTRACT,
            timeslot=TIMESLOT,
            room=ROOM,
            url=URL,
        )
        result = YouTubeContentGenerator.generate_title(session=session)

        assert isinstance(result, Success)
        assert str(result.unwrap()) == "Test Session - John"

    def test_speaker_without_last_name_and_long_title(self) -> None:
        """ラストネームがなく、イニシャルでも収まらない長いタイトルの場合

        last_name が空の場合、speakers_last_name も空になるため、
        タイトル切り詰め時にスピーカー名を維持できない。
        この場合はタイトルのみを返す。
        """
        # 97文字のタイトル + " - J." (5文字) = 102文字 → イニシャルでも収まらない
        session = create_session(
            title="X" * 97,
            speakers=[("John", "")],
            abstract=ABSTRACT,
            timeslot=TIMESLOT,
            room=ROOM,
            url=URL,
        )
        result = YouTubeContentGenerator.generate_title(session=session)

        assert isinstance(result, Success)
        title = result.unwrap()
        # speakers_last_name が空なのでタイトルのみを返す (97文字なので切り詰めなし)
        assert str(title) == "X" * 97

    def test_title_only_truncated_when_long(self) -> None:
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
        result = YouTubeContentGenerator.generate_title(session=session)

        assert isinstance(result, Success)
        title = result.unwrap()
        assert len(str(title)) == YouTubeTitle.MAX_LENGTH
        assert str(title) == "X" * 97 + "..."

    def test_title_exactly_max_length_no_speakers(self) -> None:
        """タイトルがちょうど最大長でスピーカーなしの場合、切り詰めなし"""
        session = create_session(
            title="X" * YouTubeTitle.MAX_LENGTH,
            speakers=[],
            abstract=ABSTRACT,
            timeslot=TIMESLOT,
            room=ROOM,
            url=URL,
        )
        result = YouTubeContentGenerator.generate_title(session=session)

        assert isinstance(result, Success)
        assert str(result.unwrap()) == "X" * YouTubeTitle.MAX_LENGTH

    def test_multi_word_first_name(self) -> None:
        """複合ファーストネームの場合、各単語がイニシャル化される"""
        session = create_session(
            title="Test Session",
            speakers=[("Tze Chin", "Tang")],
            abstract=ABSTRACT,
            timeslot=TIMESLOT,
            room=ROOM,
            url=URL,
        )
        result = YouTubeContentGenerator.generate_title(session=session)

        assert isinstance(result, Success)
        # フルネームで収まる場合はフルネーム
        assert str(result.unwrap()) == "Test Session - Tze Chin Tang"

    def test_multi_word_first_name_uses_initials(self) -> None:
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
        result = YouTubeContentGenerator.generate_title(session=session)

        assert isinstance(result, Success)
        title = result.unwrap()
        # イニシャル表記: 85 + " - " (3) + "T. C. Tang" (10) = 98文字
        assert len(str(title)) <= YouTubeTitle.MAX_LENGTH
        assert str(title) == f"{title_text} - T. C. Tang"


class TestGenerateDescription:
    """YouTubeContentGenerator.generate_description のテスト"""

    def test_basic(self, sample_session: Session) -> None:
        """基本的なMarkdown生成"""
        result = YouTubeContentGenerator.generate_description(
            session=sample_session,
            hashtags=(),
            footer="",
        )

        assert isinstance(result, Success)
        description = result.unwrap()
        expected = (
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
        assert str(description) == expected

    def test_with_hashtags(self, sample_session: Session) -> None:
        """ハッシュタグ付きのMarkdown生成"""
        result = YouTubeContentGenerator.generate_description(
            session=sample_session,
            hashtags=("#Test", "#Hash"),
            footer="",
        )

        assert isinstance(result, Success)
        description = result.unwrap()
        expected = (
            "Speaker: Speaker A, Speaker B\n"
            "\n"
            "This is a sample abstract.\n"
            "\n"
            "***\n"
            "\n"
            "https://example.com/session/1\n"
            "\n"
            "#Test #Hash\n"
            "\n"
            "***"
        )
        assert str(description) == expected

    def test_with_footer(self, sample_session: Session) -> None:
        """フッター付きのMarkdown生成"""
        result = YouTubeContentGenerator.generate_description(
            session=sample_session,
            hashtags=(),
            footer="Footer text here",
        )

        assert isinstance(result, Success)
        description = result.unwrap()
        expected = (
            "Speaker: Speaker A, Speaker B\n"
            "\n"
            "This is a sample abstract.\n"
            "\n"
            "***\n"
            "\n"
            "https://example.com/session/1\n"
            "\n"
            "***\n"
            "\n"
            "Footer text here"
        )
        assert str(description) == expected

    def test_without_speakers(self, empty_session: Session) -> None:
        """スピーカーがいない場合"""
        result = YouTubeContentGenerator.generate_description(
            session=empty_session,
            hashtags=(),
            footer="",
        )

        assert isinstance(result, Success)
        description = result.unwrap()
        expected = "***\n\nhttps://example.com/session/2\n\n***"
        assert str(description) == expected

    def test_without_abstract(self) -> None:
        """abstractが空の場合"""
        session = create_session(
            title="Test Title",
            speakers=[("Speaker", "A")],
            abstract="",
            timeslot=TIMESLOT,
            room=ROOM,
            url=URL,
        )
        result = YouTubeContentGenerator.generate_description(
            session=session,
            hashtags=(),
            footer="",
        )

        assert isinstance(result, Success)
        description = result.unwrap()
        expected = "Speaker: Speaker A\n\n***\n\nhttps://example.com\n\n***"
        assert str(description) == expected

    def test_without_url(self) -> None:
        """URLが空の場合"""
        session = create_session(
            title="Test Title",
            speakers=[("Speaker", "A")],
            abstract="Some abstract",
            timeslot=TIMESLOT,
            room=ROOM,
            url="",
        )
        result = YouTubeContentGenerator.generate_description(
            session=session,
            hashtags=(),
            footer="",
        )

        assert isinstance(result, Success)
        description = result.unwrap()
        expected = "Speaker: Speaker A\n\nSome abstract\n\n***\n\n***"
        assert str(description) == expected

    def test_frame_exceeds_max_length_returns_failure(self) -> None:
        """フレーム部分だけで文字数制限を超える場合は Failure(FrameOverflowError)"""
        session = create_session(
            title="Title",
            speakers=[("", "Speaker")],
            abstract="Short",
            timeslot=TIMESLOT,
            room=ROOM,
            url=URL,
        )

        # 5000文字を超えるフッターを用意
        result = YouTubeContentGenerator.generate_description(
            session=session,
            hashtags=(),
            footer="X" * 6000,
        )

        assert isinstance(result, Failure)
        error = result.failure()
        assert isinstance(error, FrameOverflowError)
        assert error.frame_length > YouTubeDescription.MAX_LENGTH

    def test_long_abstract_is_truncated(self) -> None:
        """長いabstractはYouTube説明文の最大文字数に収まるよう切り詰められる"""
        # 5000文字を超えるabstractを用意
        long_abstract = "A" * 6000
        session = create_session(
            title="Title",
            speakers=[("", "Speaker")],
            abstract=long_abstract,
            timeslot=TIMESLOT,
            room=ROOM,
            url=URL,
        )
        result = YouTubeContentGenerator.generate_description(
            session=session,
            hashtags=(),
            footer="Footer",
        )

        assert isinstance(result, Success)
        description = result.unwrap()
        description_str = str(description)
        # 最大文字数以下に収まる
        assert len(description_str) <= YouTubeDescription.MAX_LENGTH
        # 先頭部分を確認 (Speaker、Abstractの先頭)
        assert description_str.startswith("Speaker: Speaker\n\nA")
        # 末尾部分を確認 (切り詰めマーカー、URL、Footer)
        assert description_str.endswith(
            "...\n\n***\n\nhttps://example.com\n\n***\n\nFooter"
        )

    def test_sanitize_removes_angle_brackets_from_urls(self) -> None:
        """Markdownオートリンク記法 <URL> を URL に変換する"""
        session = create_session(
            title="Test",
            speakers=[("", "Speaker")],
            abstract="Link: <https://example.com/page>",
            timeslot=TIMESLOT,
            room=ROOM,
            url="",
        )
        result = YouTubeContentGenerator.generate_description(
            session=session,
            hashtags=(),
            footer="",
        )

        assert isinstance(result, Success)
        description = result.unwrap()
        expected = "Speaker: Speaker\n\nLink: https://example.com/page\n\n***\n\n***"
        assert str(description) == expected

    def test_sanitize_handles_multiple_autolinks(self) -> None:
        """複数のオートリンクを処理"""
        session = create_session(
            title="Test",
            speakers=[("", "Speaker")],
            abstract="See <https://a.com> and <http://b.com>",
            timeslot=TIMESLOT,
            room=ROOM,
            url="",
        )
        result = YouTubeContentGenerator.generate_description(
            session=session,
            hashtags=(),
            footer="",
        )

        assert isinstance(result, Success)
        description = result.unwrap()
        expected = (
            "Speaker: Speaker\n\nSee https://a.com and http://b.com\n\n***\n\n***"
        )
        assert str(description) == expected

    def test_sanitize_replaces_non_url_angle_brackets(self) -> None:
        """非URLの山括弧をUnicode引用符に置換する

        YouTubeは < > を許可しないため、URLパターン以外の山括弧は
        U+2039 と U+203A に置換する。
        """
        session = create_session(
            title="Test",
            speakers=[("", "Speaker")],
            abstract="> Quote\na < b\nList<T>",
            timeslot=TIMESLOT,
            room=ROOM,
            url="",
        )
        result = YouTubeContentGenerator.generate_description(
            session=session,
            hashtags=(),
            footer="",
        )

        assert isinstance(result, Success)
        description = result.unwrap()
        # > is replaced with U+203A, < is replaced with U+2039
        expected = (
            "Speaker: Speaker\n"
            "\n"
            "\u203a Quote\n"
            "a \u2039 b\n"
            "List\u2039T\u203a\n"
            "\n"
            "***\n"
            "\n"
            "***"
        )
        assert str(description) == expected
