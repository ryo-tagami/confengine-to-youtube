"""DiffFormatter のテスト"""

from __future__ import annotations

from io import StringIO

from rich.console import Console

from confengine_to_youtube.infrastructure.cli.diff_formatter import DiffFormatter
from confengine_to_youtube.usecases.dto import VideoUpdatePreview


class TestDiffFormatter:
    """DiffFormatter のテスト"""

    def test_print_preview_with_title_change(self) -> None:
        """タイトル変更がある場合にdiffを表示する"""
        output = StringIO()
        console = Console(file=output, force_terminal=False, width=120)
        formatter = DiffFormatter(console=console)

        preview = VideoUpdatePreview(
            session_key="2026-01-07T10:00:00+09:00_Hall A",
            video_id="video1",
            current_title="Old Title",
            current_description="Same Description",
            new_title="New Title",
            new_description="Same Description",
        )

        formatter.print_preview(preview=preview, index=1)
        result = output.getvalue()

        assert "  Video ID: video1" in result.splitlines()
        assert "    -Old Title" in result.splitlines()
        assert "    +New Title" in result.splitlines()

    def test_print_preview_with_description_change(self) -> None:
        """description変更がある場合にdiffを表示する"""
        output = StringIO()
        console = Console(file=output, force_terminal=False, width=120)
        formatter = DiffFormatter(console=console)

        preview = VideoUpdatePreview(
            session_key="2026-01-07T10:00:00+09:00_Hall A",
            video_id="video1",
            current_title="Same Title",
            current_description="Old Description\nSame Line",
            new_title="Same Title",
            new_description="New Description\nSame Line",
        )

        formatter.print_preview(preview=preview, index=1)
        result = output.getvalue()

        assert "-Old Description" in result.splitlines()
        assert "+New Description" in result.splitlines()
        # Same Lineは変更なしなので、コンテキスト行として表示
        assert " Same Line" in result.splitlines()

    def test_print_preview_no_title_change(self) -> None:
        """タイトルに変更がない場合は (unchanged) を表示する"""
        output = StringIO()
        console = Console(file=output, force_terminal=False, width=120)
        formatter = DiffFormatter(console=console)

        preview = VideoUpdatePreview(
            session_key="2026-01-07T10:00:00+09:00_Hall A",
            video_id="video1",
            current_title="Same Title",
            current_description="Old Description",
            new_title="Same Title",
            new_description="New Description",
        )

        formatter.print_preview(preview=preview, index=1)
        result = output.getvalue()

        assert "    (unchanged) Same Title" in result.splitlines()

    def test_print_preview_no_description_change(self) -> None:
        """descriptionに変更がない場合は (unchanged) を表示する"""
        output = StringIO()
        console = Console(file=output, force_terminal=False, width=120)
        formatter = DiffFormatter(console=console)

        preview = VideoUpdatePreview(
            session_key="2026-01-07T10:00:00+09:00_Hall A",
            video_id="video1",
            current_title="Old Title",
            current_description="Same Description",
            new_title="New Title",
            new_description="Same Description",
        )

        formatter.print_preview(preview=preview, index=1)
        result = output.getvalue()

        # Descriptionセクションの後に (unchanged) が表示される
        assert "  Description:" in result.splitlines()
        assert "    (unchanged)" in result.splitlines()

    def test_print_summary(self) -> None:
        """サマリーを表示する"""
        output = StringIO()
        console = Console(file=output, force_terminal=False, width=120)
        formatter = DiffFormatter(console=console)

        formatter.print_summary(update_count=3, unchanged_count=2)
        result = output.getvalue()

        expected = "Summary: Would update 3 videos, skip 2 unchanged videos"
        assert expected in result.splitlines()

    def test_print_summary_with_zero_unchanged(self) -> None:
        """変更なしが0件の場合も表示する"""
        output = StringIO()
        console = Console(file=output, force_terminal=False, width=120)
        formatter = DiffFormatter(console=console)

        formatter.print_summary(update_count=5, unchanged_count=0)
        result = output.getvalue()

        expected = "Summary: Would update 5 videos, skip 0 unchanged videos"
        assert expected in result.splitlines()

    def test_print_preview_long_description_truncated(self) -> None:
        """200文字を超えるdescriptionは変更なしの場合トランケートされる"""
        output = StringIO()
        console = Console(file=output, force_terminal=False, width=120)
        formatter = DiffFormatter(console=console)

        long_description = "X" * 250  # 200文字を超える

        preview = VideoUpdatePreview(
            session_key="2026-01-07T10:00:00+09:00_Hall A",
            video_id="video1",
            current_title="Same Title",
            current_description=long_description,
            new_title="Same Title",
            new_description=long_description,
        )

        formatter.print_preview(preview=preview, index=1)
        result = output.getvalue()

        # トランケートされて200文字 + "..."
        assert result.count("X") == 200
        assert any("..." in line for line in result.splitlines())
        # unchangedも表示される
        assert "    (unchanged)" in result.splitlines()
