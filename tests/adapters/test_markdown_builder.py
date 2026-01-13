"""Markdown ビルダーのテスト"""

from datetime import UTC, datetime

from confengine_exporter.adapters.markdown_builder import (
    MarkdownOptions,
    SessionMarkdownBuilder,
)
from confengine_exporter.domain.session import Session


class TestSessionMarkdownBuilder:
    """SessionMarkdownBuilder のテスト"""

    def test_build_basic(self, sample_session: Session) -> None:
        """基本的なMarkdown生成"""
        options = MarkdownOptions(hashtags="", footer_text="")
        builder = SessionMarkdownBuilder(options=options)
        markdown = builder.build(session=sample_session)

        expected = (
            "# Sample Session\n"
            "\n"
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
        assert markdown == expected

    def test_build_with_hashtags(self, sample_session: Session) -> None:
        """ハッシュタグ付きのMarkdown生成"""
        options = MarkdownOptions(hashtags="#Test #Hash", footer_text="")
        builder = SessionMarkdownBuilder(options=options)
        markdown = builder.build(session=sample_session)

        expected = (
            "# Sample Session\n"
            "\n"
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
        assert markdown == expected

    def test_build_with_footer(self, sample_session: Session) -> None:
        """フッター付きのMarkdown生成"""
        options = MarkdownOptions(hashtags="", footer_text="Footer text here")
        builder = SessionMarkdownBuilder(options=options)
        markdown = builder.build(session=sample_session)

        expected = (
            "# Sample Session\n"
            "\n"
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
        assert markdown == expected

    def test_build_without_speakers(self, empty_session: Session) -> None:
        """スピーカーがいない場合"""
        options = MarkdownOptions(hashtags="", footer_text="")
        builder = SessionMarkdownBuilder(options=options)
        markdown = builder.build(session=empty_session)

        expected = "# Empty Session\n\n\n\n***\n\nhttps://example.com/session/2\n\n***"
        assert markdown == expected

    def test_build_without_title(self) -> None:
        """タイトルが空の場合"""
        session = Session(
            title="",
            timeslot=datetime(2026, 1, 7, 10, 0, 0, tzinfo=UTC),
            room="Hall A",
            track="Track 1",
            speakers=["Speaker A"],
            abstract="Some abstract",
            url="https://example.com",
        )
        options = MarkdownOptions(hashtags="", footer_text="")
        builder = SessionMarkdownBuilder(options=options)
        markdown = builder.build(session=session)

        expected = (
            "Speaker: Speaker A\n\nSome abstract\n\n***\n\nhttps://example.com\n\n***"
        )
        assert markdown == expected

    def test_build_without_url(self) -> None:
        """URLが空の場合"""
        session = Session(
            title="Test Title",
            timeslot=datetime(2026, 1, 7, 10, 0, 0, tzinfo=UTC),
            room="Hall A",
            track="Track 1",
            speakers=["Speaker A"],
            abstract="Some abstract",
            url="",
        )
        options = MarkdownOptions(hashtags="", footer_text="")
        builder = SessionMarkdownBuilder(options=options)
        markdown = builder.build(session=session)

        expected = "# Test Title\n\nSpeaker: Speaker A\n\nSome abstract\n\n***\n\n***"
        assert markdown == expected
