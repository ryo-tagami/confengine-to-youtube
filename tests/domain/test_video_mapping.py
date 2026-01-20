"""VideoMapping エンティティのテスト"""

from datetime import UTC, datetime

from confengine_to_youtube.domain.video_mapping import MappingConfig, VideoMapping


class TestVideoMapping:
    """VideoMapping のテスト"""

    def test_create_video_mapping(self) -> None:
        """VideoMappingを作成できる"""
        mapping = VideoMapping(
            timeslot=datetime(year=2026, month=1, day=7, hour=10, minute=0, tzinfo=UTC),
            room="Hall A",
            video_id="abc123",
        )

        assert mapping.timeslot == datetime(
            year=2026, month=1, day=7, hour=10, minute=0, tzinfo=UTC
        )
        assert mapping.room == "Hall A"
        assert mapping.video_id == "abc123"


class TestMappingConfig:
    """MappingConfig のテスト"""

    def test_find_mapping_found(self) -> None:
        """マッピングが見つかる場合"""
        mappings = [
            VideoMapping(
                timeslot=datetime(
                    year=2026, month=1, day=7, hour=10, minute=0, tzinfo=UTC
                ),
                room="Hall A",
                video_id="abc123",
            ),
            VideoMapping(
                timeslot=datetime(
                    year=2026, month=1, day=7, hour=11, minute=0, tzinfo=UTC
                ),
                room="Hall A",
                video_id="def456",
            ),
        ]
        config = MappingConfig(mappings=mappings, hashtags=())

        result = config.find_mapping(
            timeslot=datetime(year=2026, month=1, day=7, hour=10, minute=0, tzinfo=UTC),
            room="Hall A",
        )

        assert result is not None
        assert result.video_id == "abc123"

    def test_find_mapping_not_found(self) -> None:
        """マッピングが見つからない場合"""
        mappings = [
            VideoMapping(
                timeslot=datetime(
                    year=2026, month=1, day=7, hour=10, minute=0, tzinfo=UTC
                ),
                room="Hall A",
                video_id="abc123",
            ),
        ]
        config = MappingConfig(mappings=mappings, hashtags=())

        result = config.find_mapping(
            timeslot=datetime(year=2026, month=1, day=8, hour=14, minute=0, tzinfo=UTC),
            room="Hall B",
        )

        assert result is None

    def test_find_unused(self) -> None:
        """未使用のマッピングを取得できる"""
        mappings = [
            VideoMapping(
                timeslot=datetime(
                    year=2026, month=1, day=7, hour=10, minute=0, tzinfo=UTC
                ),
                room="Hall A",
                video_id="abc123",
            ),
            VideoMapping(
                timeslot=datetime(
                    year=2026, month=1, day=7, hour=11, minute=0, tzinfo=UTC
                ),
                room="Hall A",
                video_id="def456",
            ),
            VideoMapping(
                timeslot=datetime(
                    year=2026, month=1, day=7, hour=10, minute=0, tzinfo=UTC
                ),
                room="Hall B",
                video_id="ghi789",
            ),
        ]
        config = MappingConfig(mappings=mappings, hashtags=())

        # 1つだけ使用
        used_keys = {
            (
                datetime(year=2026, month=1, day=7, hour=10, minute=0, tzinfo=UTC),
                "Hall A",
            )
        }
        unused = config.find_unused(used_keys=used_keys)

        assert len(unused) == 2
        assert unused[0].video_id == "def456"
        assert unused[1].video_id == "ghi789"

    def test_create_with_hashtags(self) -> None:
        """hashtagsを指定してMappingConfigを作成できる"""
        config = MappingConfig(
            mappings=[],
            hashtags=("#RSGT2026", "#Agile", "#Scrum"),
        )

        assert config.hashtags == ("#RSGT2026", "#Agile", "#Scrum")
