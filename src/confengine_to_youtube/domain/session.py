"""セッションエンティティ"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from snakemd import Document

from confengine_to_youtube.domain.constants import ELLIPSIS, TITLE_SPEAKER_SEPARATOR
from confengine_to_youtube.domain.youtube_description import YouTubeDescription
from confengine_to_youtube.domain.youtube_title import YouTubeTitle

if TYPE_CHECKING:
    from confengine_to_youtube.domain.abstract_markdown import AbstractMarkdown
    from confengine_to_youtube.domain.schedule_slot import ScheduleSlot


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
            # str.split() は空文字列を含まないため part[0] は安全
            initials = " ".join(f"{part[0]}." for part in self.first_name.split())
            return f"{initials} {self.last_name}".strip()

        return self.last_name

    @staticmethod
    def format_list_full(speakers: tuple[Speaker, ...]) -> str:
        """スピーカー部分をフルネームで生成"""
        return ", ".join(s.full_name for s in speakers if s.full_name)

    @staticmethod
    def format_list_initials(speakers: tuple[Speaker, ...]) -> str:
        """スピーカー部分をイニシャル表記で生成"""
        return ", ".join(s.initial_name for s in speakers if s.initial_name)

    @staticmethod
    def format_list_last_name(speakers: tuple[Speaker, ...]) -> str:
        """スピーカー部分をラストネームのみで生成"""
        return ", ".join(s.last_name for s in speakers if s.last_name)


@dataclass(frozen=True)
class Session:
    slot: ScheduleSlot
    title: str
    track: str
    speakers: tuple[Speaker, ...]
    abstract: AbstractMarkdown
    url: str

    @property
    def has_content(self) -> bool:
        return bool(self.abstract.content)

    @property
    def youtube_title(self) -> YouTubeTitle:
        """YouTube用タイトルを生成

        フォーマット: "セッションタイトル - スピーカー名"
        100文字制限を超える場合の優先順位:
        1. フルネームで試す (John Doe)
        2. イニシャル表記で試す (J. Doe)
        3. ラストネームのみで試す (Doe)
        4. タイトルを切り詰め (ラストネーム維持)
        """
        max_length = YouTubeTitle.MAX_LENGTH

        if not self.speakers:
            return YouTubeTitle(
                value=self._truncate_text(text=self.title, max_length=max_length),
            )

        format_strategies = [
            Speaker.format_list_full,
            Speaker.format_list_initials,
            Speaker.format_list_last_name,
        ]

        speaker_part = ""

        for format_func in format_strategies:
            if not (speaker_part := format_func(self.speakers)):
                return YouTubeTitle(
                    value=self._truncate_text(text=self.title, max_length=max_length),
                )

            full_title = self._combine_title_with_speaker(speaker_part=speaker_part)

            if len(full_title) <= max_length:
                return YouTubeTitle(value=full_title)

        # どのフォーマットでも収まらない場合はタイトルを切り詰める
        return YouTubeTitle(
            value=self._truncate_title_keeping_speaker(speaker_part=speaker_part),
        )

    def _truncate_text(self, text: str, max_length: int) -> str:
        """テキストを指定長に切り詰める"""
        if len(text) <= max_length:
            return text

        return text[: max_length - len(ELLIPSIS)] + ELLIPSIS

    def _combine_title_with_speaker(self, speaker_part: str) -> str:
        """タイトルとスピーカー部分を結合"""
        if not speaker_part:
            return self.title

        return f"{self.title}{TITLE_SPEAKER_SEPARATOR}{speaker_part}"

    def _truncate_title_keeping_speaker(self, speaker_part: str) -> str:
        """スピーカー名を優先してタイトルを切り詰める"""
        max_length = YouTubeTitle.MAX_LENGTH
        reserved = len(TITLE_SPEAKER_SEPARATOR) + len(speaker_part) + len(ELLIPSIS)
        available = max_length - reserved

        if available <= 0:
            return self._truncate_text(text=speaker_part, max_length=max_length)

        truncated = f"{self.title[:available]}{ELLIPSIS}"

        return f"{truncated}{TITLE_SPEAKER_SEPARATOR}{speaker_part}"

    def to_youtube_description(
        self,
        hashtags: tuple[str, ...],
        footer: str,
    ) -> YouTubeDescription:
        """YouTube用説明文を生成

        Args:
            hashtags: ハッシュタグのタプル
            footer: フッター文字列

        Returns:
            YouTubeDescription

        """
        abstract = str(self.abstract)
        max_length = YouTubeDescription.MAX_LENGTH

        frame_length = self._calculate_frame_length(
            hashtags=hashtags,
            footer=footer,
        )
        available = max_length - frame_length

        if available < len(ELLIPSIS):
            msg = f"フレーム部分だけで文字数制限を超えています ({frame_length=})"
            raise ValueError(msg)

        if abstract and len(abstract) > available:
            abstract = abstract[: available - len(ELLIPSIS)] + ELLIPSIS

        return YouTubeDescription(
            value=self._build_description_document(
                abstract=abstract,
                hashtags=hashtags,
                footer=footer,
            ),
        )

    def _calculate_frame_length(
        self,
        hashtags: tuple[str, ...],
        footer: str,
    ) -> int:
        """フレーム部分 (abstract以外) の文字数を計算"""
        placeholder = "X"
        doc_with_placeholder = self._build_description_document(
            abstract=placeholder,
            hashtags=hashtags,
            footer=footer,
        )

        return len(doc_with_placeholder) - len(placeholder)

    def _build_description_document(
        self,
        abstract: str,
        hashtags: tuple[str, ...],
        footer: str,
    ) -> str:
        """説明文のMarkdown文書を構築"""
        doc = Document()

        if speakers_str := Speaker.format_list_full(speakers=self.speakers):
            doc.add_paragraph(text=f"Speaker: {speakers_str}")

        if abstract:
            doc.add_raw(text=abstract)

        doc.add_horizontal_rule()

        if self.url:
            doc.add_paragraph(text=self.url)

        if hashtags:
            doc.add_paragraph(text=" ".join(hashtags))

        doc.add_horizontal_rule()

        if footer:
            doc.add_paragraph(text=footer)

        return YouTubeDescription.sanitize_for_youtube(text=str(doc))
