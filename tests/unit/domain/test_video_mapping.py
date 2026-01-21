"""VideoMapping エンティティのテスト"""

from datetime import UTC, datetime

import pytest
from returns.pipeline import is_successful

from confengine_to_youtube.domain.schedule_slot import ScheduleSlot
from confengine_to_youtube.domain.video_mapping import MappingConfig, VideoMapping


class TestVideoMapping:
    """VideoMapping のテスト"""

    def test_direct_instantiation_raises_error(self) -> None:
        """直接インスタンス化するとエラーになる"""
        slot = ScheduleSlot.create(
            timeslot=datetime(year=2026, month=1, day=7, hour=10, minute=0, tzinfo=UTC),
            room="Hall A",
        ).unwrap()
        with pytest.raises(
            TypeError,
            match="VideoMapping cannot be instantiated directly",
        ):
            VideoMapping(slot=slot, video_id="abc123")

    def test_create_success(self) -> None:
        """createメソッドでインスタンスを作成できる"""
        slot = ScheduleSlot.create(
            timeslot=datetime(year=2026, month=1, day=7, hour=10, minute=0, tzinfo=UTC),
            room="Hall A",
        ).unwrap()
        result = VideoMapping.create(slot=slot, video_id="abc123")
        assert is_successful(result)
        mapping = result.unwrap()
        assert mapping.slot == slot
        assert mapping.video_id == "abc123"

    def test_create_video_mapping(self) -> None:
        """VideoMappingを作成できる"""
        slot = ScheduleSlot.create(
            timeslot=datetime(year=2026, month=1, day=7, hour=10, minute=0, tzinfo=UTC),
            room="Hall A",
        ).unwrap()
        mapping = VideoMapping.create(slot=slot, video_id="abc123").unwrap()

        assert mapping.slot.timeslot == datetime(
            year=2026,
            month=1,
            day=7,
            hour=10,
            minute=0,
            tzinfo=UTC,
        )
        assert mapping.slot.room == "Hall A"
        assert mapping.video_id == "abc123"


class TestMappingConfig:
    """MappingConfig のテスト"""

    def test_direct_instantiation_raises_error(self) -> None:
        """直接インスタンス化するとエラーになる"""
        with pytest.raises(
            TypeError,
            match="MappingConfig cannot be instantiated directly",
        ):
            MappingConfig(
                conf_id="test-conf",
                mappings=frozenset(),
                hashtags=(),
                footer="",
            )

    def test_create_success(self) -> None:
        """createメソッドでインスタンスを作成できる"""
        result = MappingConfig.create(
            conf_id="test-conf",
            mappings=frozenset(),
            hashtags=(),
            footer="",
        )
        assert is_successful(result)
        config = result.unwrap()
        assert config.conf_id == "test-conf"

    def test_find_mapping_found(self) -> None:
        """マッピングが見つかる場合"""
        slot1 = ScheduleSlot.create(
            timeslot=datetime(year=2026, month=1, day=7, hour=10, minute=0, tzinfo=UTC),
            room="Hall A",
        ).unwrap()
        slot2 = ScheduleSlot.create(
            timeslot=datetime(year=2026, month=1, day=7, hour=11, minute=0, tzinfo=UTC),
            room="Hall A",
        ).unwrap()
        mappings = frozenset(
            {
                VideoMapping.create(slot=slot1, video_id="abc123").unwrap(),
                VideoMapping.create(slot=slot2, video_id="def456").unwrap(),
            },
        )
        config = MappingConfig.create(
            conf_id="test-conf",
            mappings=mappings,
            hashtags=(),
            footer="",
        ).unwrap()

        search_slot = ScheduleSlot.create(
            timeslot=datetime(year=2026, month=1, day=7, hour=10, minute=0, tzinfo=UTC),
            room="Hall A",
        ).unwrap()
        result = config.find_mapping(slot=search_slot)

        assert result is not None
        assert result.video_id == "abc123"

    def test_find_mapping_not_found(self) -> None:
        """マッピングが見つからない場合"""
        slot = ScheduleSlot.create(
            timeslot=datetime(year=2026, month=1, day=7, hour=10, minute=0, tzinfo=UTC),
            room="Hall A",
        ).unwrap()
        mappings = frozenset(
            {VideoMapping.create(slot=slot, video_id="abc123").unwrap()},
        )
        config = MappingConfig.create(
            conf_id="test-conf",
            mappings=mappings,
            hashtags=(),
            footer="",
        ).unwrap()

        search_slot = ScheduleSlot.create(
            timeslot=datetime(year=2026, month=1, day=8, hour=14, minute=0, tzinfo=UTC),
            room="Hall B",
        ).unwrap()
        result = config.find_mapping(slot=search_slot)

        assert result is None

    def test_find_unused(self) -> None:
        """未使用のマッピングを取得できる"""
        slot1 = ScheduleSlot.create(
            timeslot=datetime(year=2026, month=1, day=7, hour=10, minute=0, tzinfo=UTC),
            room="Hall A",
        ).unwrap()
        slot2 = ScheduleSlot.create(
            timeslot=datetime(year=2026, month=1, day=7, hour=11, minute=0, tzinfo=UTC),
            room="Hall A",
        ).unwrap()
        slot3 = ScheduleSlot.create(
            timeslot=datetime(year=2026, month=1, day=7, hour=10, minute=0, tzinfo=UTC),
            room="Hall B",
        ).unwrap()
        mappings = frozenset(
            {
                VideoMapping.create(slot=slot1, video_id="abc123").unwrap(),
                VideoMapping.create(slot=slot2, video_id="def456").unwrap(),
                VideoMapping.create(slot=slot3, video_id="ghi789").unwrap(),
            },
        )
        config = MappingConfig.create(
            conf_id="test-conf",
            mappings=mappings,
            hashtags=(),
            footer="",
        ).unwrap()

        # 1つだけ使用
        used_slots = {
            ScheduleSlot.create(
                timeslot=datetime(
                    year=2026,
                    month=1,
                    day=7,
                    hour=10,
                    minute=0,
                    tzinfo=UTC,
                ),
                room="Hall A",
            ).unwrap(),
        }
        unused = config.find_unused(used_slots=used_slots)

        assert len(unused) == 2
        assert {m.video_id for m in unused} == {"def456", "ghi789"}

    def test_create_with_hashtags(self) -> None:
        """hashtagsを指定してMappingConfigを作成できる"""
        config = MappingConfig.create(
            conf_id="test-conf",
            mappings=frozenset(),
            hashtags=("#RSGT2026", "#Agile", "#Scrum"),
            footer="",
        ).unwrap()

        assert config.hashtags == ("#RSGT2026", "#Agile", "#Scrum")
