"""YouTube動画説明文ビルダーのテスト"""

from datetime import UTC, datetime

from returns.result import Failure, Success

from confengine_to_youtube.adapters.youtube_description_builder import (
    YouTubeDescriptionBuilder,
)
from confengine_to_youtube.domain.session import Session
from confengine_to_youtube.domain.youtube_description import YouTubeDescription
from tests.conftest import create_session

TIMESLOT = datetime(year=2026, month=1, day=7, hour=10, tzinfo=UTC)
ROOM = "Hall A"
URL = "https://example.com"


class TestYouTubeDescriptionBuilder:
    """YouTubeDescriptionBuilder のテスト"""

    def test_build_basic(
        self,
        sample_session: Session,
        description_builder: YouTubeDescriptionBuilder,
    ) -> None:
        """基本的なMarkdown生成"""
        result = description_builder.build(
            session=sample_session,
            hashtags=(),
            footer="",
        )

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
        assert isinstance(result, Success)
        assert str(result.unwrap()) == expected

    def test_build_with_hashtags(
        self,
        sample_session: Session,
        description_builder: YouTubeDescriptionBuilder,
    ) -> None:
        """ハッシュタグ付きのMarkdown生成"""
        result = description_builder.build(
            session=sample_session,
            hashtags=("#Test", "#Hash"),
            footer="",
        )

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
        assert isinstance(result, Success)
        assert str(result.unwrap()) == expected

    def test_build_with_footer(
        self,
        sample_session: Session,
        description_builder: YouTubeDescriptionBuilder,
    ) -> None:
        """フッター付きのMarkdown生成"""
        result = description_builder.build(
            session=sample_session,
            hashtags=(),
            footer="Footer text here",
        )

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
        assert isinstance(result, Success)
        assert str(result.unwrap()) == expected

    def test_build_without_speakers(
        self,
        empty_session: Session,
        description_builder: YouTubeDescriptionBuilder,
    ) -> None:
        """スピーカーがいない場合"""
        result = description_builder.build(
            session=empty_session,
            hashtags=(),
            footer="",
        )

        expected = "***\n\nhttps://example.com/session/2\n\n***"
        assert isinstance(result, Success)
        assert str(result.unwrap()) == expected

    def test_build_without_abstract(
        self,
        description_builder: YouTubeDescriptionBuilder,
    ) -> None:
        """abstractが空の場合"""
        session = create_session(
            title="Test Title",
            speakers=[("Speaker", "A")],
            abstract="",
            timeslot=TIMESLOT,
            room=ROOM,
            url=URL,
        )
        result = description_builder.build(session=session, hashtags=(), footer="")

        expected = "Speaker: Speaker A\n\n***\n\nhttps://example.com\n\n***"
        assert isinstance(result, Success)
        assert str(result.unwrap()) == expected

    def test_build_without_url(
        self,
        description_builder: YouTubeDescriptionBuilder,
    ) -> None:
        """URLが空の場合"""
        session = create_session(
            title="Test Title",
            speakers=[("Speaker", "A")],
            abstract="Some abstract",
            timeslot=TIMESLOT,
            room=ROOM,
            url="",
        )
        result = description_builder.build(session=session, hashtags=(), footer="")

        expected = "Speaker: Speaker A\n\nSome abstract\n\n***\n\n***"
        assert isinstance(result, Success)
        assert str(result.unwrap()) == expected

    def test_frame_exceeds_max_length_returns_failure(
        self,
        description_builder: YouTubeDescriptionBuilder,
    ) -> None:
        """フレーム部分だけで文字数制限を超える場合はFailureを返す"""
        session = create_session(
            title="Title",
            speakers=[("", "Speaker")],
            abstract="Short",
            timeslot=TIMESLOT,
            room=ROOM,
            url=URL,
        )
        # 5000文字を超えるフッターを用意
        long_footer = "X" * 6000

        result = description_builder.build(
            session=session,
            hashtags=(),
            footer=long_footer,
        )

        assert isinstance(result, Failure)
        assert result.failure().message.startswith(
            "フレーム部分だけで文字数制限を超えています",
        )

    def test_long_abstract_is_truncated(
        self,
        description_builder: YouTubeDescriptionBuilder,
    ) -> None:
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
        result = description_builder.build(
            session=session,
            hashtags=(),
            footer="Footer",
        )

        assert isinstance(result, Success)
        markdown = str(result.unwrap())
        # 最大文字数以下に収まる
        assert len(markdown) <= YouTubeDescription.MAX_LENGTH
        # 先頭部分を確認 (Speaker、Abstractの先頭)
        assert markdown.startswith("Speaker: Speaker\n\nA")
        # 末尾部分を確認 (切り詰めマーカー、URL、Footer)
        assert markdown.endswith("...\n\n***\n\nhttps://example.com\n\n***\n\nFooter")

    def test_sanitize_removes_angle_brackets_from_urls(
        self,
        description_builder: YouTubeDescriptionBuilder,
    ) -> None:
        """Markdownオートリンク記法 <URL> を URL に変換する"""
        session = create_session(
            title="Test",
            speakers=[("", "Speaker")],
            abstract="Link: <https://example.com/page>",
            timeslot=TIMESLOT,
            room=ROOM,
            url="",
        )
        result = description_builder.build(session=session, hashtags=(), footer="")

        expected = "Speaker: Speaker\n\nLink: https://example.com/page\n\n***\n\n***"
        assert isinstance(result, Success)
        assert str(result.unwrap()) == expected

    def test_sanitize_handles_multiple_autolinks(
        self,
        description_builder: YouTubeDescriptionBuilder,
    ) -> None:
        """複数のオートリンクを処理"""
        session = create_session(
            title="Test",
            speakers=[("", "Speaker")],
            abstract="See <https://a.com> and <http://b.com>",
            timeslot=TIMESLOT,
            room=ROOM,
            url="",
        )
        result = description_builder.build(session=session, hashtags=(), footer="")

        expected = (
            "Speaker: Speaker\n\nSee https://a.com and http://b.com\n\n***\n\n***"
        )
        assert isinstance(result, Success)
        assert str(result.unwrap()) == expected

    def test_sanitize_replaces_non_url_angle_brackets(
        self,
        description_builder: YouTubeDescriptionBuilder,
    ) -> None:
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
        result = description_builder.build(session=session, hashtags=(), footer="")

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
        assert isinstance(result, Success)
        assert str(result.unwrap()) == expected
