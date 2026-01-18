"""YouTube動画説明文ビルダーのテスト"""

from datetime import UTC, datetime

import pytest

from confengine_exporter.adapters.constants import YOUTUBE_DESCRIPTION_MAX_LENGTH
from confengine_exporter.adapters.youtube_description_builder import (
    YouTubeDescriptionBuilder,
    YouTubeDescriptionOptions,
)
from confengine_exporter.domain.session import Session


class TestYouTubeDescriptionBuilder:
    """YouTubeDescriptionBuilder のテスト"""

    def test_build_basic(self, sample_session: Session) -> None:
        """基本的なMarkdown生成"""
        options = YouTubeDescriptionOptions(hashtags="", footer_text="")
        builder = YouTubeDescriptionBuilder(options=options)
        markdown = builder.build(session=sample_session)

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
        assert markdown == expected

    def test_build_with_hashtags(self, sample_session: Session) -> None:
        """ハッシュタグ付きのMarkdown生成"""
        options = YouTubeDescriptionOptions(hashtags="#Test #Hash", footer_text="")
        builder = YouTubeDescriptionBuilder(options=options)
        markdown = builder.build(session=sample_session)

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
        assert markdown == expected

    def test_build_with_footer(self, sample_session: Session) -> None:
        """フッター付きのMarkdown生成"""
        options = YouTubeDescriptionOptions(hashtags="", footer_text="Footer text here")
        builder = YouTubeDescriptionBuilder(options=options)
        markdown = builder.build(session=sample_session)

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
        assert markdown == expected

    def test_build_without_speakers(self, empty_session: Session) -> None:
        """スピーカーがいない場合"""
        options = YouTubeDescriptionOptions(hashtags="", footer_text="")
        builder = YouTubeDescriptionBuilder(options=options)
        markdown = builder.build(session=empty_session)

        expected = "***\n\nhttps://example.com/session/2\n\n***"
        assert markdown == expected

    def test_build_without_abstract(self) -> None:
        """abstractが空の場合"""
        session = Session(
            title="Test Title",
            timeslot=datetime(
                year=2026, month=1, day=7, hour=10, minute=0, second=0, tzinfo=UTC
            ),
            room="Hall A",
            track="Track 1",
            speakers=["Speaker A"],
            abstract="",
            url="https://example.com",
        )
        options = YouTubeDescriptionOptions(hashtags="", footer_text="")
        builder = YouTubeDescriptionBuilder(options=options)
        markdown = builder.build(session=session)

        expected = "Speaker: Speaker A\n\n***\n\nhttps://example.com\n\n***"
        assert markdown == expected

    def test_build_without_url(self) -> None:
        """URLが空の場合"""
        session = Session(
            title="Test Title",
            timeslot=datetime(
                year=2026, month=1, day=7, hour=10, minute=0, second=0, tzinfo=UTC
            ),
            room="Hall A",
            track="Track 1",
            speakers=["Speaker A"],
            abstract="Some abstract",
            url="",
        )
        options = YouTubeDescriptionOptions(hashtags="", footer_text="")
        builder = YouTubeDescriptionBuilder(options=options)
        markdown = builder.build(session=session)

        expected = "Speaker: Speaker A\n\nSome abstract\n\n***\n\n***"
        assert markdown == expected

    def test_frame_exceeds_max_length_raises_error(self) -> None:
        """フレーム部分だけで文字数制限を超える場合はValueErrorを発生"""
        session = Session(
            title="Title",
            timeslot=datetime(
                year=2026, month=1, day=7, hour=10, minute=0, second=0, tzinfo=UTC
            ),
            room="Hall A",
            track="Track 1",
            speakers=["Speaker"],
            abstract="Short",
            url="https://example.com",
        )
        # 5000文字を超えるフッターを用意
        long_footer = "X" * 6000
        options = YouTubeDescriptionOptions(
            hashtags="",
            footer_text=long_footer,
        )
        builder = YouTubeDescriptionBuilder(options=options)

        expected_msg = "フレーム部分だけで文字数制限を超えています"
        with pytest.raises(expected_exception=ValueError, match=expected_msg):
            builder.build(session=session)

    def test_long_abstract_is_truncated(self) -> None:
        """長いabstractはYouTube説明文の最大文字数に収まるよう切り詰められる"""
        # 5000文字を超えるabstractを用意
        long_abstract = "A" * 6000
        session = Session(
            title="Title",
            timeslot=datetime(
                year=2026, month=1, day=7, hour=10, minute=0, second=0, tzinfo=UTC
            ),
            room="Hall A",
            track="Track 1",
            speakers=["Speaker"],
            abstract=long_abstract,
            url="https://example.com",
        )
        options = YouTubeDescriptionOptions(
            hashtags="",
            footer_text="Footer",
        )
        builder = YouTubeDescriptionBuilder(options=options)
        markdown = builder.build(session=session)

        # 最大文字数以下に収まる
        assert len(markdown) <= YOUTUBE_DESCRIPTION_MAX_LENGTH
        # 切り詰めマーカーが含まれる
        assert "..." in markdown
        # フレーム部分は残る
        assert "Footer" in markdown
        assert "https://example.com" in markdown

    def test_sanitize_removes_angle_brackets_from_urls(self) -> None:
        """Markdownオートリンク記法 <URL> を URL に変換する"""
        session = Session(
            title="Test",
            timeslot=datetime(
                year=2026, month=1, day=7, hour=10, minute=0, second=0, tzinfo=UTC
            ),
            room="Hall A",
            track="Track 1",
            speakers=["Speaker"],
            abstract="Link: <https://example.com/page>",
            url="",
        )
        options = YouTubeDescriptionOptions(hashtags="", footer_text="")
        builder = YouTubeDescriptionBuilder(options=options)
        markdown = builder.build(session=session)

        expected = "Speaker: Speaker\n\nLink: https://example.com/page\n\n***\n\n***"
        assert markdown == expected

    def test_sanitize_handles_multiple_autolinks(self) -> None:
        """複数のオートリンクを処理"""
        session = Session(
            title="Test",
            timeslot=datetime(
                year=2026, month=1, day=7, hour=10, minute=0, second=0, tzinfo=UTC
            ),
            room="Hall A",
            track="Track 1",
            speakers=["Speaker"],
            abstract="See <https://a.com> and <http://b.com>",
            url="",
        )
        options = YouTubeDescriptionOptions(hashtags="", footer_text="")
        builder = YouTubeDescriptionBuilder(options=options)
        markdown = builder.build(session=session)

        expected = (
            "Speaker: Speaker\n\nSee https://a.com and http://b.com\n\n***\n\n***"
        )
        assert markdown == expected
