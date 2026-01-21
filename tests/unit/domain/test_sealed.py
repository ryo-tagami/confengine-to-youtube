"""sealed module のテスト"""

import pytest

from confengine_to_youtube.domain.sealed import (
    _SEALED,
    _SealedToken,
    sealed_field,
    validate_sealed,
)


class TestSealedToken:
    """_SealedToken のテスト"""

    def test_sealed_token_is_singleton(self) -> None:
        """_SEALED は唯一のインスタンス"""
        assert isinstance(_SEALED, _SealedToken)


class TestValidateSealed:
    """validate_sealed のテスト"""

    def test_validate_with_sealed_token_passes(self) -> None:
        """正しいトークンではエラーなし"""
        instance = object()
        validate_sealed(instance=instance, token=_SEALED)

    def test_validate_with_none_raises_error(self) -> None:
        """Noneトークンではエラー"""
        instance = object()
        with pytest.raises(TypeError, match="cannot be instantiated directly"):
            validate_sealed(instance=instance, token=None)

    def test_validate_with_wrong_token_raises_error(self) -> None:
        """不正なトークンではエラー"""
        instance = object()
        with pytest.raises(TypeError, match="cannot be instantiated directly"):
            validate_sealed(instance=instance, token=_SealedToken())


class TestSealedField:
    """sealed_field のテスト"""

    def test_sealed_field_returns_field(self) -> None:
        """sealed_fieldはフィールドを返す"""
        # sealed_field() は実行時には Field オブジェクトを返すが、
        # 型アノテーションは _SealedToken | None なので型エラーを無視
        field_instance = sealed_field()
        assert field_instance.default is None  # type: ignore[union-attr]
        assert field_instance.repr is False  # type: ignore[union-attr]
        assert field_instance.compare is False  # type: ignore[union-attr]
        assert field_instance.hash is False  # type: ignore[union-attr]
