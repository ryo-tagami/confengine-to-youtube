"""MarkdownConverter のテスト"""

from confengine_to_youtube.adapters.markdown_converter import MarkdownConverter
from confengine_to_youtube.domain.session_abstract import SessionAbstract


class TestMarkdownConverter:
    """MarkdownConverter のテスト"""

    def test_convert_html_to_markdown(self) -> None:
        """HTML を Markdown に変換する"""
        converter = MarkdownConverter()
        result = converter.convert(html="<p>Hello <strong>World</strong></p>")

        assert result == SessionAbstract(content="Hello **World**")

    def test_convert_empty_string(self) -> None:
        """空文字列は空の SessionAbstract を返す"""
        converter = MarkdownConverter()
        result = converter.convert(html="")

        assert result == SessionAbstract(content="")

    def test_convert_removes_excess_newlines(self) -> None:
        """連続する改行を2つに正規化する"""
        converter = MarkdownConverter()
        result = converter.convert(html="<p>First</p><p></p><p></p><p>Second</p>")

        # 3つ以上の改行が2つに正規化される
        assert result == SessionAbstract(content="First\n\nSecond")
