from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

from confengine_exporter.adapters.mapping_file_reader import (
    MappingFileError,
    MappingFileReader,
)


class TestMappingFileReader:
    def test_read_yaml_file(self, tmp_path: Path) -> None:
        yaml_content = """
sessions:
  "2026-01-07":
    "Hall A":
      "10:00":
        video_id: "abc123"
      "11:00":
        video_id: "def456"
    "Hall B":
      "10:00":
        video_id: "ghi789"
"""
        jst = ZoneInfo(key="Asia/Tokyo")

        yaml_file = tmp_path / "mapping.yaml"
        yaml_file.write_text(data=yaml_content, encoding="utf-8")

        reader = MappingFileReader()
        config = reader.read(file_path=yaml_file, timezone=jst)

        assert len(config.mappings) == 3

        mapping1 = config.find_mapping(
            timeslot=datetime(year=2026, month=1, day=7, hour=10, minute=0, tzinfo=jst),
            room="Hall A",
        )
        assert mapping1 is not None
        assert mapping1.video_id == "abc123"

        mapping2 = config.find_mapping(
            timeslot=datetime(year=2026, month=1, day=7, hour=11, minute=0, tzinfo=jst),
            room="Hall A",
        )
        assert mapping2 is not None
        assert mapping2.video_id == "def456"

        mapping3 = config.find_mapping(
            timeslot=datetime(year=2026, month=1, day=7, hour=10, minute=0, tzinfo=jst),
            room="Hall B",
        )
        assert mapping3 is not None
        assert mapping3.video_id == "ghi789"

    def test_read_file_not_found(self) -> None:
        """存在しないファイルはMappingFileErrorを発生"""
        reader = MappingFileReader()
        jst = ZoneInfo(key="Asia/Tokyo")

        with pytest.raises(expected_exception=MappingFileError, match="not found"):
            reader.read(file_path=Path("/nonexistent/file.yaml"), timezone=jst)

    def test_read_invalid_yaml_syntax(self, tmp_path: Path) -> None:
        """不正なYAML構文はMappingFileErrorを発生"""
        invalid_yaml = """
sessions:
  "2026-01-07":
    "Hall A"
      "10:00":  # インデントが不正
        video_id: "abc123"
"""
        jst = ZoneInfo(key="Asia/Tokyo")

        yaml_file = tmp_path / "invalid.yaml"
        yaml_file.write_text(data=invalid_yaml, encoding="utf-8")

        reader = MappingFileReader()
        with pytest.raises(
            expected_exception=MappingFileError, match="Invalid YAML syntax"
        ):
            reader.read(file_path=yaml_file, timezone=jst)

    def test_read_invalid_schema(self, tmp_path: Path) -> None:
        """スキーマ不一致はMappingFileErrorを発生"""
        invalid_schema = """
sessions:
  "2026-01-07":
    "Hall A":
      "10:00":
        wrong_field: "abc123"
"""
        jst = ZoneInfo(key="Asia/Tokyo")

        yaml_file = tmp_path / "invalid_schema.yaml"
        yaml_file.write_text(data=invalid_schema, encoding="utf-8")

        reader = MappingFileReader()
        with pytest.raises(
            expected_exception=MappingFileError, match="Invalid mapping file format"
        ):
            reader.read(file_path=yaml_file, timezone=jst)

    def test_read_unquoted_date_keys(self, tmp_path: Path) -> None:
        """クォートなしの日付キーでも正しく読み込める

        ruamel.yamlはクォートなしの日付(例: 2026-01-07)を
        datetime.dateオブジェクトに自動変換するため、
        parse_date_keysでその場合を処理する必要がある。
        """
        yaml_content = """
sessions:
  2026-01-07:
    Hall A:
      "10:00":
        video_id: "abc123"
"""
        jst = ZoneInfo(key="Asia/Tokyo")

        yaml_file = tmp_path / "unquoted_date.yaml"
        yaml_file.write_text(data=yaml_content, encoding="utf-8")

        reader = MappingFileReader()
        config = reader.read(file_path=yaml_file, timezone=jst)

        assert len(config.mappings) == 1
        mapping = config.find_mapping(
            timeslot=datetime(year=2026, month=1, day=7, hour=10, minute=0, tzinfo=jst),
            room="Hall A",
        )
        assert mapping is not None
        assert mapping.video_id == "abc123"

    def test_read_datetime_keys(self, tmp_path: Path) -> None:
        """datetime形式のキーでも正しく読み込める

        ruamel.yamlはdatetime形式(例: 2026-01-07T10:00:00)を
        TimeStamp(datetimeのサブクラス)に自動変換するため、
        parse_date_keysでdatetimeから日付部分を抽出する必要がある。
        """
        yaml_content = """
sessions:
  2026-01-07T00:00:00:
    Hall A:
      "10:00":
        video_id: "abc123"
"""
        jst = ZoneInfo(key="Asia/Tokyo")

        yaml_file = tmp_path / "datetime_key.yaml"
        yaml_file.write_text(data=yaml_content, encoding="utf-8")

        reader = MappingFileReader()
        config = reader.read(file_path=yaml_file, timezone=jst)

        assert len(config.mappings) == 1
        mapping = config.find_mapping(
            timeslot=datetime(year=2026, month=1, day=7, hour=10, minute=0, tzinfo=jst),
            room="Hall A",
        )
        assert mapping is not None
        assert mapping.video_id == "abc123"
