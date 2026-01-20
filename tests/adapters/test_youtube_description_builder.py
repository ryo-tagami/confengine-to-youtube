"""YouTube動画説明文ビルダーのテスト"""

from datetime import UTC, datetime

import pytest

from confengine_to_youtube.adapters.youtube_description_builder import (
    YouTubeDescriptionBuilder,
)
from confengine_to_youtube.domain.abstract_markdown import AbstractMarkdown
from confengine_to_youtube.domain.schedule_slot import ScheduleSlot
from confengine_to_youtube.domain.session import Session, Speaker
from confengine_to_youtube.domain.youtube_description import YouTubeDescription


class TestYouTubeDescriptionBuilder:
    """YouTubeDescriptionBuilder のテスト"""

    def test_build_basic(self, sample_session: Session) -> None:
        """基本的なMarkdown生成"""
        builder = YouTubeDescriptionBuilder()
        markdown = builder.build(session=sample_session, hashtags=(), footer="")

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
        assert str(markdown) == expected

    def test_build_with_hashtags(self, sample_session: Session) -> None:
        """ハッシュタグ付きのMarkdown生成"""
        builder = YouTubeDescriptionBuilder()
        markdown = builder.build(
            session=sample_session, hashtags=("#Test", "#Hash"), footer=""
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
        assert str(markdown) == expected

    def test_build_with_footer(self, sample_session: Session) -> None:
        """フッター付きのMarkdown生成"""
        builder = YouTubeDescriptionBuilder()
        markdown = builder.build(
            session=sample_session, hashtags=(), footer="Footer text here"
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
        assert str(markdown) == expected

    def test_build_without_speakers(self, empty_session: Session) -> None:
        """スピーカーがいない場合"""
        builder = YouTubeDescriptionBuilder()
        markdown = builder.build(session=empty_session, hashtags=(), footer="")

        expected = "***\n\nhttps://example.com/session/2\n\n***"
        assert str(markdown) == expected

    def test_build_without_abstract(self) -> None:
        """abstractが空の場合"""
        session = Session(
            slot=ScheduleSlot(
                timeslot=datetime(year=2026, month=1, day=7, hour=10, tzinfo=UTC),
                room="Hall A",
            ),
            title="Test Title",
            track="Track 1",
            speakers=[Speaker(first_name="Speaker", last_name="A")],
            abstract=AbstractMarkdown(content=""),
            url="https://example.com",
        )
        builder = YouTubeDescriptionBuilder()
        markdown = builder.build(session=session, hashtags=(), footer="")

        expected = "Speaker: Speaker A\n\n***\n\nhttps://example.com\n\n***"
        assert str(markdown) == expected

    def test_build_without_url(self) -> None:
        """URLが空の場合"""
        session = Session(
            slot=ScheduleSlot(
                timeslot=datetime(year=2026, month=1, day=7, hour=10, tzinfo=UTC),
                room="Hall A",
            ),
            title="Test Title",
            track="Track 1",
            speakers=[Speaker(first_name="Speaker", last_name="A")],
            abstract=AbstractMarkdown(content="Some abstract"),
            url="",
        )
        builder = YouTubeDescriptionBuilder()
        markdown = builder.build(session=session, hashtags=(), footer="")

        expected = "Speaker: Speaker A\n\nSome abstract\n\n***\n\n***"
        assert str(markdown) == expected

    def test_frame_exceeds_max_length_raises_error(self) -> None:
        """フレーム部分だけで文字数制限を超える場合はValueErrorを発生"""
        session = Session(
            slot=ScheduleSlot(
                timeslot=datetime(year=2026, month=1, day=7, hour=10, tzinfo=UTC),
                room="Hall A",
            ),
            title="Title",
            track="Track 1",
            speakers=[Speaker(first_name="", last_name="Speaker")],
            abstract=AbstractMarkdown(content="Short"),
            url="https://example.com",
        )
        # 5000文字を超えるフッターを用意
        long_footer = "X" * 6000
        builder = YouTubeDescriptionBuilder()

        expected_msg = "フレーム部分だけで文字数制限を超えています"
        with pytest.raises(expected_exception=ValueError, match=expected_msg):
            builder.build(session=session, hashtags=(), footer=long_footer)

    def test_long_abstract_is_truncated(self) -> None:
        """長いabstractはYouTube説明文の最大文字数に収まるよう切り詰められる"""
        # 5000文字を超えるabstractを用意
        long_abstract = "A" * 6000
        session = Session(
            slot=ScheduleSlot(
                timeslot=datetime(year=2026, month=1, day=7, hour=10, tzinfo=UTC),
                room="Hall A",
            ),
            title="Title",
            track="Track 1",
            speakers=[Speaker(first_name="", last_name="Speaker")],
            abstract=AbstractMarkdown(content=long_abstract),
            url="https://example.com",
        )
        builder = YouTubeDescriptionBuilder()
        markdown = builder.build(session=session, hashtags=(), footer="Footer")

        result = str(markdown)
        # 最大文字数以下に収まる
        assert len(result) <= YouTubeDescription.MAX_LENGTH
        # 先頭部分を確認 (Speaker、Abstractの先頭)
        assert result.startswith("Speaker: Speaker\n\nA")
        # 末尾部分を確認 (切り詰めマーカー、URL、Footer)
        assert result.endswith("...\n\n***\n\nhttps://example.com\n\n***\n\nFooter")

    def test_sanitize_removes_angle_brackets_from_urls(self) -> None:
        """Markdownオートリンク記法 <URL> を URL に変換する"""
        session = Session(
            slot=ScheduleSlot(
                timeslot=datetime(year=2026, month=1, day=7, hour=10, tzinfo=UTC),
                room="Hall A",
            ),
            title="Test",
            track="Track 1",
            speakers=[Speaker(first_name="", last_name="Speaker")],
            abstract=AbstractMarkdown(content="Link: <https://example.com/page>"),
            url="",
        )
        builder = YouTubeDescriptionBuilder()
        markdown = builder.build(session=session, hashtags=(), footer="")

        expected = "Speaker: Speaker\n\nLink: https://example.com/page\n\n***\n\n***"
        assert str(markdown) == expected

    def test_sanitize_handles_multiple_autolinks(self) -> None:
        """複数のオートリンクを処理"""
        session = Session(
            slot=ScheduleSlot(
                timeslot=datetime(year=2026, month=1, day=7, hour=10, tzinfo=UTC),
                room="Hall A",
            ),
            title="Test",
            track="Track 1",
            speakers=[Speaker(first_name="", last_name="Speaker")],
            abstract=AbstractMarkdown(content="See <https://a.com> and <http://b.com>"),
            url="",
        )
        builder = YouTubeDescriptionBuilder()
        markdown = builder.build(session=session, hashtags=(), footer="")

        expected = (
            "Speaker: Speaker\n\nSee https://a.com and http://b.com\n\n***\n\n***"
        )
        assert str(markdown) == expected

    def test_sanitize_replaces_non_url_angle_brackets(self) -> None:
        """非URLの山括弧をUnicode引用符に置換する

        YouTubeは < > を許可しないため、URLパターン以外の山括弧は
        U+2039 と U+203A に置換する。
        """
        session = Session(
            slot=ScheduleSlot(
                timeslot=datetime(year=2026, month=1, day=7, hour=10, tzinfo=UTC),
                room="Hall A",
            ),
            title="Test",
            track="Track 1",
            speakers=[Speaker(first_name="", last_name="Speaker")],
            abstract=AbstractMarkdown(content="> Quote\na < b\nList<T>"),
            url="",
        )
        builder = YouTubeDescriptionBuilder()
        markdown = builder.build(session=session, hashtags=(), footer="")

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
        assert str(markdown) == expected
