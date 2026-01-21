"""YouTube動画マッピングエンティティ"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Self

from returns.result import Result, Success

from confengine_to_youtube.domain.sealed import (
    _SEALED,
    _SealedToken,
    sealed_field,
    validate_sealed,
)

if TYPE_CHECKING:
    from collections.abc import Set as AbstractSet
    from typing import Never

    from confengine_to_youtube.domain.schedule_slot import ScheduleSlot


@dataclass(frozen=True)
class VideoMapping:
    slot: ScheduleSlot
    video_id: str
    _sealed: _SealedToken | None = sealed_field()  # noqa: RUF009

    def __post_init__(self) -> None:
        validate_sealed(instance=self, token=self._sealed)

    @classmethod
    def create(
        cls,
        slot: ScheduleSlot,
        video_id: str,
    ) -> Result[Self, Never]:
        return Success(cls(slot=slot, video_id=video_id, _sealed=_SEALED))


@dataclass(frozen=True)
class MappingConfig:
    conf_id: str
    mappings: frozenset[VideoMapping]
    hashtags: tuple[str, ...]
    footer: str
    _sealed: _SealedToken | None = sealed_field()  # noqa: RUF009

    def __post_init__(self) -> None:
        validate_sealed(instance=self, token=self._sealed)

    @classmethod
    def create(
        cls,
        conf_id: str,
        mappings: frozenset[VideoMapping],
        hashtags: tuple[str, ...],
        footer: str,
    ) -> Result[Self, Never]:
        return Success(
            cls(
                conf_id=conf_id,
                mappings=mappings,
                hashtags=hashtags,
                footer=footer,
                _sealed=_SEALED,
            ),
        )

    def find_mapping(self, slot: ScheduleSlot) -> VideoMapping | None:
        # 線形検索だが、セッション数は通常数百以下のため実用上問題なし
        for mapping in self.mappings:
            if mapping.slot == slot:
                return mapping

        return None

    def find_unused(
        self,
        used_slots: AbstractSet[ScheduleSlot],
    ) -> frozenset[VideoMapping]:
        return frozenset(m for m in self.mappings if m.slot not in used_slots)
