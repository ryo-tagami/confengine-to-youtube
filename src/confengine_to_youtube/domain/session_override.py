"""セッションオーバーライド値オブジェクト"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from confengine_to_youtube.domain.session_abstract import SessionAbstract
    from confengine_to_youtube.domain.speaker import Speaker


@dataclass(frozen=True)
class SessionOverride:
    """YAMLマッピングファイルからのセッション情報オーバーライド

    Noneのフィールドはオーバーライドしない。
    """

    speakers: tuple[Speaker, ...] | None = None
    abstract: SessionAbstract | None = None
