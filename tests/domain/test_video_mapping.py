"""VideoMapping エンティティのテスト"""

from datetime import UTC, datetime

from confengine_to_youtube.domain.schedule_slot import ScheduleSlot
from confengine_to_youtube.domain.video_mapping import MappingConfig, VideoMapping


class TestVideoMapping:
    """VideoMapping のテスト"""

    def test_create_video_mapping(self) -> None:
        """VideoMappingを作成できる"""
        slot = ScheduleSlot(
            timeslot=datetime(year=2026, month=1, day=7, hour=10, minute=0, tzinfo=UTC),
            room="Hall A",
        )
        mapping = VideoMapping(slot=slot, video_id="abc123")

        assert mapping.slot.timeslot == datetime(
            year=2026, month=1, day=7, hour=10, minute=0, tzinfo=UTC
        )
        assert mapping.slot.room == "Hall A"
        assert mapping.video_id == "abc123"


class TestMappingConfig:
    """MappingConfig のテスト"""

    def test_find_mapping_found(self) -> None:
        """マッピングが見つかる場合"""
        slot1 = ScheduleSlot(
            timeslot=datetime(year=2026, month=1, day=7, hour=10, minute=0, tzinfo=UTC),
            room="Hall A",
        )
        slot2 = ScheduleSlot(
            timeslot=datetime(year=2026, month=1, day=7, hour=11, minute=0, tzinfo=UTC),
            room="Hall A",
        )
        mappings = [
            VideoMapping(slot=slot1, video_id="abc123"),
            VideoMapping(slot=slot2, video_id="def456"),
        ]
        config = MappingConfig(mappings=mappings, hashtags=(), footer="")

        search_slot = ScheduleSlot(
            timeslot=datetime(year=2026, month=1, day=7, hour=10, minute=0, tzinfo=UTC),
            room="Hall A",
        )
        result = config.find_mapping(slot=search_slot)

        assert result is not None
        assert result.video_id == "abc123"

    def test_find_mapping_not_found(self) -> None:
        """マッピングが見つからない場合"""
        slot = ScheduleSlot(
            timeslot=datetime(year=2026, month=1, day=7, hour=10, minute=0, tzinfo=UTC),
            room="Hall A",
        )
        mappings = [VideoMapping(slot=slot, video_id="abc123")]
        config = MappingConfig(mappings=mappings, hashtags=(), footer="")

        search_slot = ScheduleSlot(
            timeslot=datetime(year=2026, month=1, day=8, hour=14, minute=0, tzinfo=UTC),
            room="Hall B",
        )
        result = config.find_mapping(slot=search_slot)

        assert result is None

    def test_find_unused(self) -> None:
        """未使用のマッピングを取得できる"""
        slot1 = ScheduleSlot(
            timeslot=datetime(year=2026, month=1, day=7, hour=10, minute=0, tzinfo=UTC),
            room="Hall A",
        )
        slot2 = ScheduleSlot(
            timeslot=datetime(year=2026, month=1, day=7, hour=11, minute=0, tzinfo=UTC),
            room="Hall A",
        )
        slot3 = ScheduleSlot(
            timeslot=datetime(year=2026, month=1, day=7, hour=10, minute=0, tzinfo=UTC),
            room="Hall B",
        )
        mappings = [
            VideoMapping(slot=slot1, video_id="abc123"),
            VideoMapping(slot=slot2, video_id="def456"),
            VideoMapping(slot=slot3, video_id="ghi789"),
        ]
        config = MappingConfig(mappings=mappings, hashtags=(), footer="")

        # 1つだけ使用
        used_slots = {
            ScheduleSlot(
                timeslot=datetime(
                    year=2026, month=1, day=7, hour=10, minute=0, tzinfo=UTC
                ),
                room="Hall A",
            )
        }
        unused = config.find_unused(used_slots=used_slots)

        assert len(unused) == 2
        assert unused[0].video_id == "def456"
        assert unused[1].video_id == "ghi789"

    def test_create_with_hashtags(self) -> None:
        """hashtagsを指定してMappingConfigを作成できる"""
        config = MappingConfig(
            mappings=[],
            hashtags=("#RSGT2026", "#Agile", "#Scrum"),
            footer="",
        )

        assert config.hashtags == ("#RSGT2026", "#Agile", "#Scrum")
