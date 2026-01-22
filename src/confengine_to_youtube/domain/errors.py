"""ドメイン層のエラー型定義"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


class DomainError(ABC):
    """ドメイン層のエラー基底クラス"""

    @property
    @abstractmethod
    def message(self) -> str:
        """エラーメッセージ"""


@dataclass(frozen=True)
class TitleEmptyError(DomainError):
    """Title is empty."""

    @property
    def message(self) -> str:  # pragma: no cover
        return "Title is required"


@dataclass(frozen=True)
class TitleTooLongError(DomainError):
    """Title exceeds maximum length."""

    length: int
    max_length: int

    @property
    def message(self) -> str:  # pragma: no cover
        return (
            f"Title must be {self.max_length} characters or less "
            f"(current: {self.length})"
        )


@dataclass(frozen=True)
class DescriptionTooLongError(DomainError):
    """Description exceeds maximum length."""

    length: int
    max_length: int

    @property
    def message(self) -> str:  # pragma: no cover
        return (
            f"Description must be {self.max_length} characters or less "
            f"(current: {self.length})"
        )


@dataclass(frozen=True)
class FrameOverflowError(DomainError):
    """Frame content alone exceeds character limit."""

    frame_length: int

    @property
    def message(self) -> str:  # pragma: no cover
        return (
            f"Frame content alone exceeds character limit (length: {self.frame_length})"
        )


# Union型でドメインエラーを集約
type TitleError = TitleEmptyError | TitleTooLongError
