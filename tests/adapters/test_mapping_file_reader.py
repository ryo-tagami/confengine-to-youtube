from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

from confengine_to_youtube.adapters.mapping_file_reader import MappingFileReader
from confengine_to_youtube.domain.schedule_slot import ScheduleSlot
from confengine_to_youtube.usecases.protocols import MappingFileError


class TestMappingFileReader:
    def test_read(self, tmp_path: Path) -> None:
        yaml_content = """
conf_id: test-conf
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
        mapping = reader.read(file_path=yaml_file)

        assert mapping.conf_id == "test-conf"

        config = mapping.to_domain(timezone=jst)

        assert len(config.mappings) == 3

        slot1 = ScheduleSlot(
            timeslot=datetime(year=2026, month=1, day=7, hour=10, minute=0, tzinfo=jst),
            room="Hall A",
        )
        mapping1 = config.find_mapping(slot=slot1)
        assert mapping1 is not None
        assert mapping1.video_id == "abc123"

        slot2 = ScheduleSlot(
            timeslot=datetime(year=2026, month=1, day=7, hour=11, minute=0, tzinfo=jst),
            room="Hall A",
        )
        mapping2 = config.find_mapping(slot=slot2)
        assert mapping2 is not None
        assert mapping2.video_id == "def456"

        slot3 = ScheduleSlot(
            timeslot=datetime(year=2026, month=1, day=7, hour=10, minute=0, tzinfo=jst),
            room="Hall B",
        )
        mapping3 = config.find_mapping(slot=slot3)
        assert mapping3 is not None
        assert mapping3.video_id == "ghi789"

    def test_read_file_not_found(self) -> None:
        """存在しないファイルはMappingFileErrorを発生"""
        reader = MappingFileReader()

        with pytest.raises(expected_exception=MappingFileError, match="not found"):
            reader.read(file_path=Path("/nonexistent/file.yaml"))

    def test_read_invalid_yaml_syntax(self, tmp_path: Path) -> None:
        """不正なYAML構文はMappingFileErrorを発生"""
        invalid_yaml = """
conf_id: test-conf
sessions:
  "2026-01-07":
    "Hall A"
      "10:00":  # インデントが不正
        video_id: "abc123"
"""
        yaml_file = tmp_path / "invalid.yaml"
        yaml_file.write_text(data=invalid_yaml, encoding="utf-8")

        reader = MappingFileReader()
        with pytest.raises(
            expected_exception=MappingFileError, match="Invalid YAML syntax"
        ):
            reader.read(file_path=yaml_file)

    def test_read_invalid_schema(self, tmp_path: Path) -> None:
        """スキーマ不一致はMappingFileErrorを発生"""
        invalid_schema = """
conf_id: test-conf
sessions:
  "2026-01-07":
    "Hall A":
      "10:00":
        wrong_field: "abc123"
"""
        yaml_file = tmp_path / "invalid_schema.yaml"
        yaml_file.write_text(data=invalid_schema, encoding="utf-8")

        reader = MappingFileReader()
        with pytest.raises(
            expected_exception=MappingFileError, match="Invalid mapping file format"
        ):
            reader.read(file_path=yaml_file)

    def test_read_missing_conf_id(self, tmp_path: Path) -> None:
        """conf_idがないYAMLファイルはMappingFileErrorを発生"""
        missing_conf_id = """
sessions:
  "2026-01-07":
    "Hall A":
      "10:00":
        video_id: "abc123"
"""
        yaml_file = tmp_path / "missing_conf_id.yaml"
        yaml_file.write_text(data=missing_conf_id, encoding="utf-8")

        reader = MappingFileReader()
        with pytest.raises(
            expected_exception=MappingFileError, match="Invalid mapping file format"
        ):
            reader.read(file_path=yaml_file)

    def test_read_unquoted_date_keys(self, tmp_path: Path) -> None:
        """クォートなしの日付キーでも正しく読み込める

        ruamel.yamlはクォートなしの日付(例: 2026-01-07)を
        datetime.dateオブジェクトに自動変換するため、
        parse_date_keysでその場合を処理する必要がある。
        """
        yaml_content = """
conf_id: test-conf
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
        mapping = reader.read(file_path=yaml_file)
        config = mapping.to_domain(timezone=jst)

        assert len(config.mappings) == 1
        slot = ScheduleSlot(
            timeslot=datetime(year=2026, month=1, day=7, hour=10, minute=0, tzinfo=jst),
            room="Hall A",
        )
        video_mapping = config.find_mapping(slot=slot)
        assert video_mapping is not None
        assert video_mapping.video_id == "abc123"

    def test_read_datetime_keys(self, tmp_path: Path) -> None:
        """datetime形式のキーでも正しく読み込める

        ruamel.yamlはdatetime形式(例: 2026-01-07T10:00:00)を
        TimeStamp(datetimeのサブクラス)に自動変換するため、
        parse_date_keysでdatetimeから日付部分を抽出する必要がある。
        """
        yaml_content = """
conf_id: test-conf
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
        mapping = reader.read(file_path=yaml_file)
        config = mapping.to_domain(timezone=jst)

        assert len(config.mappings) == 1
        slot = ScheduleSlot(
            timeslot=datetime(year=2026, month=1, day=7, hour=10, minute=0, tzinfo=jst),
            room="Hall A",
        )
        video_mapping = config.find_mapping(slot=slot)
        assert video_mapping is not None
        assert video_mapping.video_id == "abc123"

    def test_read_with_hashtags(self, tmp_path: Path) -> None:
        """hashtagsフィールドを含むYAMLファイルを読み込める"""
        yaml_content = """
conf_id: test-conf
hashtags:
  - "#RSGT2026"
  - "#Agile"
  - "#Scrum"
sessions:
  2026-01-07:
    Hall A:
      "10:00":
        video_id: "abc123"
"""
        jst = ZoneInfo(key="Asia/Tokyo")

        yaml_file = tmp_path / "with_hashtags.yaml"
        yaml_file.write_text(data=yaml_content, encoding="utf-8")

        reader = MappingFileReader()
        mapping = reader.read(file_path=yaml_file)
        config = mapping.to_domain(timezone=jst)

        assert config.hashtags == ("#RSGT2026", "#Agile", "#Scrum")
        assert len(config.mappings) == 1

    def test_read_without_hashtags_defaults_to_empty(self, tmp_path: Path) -> None:
        """hashtagsフィールドがないYAMLファイルでもエラーにならない"""
        yaml_content = """
conf_id: test-conf
sessions:
  2026-01-07:
    Hall A:
      "10:00":
        video_id: "abc123"
"""
        jst = ZoneInfo(key="Asia/Tokyo")

        yaml_file = tmp_path / "without_hashtags.yaml"
        yaml_file.write_text(data=yaml_content, encoding="utf-8")

        reader = MappingFileReader()
        mapping = reader.read(file_path=yaml_file)
        config = mapping.to_domain(timezone=jst)

        assert config.hashtags == ()
        assert len(config.mappings) == 1

    def test_read_with_footer(self, tmp_path: Path) -> None:
        """footerフィールドを含むYAMLファイルを読み込める"""
        yaml_content = """
conf_id: test-conf
footer: |
  Please subscribe to our channel!
  https://example.com
sessions:
  2026-01-07:
    Hall A:
      "10:00":
        video_id: "abc123"
"""
        jst = ZoneInfo(key="Asia/Tokyo")

        yaml_file = tmp_path / "with_footer.yaml"
        yaml_file.write_text(data=yaml_content, encoding="utf-8")

        reader = MappingFileReader()
        mapping = reader.read(file_path=yaml_file)
        config = mapping.to_domain(timezone=jst)

        assert (
            config.footer == "Please subscribe to our channel!\nhttps://example.com\n"
        )
        assert len(config.mappings) == 1

    def test_read_without_footer_defaults_to_empty(self, tmp_path: Path) -> None:
        """footerフィールドがないYAMLファイルでもエラーにならない"""
        yaml_content = """
conf_id: test-conf
sessions:
  2026-01-07:
    Hall A:
      "10:00":
        video_id: "abc123"
"""
        jst = ZoneInfo(key="Asia/Tokyo")

        yaml_file = tmp_path / "without_footer.yaml"
        yaml_file.write_text(data=yaml_content, encoding="utf-8")

        reader = MappingFileReader()
        mapping = reader.read(file_path=yaml_file)
        config = mapping.to_domain(timezone=jst)

        assert config.footer == ""
        assert len(config.mappings) == 1
