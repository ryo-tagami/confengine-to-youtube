"""セッションファイル出力"""

from __future__ import annotations

import re
import sys
from pathlib import Path  # noqa: TC003
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from confengine_exporter.domain.session import Session


class SessionFileWriter:
    """セッションをファイルに出力"""

    def __init__(self, output_dir: Path) -> None:
        self.output_dir = output_dir

    def write(self, session: Session, content: str) -> Path:
        """セッションをファイルに書き出し"""
        self.output_dir.mkdir(parents=True, exist_ok=True)

        filename = self._generate_filename(session=session)
        filepath = self.output_dir / filename

        if filepath.exists():
            print(  # noqa: T201
                f"Warning: Overwriting {filepath}",
                file=sys.stderr,
            )

        with filepath.open("w", encoding="utf-8") as file:
            file.write(content)

        return filepath

    def _generate_filename(self, session: Session) -> str:
        """ファイル名を生成"""
        date = session.timeslot.strftime("%Y-%m-%d")
        time = session.timeslot.strftime("%H-%M")
        room = self._sanitize_filename(text=session.room)

        return f"{date}_{room}_{time}.md"

    def _sanitize_filename(self, text: str) -> str:
        """ファイル名に使えない文字を置換"""
        text = re.sub(r'[/:*?"<>|\\]', "-", text)
        text = text.replace(" ", "-")
        text = re.sub(r"-+", "-", text)
        text = text.strip("-")
        return text  # noqa: RET504
