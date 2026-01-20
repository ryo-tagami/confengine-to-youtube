"""YouTubeタイトル値オブジェクト"""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar


@dataclass(frozen=True)
class YouTubeTitle:
    """YouTube動画タイトル (最大100文字)"""

    MAX_LENGTH: ClassVar[int] = 100

    value: str

    def __post_init__(self) -> None:  # noqa: D105
        if not self.value:
            msg = "タイトルは必須です"
            raise ValueError(msg)
        if len(self.value) > self.MAX_LENGTH:
            msg = f"タイトルは{self.MAX_LENGTH}文字以内 (現在: {len(self.value)}文字)"
            raise ValueError(msg)

    def __str__(self) -> str:  # noqa: D105
        return self.value
