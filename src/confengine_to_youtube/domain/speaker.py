"""スピーカー値オブジェクト"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Speaker:
    """スピーカー情報"""

    first_name: str
    last_name: str

    @property
    def full_name(self) -> str | None:
        """フルネームを取得 (例: "John Doe")

        first_name と last_name が両方空の場合は None を返す。
        """
        name = f"{self.first_name} {self.last_name}".strip()

        return name or None

    @property
    def initial_name(self) -> str | None:
        """イニシャル表記を取得

        例: "John Doe" -> "J. Doe", "Tze Chin Tang" -> "T. C. Tang"

        first_name と last_name が両方空の場合は None を返す。
        """
        if not self.first_name and not self.last_name:
            return None

        if self.first_name:
            # split() は空文字列を含まないリストを返す (空白のみなら空リスト)
            initials = " ".join(f"{part[0]}." for part in self.first_name.split())

            return f"{initials} {self.last_name}".strip()

        return self.last_name
