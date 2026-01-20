"""YouTube動画タイトルビルダー"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from confengine_to_youtube.adapters.constants import (
    ELLIPSIS,
    TITLE_SPEAKER_SEPARATOR,
    YOUTUBE_TITLE_MAX_LENGTH,
)

if TYPE_CHECKING:
    from confengine_to_youtube.domain.session import Session, Speaker


@dataclass(frozen=True)
class YouTubeTitleBuilder:
    """YouTube動画タイトルを生成するビルダー

    フォーマット: "セッションタイトル - スピーカー名"
    100文字制限を超える場合の優先順位:
    1. フルネームで試す (John Doe)
    2. イニシャル表記で試す (J. Doe)
    3. ラストネームのみで試す (Doe)
    4. タイトルを切り詰め (ラストネーム維持)
    """

    def build(self, session: Session) -> str:
        """セッションからYouTube用タイトルを生成"""
        if not session.speakers:
            return self._truncate(
                text=session.title,
                max_length=YOUTUBE_TITLE_MAX_LENGTH,
            )

        # スピーカー名のフォーマット戦略: フルネーム → イニシャル → ラストネーム
        format_strategies = [
            self.format_speakers_full,
            self.format_speakers_initials,
            self.format_speakers_last_name,
        ]

        speaker_part = ""

        for format_func in format_strategies:
            if not (speaker_part := format_func(speakers=session.speakers)):
                # 全スピーカーの名前が空の場合はタイトルのみ
                return self._truncate(
                    text=session.title,
                    max_length=YOUTUBE_TITLE_MAX_LENGTH,
                )

            full_title = self.combine(title=session.title, speaker_part=speaker_part)

            if len(full_title) <= YOUTUBE_TITLE_MAX_LENGTH:
                return full_title

        # どのフォーマットでも収まらない場合はタイトルを切り詰める
        return self._truncate_title(title=session.title, speaker_part=speaker_part)

    @staticmethod
    def format_speakers_full(speakers: list[Speaker]) -> str:
        """スピーカー部分をフルネームで生成"""
        return ", ".join(s.full_name for s in speakers if s.full_name)

    @staticmethod
    def format_speakers_initials(speakers: list[Speaker]) -> str:
        """スピーカー部分をイニシャル表記で生成"""
        return ", ".join(s.initial_name for s in speakers if s.initial_name)

    @staticmethod
    def format_speakers_last_name(speakers: list[Speaker]) -> str:
        """スピーカー部分をラストネームのみで生成"""
        return ", ".join(s.last_name for s in speakers if s.last_name)

    @staticmethod
    def combine(title: str, speaker_part: str) -> str:
        """タイトルとスピーカー部分を結合

        speaker_part が空の場合は title のみを返す。
        """
        if not speaker_part:
            return title

        return f"{title}{TITLE_SPEAKER_SEPARATOR}{speaker_part}"

    def _truncate_title(self, title: str, speaker_part: str) -> str:
        """スピーカー名を優先してタイトルを切り詰める"""
        reserved = len(TITLE_SPEAKER_SEPARATOR) + len(speaker_part) + len(ELLIPSIS)
        available = YOUTUBE_TITLE_MAX_LENGTH - reserved

        if available <= 0:
            # スピーカー名だけで制限を超える場合はスピーカー名を切り詰め
            return self._truncate(
                text=speaker_part,
                max_length=YOUTUBE_TITLE_MAX_LENGTH,
            )

        return f"{title[:available]}{ELLIPSIS}{TITLE_SPEAKER_SEPARATOR}{speaker_part}"

    def _truncate(self, text: str, max_length: int) -> str:
        """テキストを指定長に切り詰める"""
        if len(text) <= max_length:
            return text

        return text[: max_length - len(ELLIPSIS)] + ELLIPSIS
