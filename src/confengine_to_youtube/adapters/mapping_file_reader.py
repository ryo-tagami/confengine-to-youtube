from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import ValidationError
from ruamel.yaml import YAML
from ruamel.yaml.error import YAMLError

from confengine_to_youtube.adapters.mapping_schema import MappingFileSchema
from confengine_to_youtube.usecases.errors import MappingFileError

if TYPE_CHECKING:
    from pathlib import Path


class MappingFileReader:
    def read(self, file_path: Path) -> MappingFileSchema:
        yaml = YAML()
        try:
            with file_path.open(encoding="utf-8") as f:
                data = yaml.load(stream=f)
        except FileNotFoundError as e:
            msg = f"Mapping file not found: {file_path}"
            raise MappingFileError(msg) from e
        except YAMLError as e:
            msg = f"Invalid YAML syntax in {file_path}: {e}"
            raise MappingFileError(msg) from e

        try:
            return MappingFileSchema.model_validate(obj=data)
        except ValidationError as e:
            msg = f"Invalid mapping file format in {file_path}:\n{e}"
            raise MappingFileError(msg) from e
