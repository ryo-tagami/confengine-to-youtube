"""ドメイン層のエラー型定義"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ValidationError(Exception):
    """バリデーションエラーの基底クラス"""

    message: str
    cause: Exception | None = field(default=None, kw_only=True)


@dataclass(frozen=True)
class TitleValidationError(ValidationError):
    """タイトルバリデーションエラー"""


@dataclass(frozen=True)
class DescriptionValidationError(ValidationError):
    """説明文バリデーションエラー"""
