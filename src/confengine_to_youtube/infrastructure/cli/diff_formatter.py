"""色付きdiff表示モジュール"""

from __future__ import annotations

import difflib
from typing import TYPE_CHECKING

from rich.syntax import Syntax
from rich.text import Text

from confengine_to_youtube.infrastructure.cli.constants import PREVIEW_TRUNCATE_LENGTH

if TYPE_CHECKING:
    from rich.console import Console

    from confengine_to_youtube.usecases.dto import VideoUpdatePreview


class DiffFormatter:
    """deltaライクな色付きdiff表示"""

    def __init__(self, console: Console) -> None:
        self._console = console

    def print_header(self, message: str) -> None:
        """ヘッダーメッセージを表示"""
        self._console.print(f"[bold]{message}[/bold]")

    def print_preview(self, preview: VideoUpdatePreview, index: int) -> None:
        """プレビューを色付きdiff形式で表示"""
        self._console.print(
            f"\n[bold][{index}] {preview.session_key}[/bold]",
            highlight=False,
        )
        self._console.print(
            f"  Video ID: {preview.video_id}",
            highlight=False,
        )

        # Title diff
        self._console.print("\n  [bold]Title:[/bold]")

        if preview.current_title == preview.new_title:
            self._console.print(
                f"    [dim](unchanged) {preview.current_title}[/dim]",
                highlight=False,
            )
        else:
            self._console.print(
                f"    [red]-{preview.current_title}[/red]",
                highlight=False,
            )
            self._console.print(
                f"    [green]+{preview.new_title}[/green]",
                highlight=False,
            )

        # Description diff
        self._console.print("\n  [bold]Description:[/bold]")

        self._print_diff(
            old=preview.current_description,
            new=preview.new_description,
        )

    def _print_diff(self, old: str, new: str) -> None:
        """複数行のdiffをSyntaxハイライトで表示"""
        if old == new:
            # 変更なしの場合は先頭部分だけ表示
            if len(old) > PREVIEW_TRUNCATE_LENGTH:
                preview_text = old[:PREVIEW_TRUNCATE_LENGTH] + "..."
            else:
                preview_text = old

            for line in preview_text.split(sep="\n"):
                self._console.print(f"    [dim]{line}[/dim]", highlight=False)

            self._console.print("    [dim](unchanged)[/dim]", highlight=False)

            return

        diff = difflib.unified_diff(
            a=old.splitlines(keepends=True),
            b=new.splitlines(keepends=True),
            fromfile="Current",
            tofile="New",
        )
        diff_text = "".join(diff)

        syntax = Syntax(
            code=diff_text,
            lexer="diff",
            theme="ansi_dark",
            line_numbers=False,
        )

        self._console.print(syntax)

    def print_summary(self, count: int) -> None:
        """サマリーを表示"""
        text = Text()
        text.append("\nSummary: Would update ")
        text.append(str(count), style="bold green")
        text.append(" videos")

        self._console.print(text)
