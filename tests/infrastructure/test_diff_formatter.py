"""DiffFormatter のテスト"""

from __future__ import annotations

from io import StringIO

from rich.console import Console

from confengine_exporter.infrastructure.cli.diff_formatter import DiffFormatter
from confengine_exporter.usecases.dto import UpdatePreview


class TestDiffFormatter:
    """DiffFormatter のテスト"""

    def test_print_preview_with_title_change(self) -> None:
        """タイトル変更がある場合にdiffを表示する"""
        output = StringIO()
        console = Console(file=output, force_terminal=True, width=120)
        formatter = DiffFormatter(console=console)

        preview = UpdatePreview(
            session_key="2026-01-07T10:00:00+09:00_Hall A",
            video_id="video1",
            current_title="Old Title",
            current_description="Same Description",
            new_title="New Title",
            new_description="Same Description",
        )

        formatter.print_preview(preview=preview, index=1)
        result = output.getvalue()

        assert "video1" in result
        assert "-Old Title" in result
        assert "+New Title" in result

    def test_print_preview_with_description_change(self) -> None:
        """description変更がある場合にdiffを表示する"""
        output = StringIO()
        console = Console(file=output, force_terminal=True, width=120)
        formatter = DiffFormatter(console=console)

        preview = UpdatePreview(
            session_key="2026-01-07T10:00:00+09:00_Hall A",
            video_id="video1",
            current_title="Same Title",
            current_description="Old Description\nSame Line",
            new_title="Same Title",
            new_description="New Description\nSame Line",
        )

        formatter.print_preview(preview=preview, index=1)
        result = output.getvalue()

        assert "-Old Description" in result
        assert "+New Description" in result
        # Same Lineは変更なしなので、コンテキスト行として表示
        assert "Same Line" in result

    def test_print_preview_with_error(self) -> None:
        """エラーがある場合にエラーメッセージを表示する"""
        output = StringIO()
        console = Console(file=output, force_terminal=True, width=120)
        formatter = DiffFormatter(console=console)

        preview = UpdatePreview(
            session_key="2026-01-07T10:00:00+09:00_Hall A",
            video_id="video1",
            current_title=None,
            current_description=None,
            new_title=None,
            new_description=None,
            error="API Error",
        )

        formatter.print_preview(preview=preview, index=1)
        result = output.getvalue()

        assert "Error" in result
        assert "API Error" in result

    def test_print_preview_no_title_change(self) -> None:
        """タイトルに変更がない場合は (unchanged) を表示する"""
        output = StringIO()
        console = Console(file=output, force_terminal=True, width=120)
        formatter = DiffFormatter(console=console)

        preview = UpdatePreview(
            session_key="2026-01-07T10:00:00+09:00_Hall A",
            video_id="video1",
            current_title="Same Title",
            current_description="Old Description",
            new_title="Same Title",
            new_description="New Description",
        )

        formatter.print_preview(preview=preview, index=1)
        result = output.getvalue()

        assert "unchanged" in result
        assert "Same Title" in result

    def test_print_preview_no_description_change(self) -> None:
        """descriptionに変更がない場合は (unchanged) を表示する"""
        output = StringIO()
        console = Console(file=output, force_terminal=True, width=120)
        formatter = DiffFormatter(console=console)

        preview = UpdatePreview(
            session_key="2026-01-07T10:00:00+09:00_Hall A",
            video_id="video1",
            current_title="Old Title",
            current_description="Same Description",
            new_title="New Title",
            new_description="Same Description",
        )

        formatter.print_preview(preview=preview, index=1)
        result = output.getvalue()

        # descriptionセクションにunchangedが表示される
        assert "unchanged" in result

    def test_print_summary(self) -> None:
        """サマリーを表示する"""
        output = StringIO()
        console = Console(file=output, force_terminal=True, width=120)
        formatter = DiffFormatter(console=console)

        formatter.print_summary(success_count=5, error_count=2)
        result = output.getvalue()

        assert "5" in result
        assert "2" in result
        assert "Would update" in result

    def test_print_summary_no_errors(self) -> None:
        """エラーがない場合はエラー数を表示しない"""
        output = StringIO()
        console = Console(file=output, force_terminal=True, width=120)
        formatter = DiffFormatter(console=console)

        formatter.print_summary(success_count=3, error_count=0)
        result = output.getvalue()

        assert "3" in result
        assert "Would update" in result
        assert "error" not in result.lower()

    def test_print_preview_long_description_truncated(self) -> None:
        """200文字を超えるdescriptionは変更なしの場合トランケートされる"""
        output = StringIO()
        console = Console(file=output, force_terminal=True, width=120)
        formatter = DiffFormatter(console=console)

        long_description = "A" * 250  # 200文字を超える

        preview = UpdatePreview(
            session_key="2026-01-07T10:00:00+09:00_Hall A",
            video_id="video1",
            current_title="Same Title",
            current_description=long_description,
            new_title="Same Title",
            new_description=long_description,
        )

        formatter.print_preview(preview=preview, index=1)
        result = output.getvalue()

        # トランケートされて "..." が付く
        assert "..." in result
        # 全文は表示されない (250文字のAが全て表示されていない)
        assert "A" * 250 not in result
        # unchangedも表示される
        assert "unchanged" in result
