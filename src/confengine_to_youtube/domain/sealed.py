"""Sealed pattern utilities for domain objects.

The sealed pattern ensures domain objects can only be created through
their `.create()` factory methods, preventing direct instantiation.
"""

from __future__ import annotations

from dataclasses import field
from typing import Final


class _SealedToken:
    """Internal token for sealed pattern.

    Only the module itself can create this token, ensuring that
    domain objects can only be instantiated via their .create() methods.
    """

    __slots__ = ()


_SEALED: Final = _SealedToken()


def sealed_field() -> _SealedToken | None:
    return field(default=None, repr=False, compare=False, hash=False)


def validate_sealed(instance: object, token: object) -> None:
    """Validate that an instance was created with the sealed token.

    Args:
        instance: The domain object being validated.
        token: The token passed to the constructor.

    Raises:
        TypeError: If the token is not the sealed token.

    """
    if token is not _SEALED:
        class_name = type(instance).__name__
        msg = f"{class_name} cannot be instantiated directly. Use {class_name}.create()"
        raise TypeError(msg)
