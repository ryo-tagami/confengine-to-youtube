from __future__ import annotations

from typing import TYPE_CHECKING, Any

from returns.io import IOResult, impure_safe
from ruamel.yaml import YAML

from confengine_to_youtube.adapters.mapping_schema import MappingFileSchema

if TYPE_CHECKING:
    from pathlib import Path


def _load_yaml(file_path: Path) -> dict[str, Any]:
    yaml = YAML()

    with file_path.open(encoding="utf-8") as f:
        return yaml.load(stream=f)  # type: ignore[no-any-return]


class MappingFileReader:
    def read(self, file_path: Path) -> IOResult[MappingFileSchema, Exception]:
        """マッピングファイルを読み込む"""
        return impure_safe(_load_yaml)(file_path).bind(
            lambda data: impure_safe(MappingFileSchema.model_validate)(data),
        )
