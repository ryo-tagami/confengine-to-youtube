"""YouTube向けコンテンツ生成ドメインサービス"""

from __future__ import annotations

from typing import TYPE_CHECKING

from returns.result import Failure, Result
from snakemd import Document

from confengine_to_youtube.domain.constants import ELLIPSIS, TITLE_SPEAKER_SEPARATOR
from confengine_to_youtube.domain.errors import (
    DescriptionError,
    FrameOverflowError,
    TitleError,
)
from confengine_to_youtube.domain.youtube_description import YouTubeDescription
from confengine_to_youtube.domain.youtube_title import YouTubeTitle

if TYPE_CHECKING:
    from confengine_to_youtube.domain.session import Session


class YouTubeContentGenerator:
    """SessionからYouTube用コンテンツを生成するドメインサービス

    YouTube固有のフォーマット変換ロジックをカプセル化する。
    """

    @staticmethod
    def generate_title(session: Session) -> Result[YouTubeTitle, TitleError]:
        """YouTube用タイトルを生成

        フォーマット: "セッションタイトル - スピーカー名"
        100文字制限を超える場合の優先順位:
        1. フルネームで試す (John Doe)
        2. イニシャル表記で試す (J. Doe)
        3. ラストネームのみで試す (Doe)
        4. タイトルを切り詰め (ラストネーム維持)

        Returns:
            Success(YouTubeTitle): 生成成功
            Failure(TitleError): タイトル生成エラー

        Note:
            切り詰めロジックにより TitleTooLongError は実際には発生しない。
            また Session の空タイトル禁止により TitleEmptyError も発生しない。

        """
        max_length = YouTubeTitle.MAX_LENGTH

        if not session.speakers:
            return YouTubeTitle.create(
                value=_truncate_text(text=session.title, max_length=max_length),
            )

        speaker_formats = [
            session.speakers_full,
            session.speakers_initials,
            session.speakers_last_name,
        ]

        for speaker_part in speaker_formats:
            # フォーマット済みスピーカー名が空の場合はタイトルのみを返す
            if not speaker_part:
                return YouTubeTitle.create(
                    value=_truncate_text(text=session.title, max_length=max_length),
                )

            full_title = _combine_title_with_speaker(
                title=session.title,
                speaker_part=speaker_part,
            )

            if len(full_title) <= max_length:
                return YouTubeTitle.create(value=full_title)

        # どのフォーマットでも収まらない場合はタイトルを切り詰める
        return YouTubeTitle.create(
            value=_truncate_title_keeping_speaker(
                title=session.title,
                speaker_part=session.speakers_last_name,
            ),
        )

    @staticmethod
    def generate_description(
        session: Session,
        hashtags: tuple[str, ...],
        footer: str,
    ) -> Result[YouTubeDescription, DescriptionError]:
        """YouTube用説明文を生成

        Args:
            session: セッション
            hashtags: ハッシュタグのタプル
            footer: フッター文字列

        Returns:
            Success(YouTubeDescription): 生成成功
            Failure(DescriptionError): 説明文生成エラー

        Note:
            切り詰めロジックにより DescriptionTooLongError は実際には発生しない。

        """
        abstract = str(session.abstract)
        max_length = YouTubeDescription.MAX_LENGTH

        frame_length = _calculate_frame_length(
            session=session,
            hashtags=hashtags,
            footer=footer,
        )
        available = max_length - frame_length

        if available < len(ELLIPSIS):
            return Failure(FrameOverflowError(frame_length=frame_length))

        if abstract and len(abstract) > available:
            abstract = abstract[: available - len(ELLIPSIS)] + ELLIPSIS

        description_text = _build_description_document(
            session=session,
            abstract=abstract,
            hashtags=hashtags,
            footer=footer,
        )

        return YouTubeDescription.create(value=description_text)


def _truncate_text(text: str, max_length: int) -> str:
    """テキストを指定長に切り詰める"""
    if len(text) <= max_length:
        return text

    return text[: max_length - len(ELLIPSIS)] + ELLIPSIS


def _combine_title_with_speaker(title: str, speaker_part: str) -> str:
    """タイトルとスピーカー部分を結合"""
    # generate_title() は空でない speaker_part を必ず渡すが、
    # この関数の責務として最終的に防御をする。
    if not speaker_part:  # pragma: no cover
        return title

    return f"{title}{TITLE_SPEAKER_SEPARATOR}{speaker_part}"


def _truncate_title_keeping_speaker(title: str, speaker_part: str) -> str:
    """スピーカー名を優先してタイトルを切り詰める"""
    max_length = YouTubeTitle.MAX_LENGTH

    # generate_title() は空でない speaker_part を必ず渡すが、
    # この関数の責務として最終的に防御をする。
    if not speaker_part:  # pragma: no cover
        return _truncate_text(text=title, max_length=max_length)

    reserved = len(TITLE_SPEAKER_SEPARATOR) + len(speaker_part) + len(ELLIPSIS)
    available = max_length - reserved

    if available <= 0:
        return _truncate_text(text=speaker_part, max_length=max_length)

    truncated = f"{title[:available]}{ELLIPSIS}"

    return f"{truncated}{TITLE_SPEAKER_SEPARATOR}{speaker_part}"


def _calculate_frame_length(
    session: Session,
    hashtags: tuple[str, ...],
    footer: str,
) -> int:
    """フレーム部分 (abstract以外) の文字数を計算"""
    placeholder = "X" if session.has_content else ""
    doc_with_placeholder = _build_description_document(
        session=session,
        abstract=placeholder,
        hashtags=hashtags,
        footer=footer,
    )

    return len(doc_with_placeholder) - len(placeholder)


def _build_description_document(
    session: Session,
    abstract: str,
    hashtags: tuple[str, ...],
    footer: str,
) -> str:
    """説明文のMarkdown文書を構築"""
    doc = Document()

    if session.speakers_full:
        doc.add_paragraph(text=f"Speaker: {session.speakers_full}")

    if abstract:
        doc.add_raw(text=abstract)

    doc.add_horizontal_rule()

    if session.url:
        doc.add_paragraph(text=session.url)

    if hashtags:
        doc.add_paragraph(text=" ".join(hashtags))

    doc.add_horizontal_rule()

    if footer:
        doc.add_paragraph(text=footer)

    return YouTubeDescription.sanitize_for_youtube(text=str(doc))
