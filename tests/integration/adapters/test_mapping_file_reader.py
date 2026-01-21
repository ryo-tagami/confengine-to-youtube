from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

from confengine_to_youtube.adapters.mapping_file_reader import MappingFileReader
from confengine_to_youtube.domain.schedule_slot import ScheduleSlot
from confengine_to_youtube.usecases.protocols import MappingFileError
from tests.conftest import write_yaml_file


class TestMappingFileReader:
    _YAML_CONTENT = """
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

    @pytest.mark.parametrize(
        ("hour", "room", "expected_video_id"),
        [
            (10, "Hall A", "abc123"),
            (11, "Hall A", "def456"),
            (10, "Hall B", "ghi789"),
        ],
    )
    def test_read(
        self,
        tmp_path: Path,
        jst: ZoneInfo,
        hour: int,
        room: str,
        expected_video_id: str,
    ) -> None:
        """YAMLファイルを正しく読み込める"""
        yaml_file = write_yaml_file(
            tmp_path=tmp_path,
            content=self._YAML_CONTENT,
            filename="mapping.yaml",
        )

        reader = MappingFileReader()
        mapping = reader.read(file_path=yaml_file)

        assert mapping.conf_id == "test-conf"

        config = mapping.to_domain(timezone=jst)

        assert len(config.mappings) == 3

        slot = ScheduleSlot(
            timeslot=datetime(
                year=2026,
                month=1,
                day=7,
                hour=hour,
                minute=0,
                tzinfo=jst,
            ),
            room=room,
        )
        video_mapping = config.find_mapping(slot=slot)
        assert video_mapping is not None
        assert video_mapping.video_id == expected_video_id

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
        yaml_file = write_yaml_file(
            tmp_path=tmp_path,
            content=invalid_yaml,
            filename="invalid.yaml",
        )

        reader = MappingFileReader()
        with pytest.raises(
            expected_exception=MappingFileError,
            match="Invalid YAML syntax",
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
        yaml_file = write_yaml_file(
            tmp_path=tmp_path,
            content=invalid_schema,
            filename="invalid_schema.yaml",
        )

        reader = MappingFileReader()
        with pytest.raises(
            expected_exception=MappingFileError,
            match="Invalid mapping file format",
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
        yaml_file = write_yaml_file(
            tmp_path=tmp_path,
            content=missing_conf_id,
            filename="missing_conf_id.yaml",
        )

        reader = MappingFileReader()
        with pytest.raises(
            expected_exception=MappingFileError,
            match="Invalid mapping file format",
        ):
            reader.read(file_path=yaml_file)

    def test_read_unquoted_date_keys(self, tmp_path: Path, jst: ZoneInfo) -> None:
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
        yaml_file = write_yaml_file(
            tmp_path=tmp_path,
            content=yaml_content,
            filename="unquoted_date.yaml",
        )

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

    def test_read_datetime_keys(self, tmp_path: Path, jst: ZoneInfo) -> None:
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
        yaml_file = write_yaml_file(
            tmp_path=tmp_path,
            content=yaml_content,
            filename="datetime_key.yaml",
        )

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

    def test_read_with_hashtags(self, tmp_path: Path, jst: ZoneInfo) -> None:
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
        yaml_file = write_yaml_file(
            tmp_path=tmp_path,
            content=yaml_content,
            filename="with_hashtags.yaml",
        )

        reader = MappingFileReader()
        mapping = reader.read(file_path=yaml_file)
        config = mapping.to_domain(timezone=jst)

        assert config.hashtags == ("#RSGT2026", "#Agile", "#Scrum")
        assert len(config.mappings) == 1

    def test_read_without_hashtags_defaults_to_empty(
        self,
        tmp_path: Path,
        jst: ZoneInfo,
    ) -> None:
        """hashtagsフィールドがないYAMLファイルでもエラーにならない"""
        yaml_content = """
conf_id: test-conf
sessions:
  2026-01-07:
    Hall A:
      "10:00":
        video_id: "abc123"
"""
        yaml_file = write_yaml_file(
            tmp_path=tmp_path,
            content=yaml_content,
            filename="without_hashtags.yaml",
        )

        reader = MappingFileReader()
        mapping = reader.read(file_path=yaml_file)
        config = mapping.to_domain(timezone=jst)

        assert config.hashtags == ()
        assert len(config.mappings) == 1

    def test_read_with_footer(self, tmp_path: Path, jst: ZoneInfo) -> None:
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
        yaml_file = write_yaml_file(
            tmp_path=tmp_path,
            content=yaml_content,
            filename="with_footer.yaml",
        )

        reader = MappingFileReader()
        mapping = reader.read(file_path=yaml_file)
        config = mapping.to_domain(timezone=jst)

        assert (
            config.footer == "Please subscribe to our channel!\nhttps://example.com\n"
        )
        assert len(config.mappings) == 1

    def test_read_without_footer_defaults_to_empty(
        self,
        tmp_path: Path,
        jst: ZoneInfo,
    ) -> None:
        """footerフィールドがないYAMLファイルでもエラーにならない"""
        yaml_content = """
conf_id: test-conf
sessions:
  2026-01-07:
    Hall A:
      "10:00":
        video_id: "abc123"
"""
        yaml_file = write_yaml_file(
            tmp_path=tmp_path,
            content=yaml_content,
            filename="without_footer.yaml",
        )

        reader = MappingFileReader()
        mapping = reader.read(file_path=yaml_file)
        config = mapping.to_domain(timezone=jst)

        assert config.footer == ""
        assert len(config.mappings) == 1
