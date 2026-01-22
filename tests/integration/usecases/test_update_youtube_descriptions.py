from datetime import datetime
from pathlib import Path
from unittest.mock import create_autospec
from zoneinfo import ZoneInfo

import pytest

from confengine_to_youtube.adapters.mapping_file_reader import MappingFileReader
from confengine_to_youtube.adapters.youtube_api import YouTubeApiGateway
from confengine_to_youtube.domain.session import Session
from confengine_to_youtube.usecases.protocols import (
    ConfEngineApiProtocol,
    VideoInfo,
    YouTubeApiProtocol,
)
from confengine_to_youtube.usecases.update_youtube_descriptions import (
    UpdateYouTubeDescriptionsUseCase,
)
from tests.conftest import create_session, write_yaml_file
from tests.integration.usecases.conftest import create_mock_confengine_api


class TestUpdateYouTubeDescriptionsUseCase:
    """UpdateYouTubeDescriptionsUseCase のテスト"""

    @pytest.fixture
    def sessions(self, jst: ZoneInfo) -> tuple[Session, ...]:
        return (
            create_session(
                title="Session 1",
                speakers=[("Speaker", "A")],
                abstract="Abstract 1",
                timeslot=datetime(
                    year=2026,
                    month=1,
                    day=7,
                    hour=10,
                    minute=0,
                    tzinfo=jst,
                ),
                room="Hall A",
                url="https://example.com/1",
            ),
            create_session(
                title="Session 2",
                speakers=[("Speaker", "B")],
                abstract="Abstract 2",
                timeslot=datetime(
                    year=2026,
                    month=1,
                    day=7,
                    hour=11,
                    minute=0,
                    tzinfo=jst,
                ),
                room="Hall A",
                url="https://example.com/2",
            ),
        )

    @pytest.fixture
    def mapping_file(self, tmp_path: Path) -> Path:
        """テスト用マッピングファイル"""
        yaml_content = """
conf_id: test-conf
sessions:
  "2026-01-07":
    "Hall A":
      "10:00":
        video_id: "video1"
      "11:00":
        video_id: "video2"
"""
        return write_yaml_file(
            tmp_path=tmp_path,
            content=yaml_content,
            filename="mapping.yaml",
        )

    @pytest.fixture
    def mock_confengine_api(
        self,
        sessions: tuple[Session, ...],
        jst: ZoneInfo,
    ) -> ConfEngineApiProtocol:
        return create_mock_confengine_api(sessions=sessions, timezone=jst)

    @pytest.fixture
    def mock_youtube_api(self) -> YouTubeApiProtocol:
        """モックYouTube API"""
        mock = create_autospec(YouTubeApiGateway, spec_set=True)
        mock.get_video_info.side_effect = lambda video_id: VideoInfo(
            video_id=video_id,
            title=f"Title for {video_id}",
            description=f"Description for {video_id}",
            category_id=28,
        )
        return mock  # type: ignore[no-any-return]

    @pytest.fixture
    def usecase(
        self,
        mock_confengine_api: ConfEngineApiProtocol,
        mock_youtube_api: YouTubeApiProtocol,
        mapping_reader: MappingFileReader,
    ) -> UpdateYouTubeDescriptionsUseCase:
        """テスト用ユースケース"""
        return UpdateYouTubeDescriptionsUseCase(
            confengine_api=mock_confengine_api,
            mapping_reader=mapping_reader,
            youtube_api=mock_youtube_api,
        )

    def test_execute_dry_run(
        self,
        usecase: UpdateYouTubeDescriptionsUseCase,
        mapping_file: Path,
        mock_confengine_api: ConfEngineApiProtocol,
    ) -> None:
        """dry-runモードでプレビューを返す"""
        result = usecase.execute(
            mapping_file=mapping_file,
            dry_run=True,
        )

        assert result.is_dry_run is True
        assert result.updated_count == 0
        assert len(result.previews) == 2

        # ConfEngine APIが呼ばれたことを検証
        mock_confengine_api.fetch_sessions.assert_called_once()  # type: ignore[attr-defined]

        # プレビューの内容を確認
        preview1 = result.previews[0]
        assert preview1.video_id == "video1"
        expected_description = (
            "Speaker: Speaker A\n\nAbstract 1\n\n***\n\nhttps://example.com/1\n\n***"
        )
        assert preview1.new_description == expected_description

    def test_execute_update(
        self,
        usecase: UpdateYouTubeDescriptionsUseCase,
        mapping_file: Path,
        mock_youtube_api: YouTubeApiProtocol,
    ) -> None:
        """更新モードで動画を更新する"""
        result = usecase.execute(
            mapping_file=mapping_file,
            dry_run=False,
        )

        assert result.is_dry_run is False
        assert result.updated_count == 2
        assert result.no_content_count == 0
        assert result.no_mapping_count == 0

        # YouTube APIが呼ばれたことを確認
        assert mock_youtube_api.update_video.call_count == 2  # type: ignore[attr-defined]

    def test_execute_skips_empty_sessions(
        self,
        mock_youtube_api: YouTubeApiProtocol,
        mapping_file: Path,
        mapping_reader: MappingFileReader,
        jst: ZoneInfo,
    ) -> None:
        """abstractが空のセッションはスキップする"""
        empty_session = create_session(
            title="Empty Session",
            speakers=[],
            abstract="",
            timeslot=datetime(year=2026, month=1, day=7, hour=10, minute=0, tzinfo=jst),
            room="Hall A",
            url="https://example.com/empty",
        )
        mock_confengine_api = create_mock_confengine_api(
            sessions=(empty_session,),
            timezone=jst,
        )

        usecase = UpdateYouTubeDescriptionsUseCase(
            confengine_api=mock_confengine_api,
            mapping_reader=mapping_reader,
            youtube_api=mock_youtube_api,
        )

        result = usecase.execute(
            mapping_file=mapping_file,
            dry_run=False,
        )

        assert result.updated_count == 0
        assert result.no_content_count == 1

    def test_execute_skips_unmapped_sessions(
        self,
        mock_youtube_api: YouTubeApiProtocol,
        tmp_path: Path,
        mapping_reader: MappingFileReader,
        jst: ZoneInfo,
    ) -> None:
        """マッピングがないセッションはスキップする"""
        unmapped_session = create_session(
            title="Unmapped Session",
            speakers=[("", "Speaker")],
            abstract="Content",
            timeslot=datetime(year=2026, month=1, day=8, hour=14, minute=0, tzinfo=jst),
            room="Hall C",
            url="https://example.com/unmapped",
        )
        mock_confengine_api = create_mock_confengine_api(
            sessions=(unmapped_session,),
            timezone=jst,
        )

        # 空のマッピングファイル
        yaml_content = """
conf_id: test-conf
sessions: {}
"""
        mapping_file = write_yaml_file(
            tmp_path=tmp_path,
            content=yaml_content,
            filename="empty_mapping.yaml",
        )

        usecase = UpdateYouTubeDescriptionsUseCase(
            confengine_api=mock_confengine_api,
            mapping_reader=mapping_reader,
            youtube_api=mock_youtube_api,
        )

        result = usecase.execute(
            mapping_file=mapping_file,
            dry_run=False,
        )

        assert result.updated_count == 0
        assert result.no_mapping_count == 1

    def test_execute_warns_unused_mappings(
        self,
        mock_youtube_api: YouTubeApiProtocol,
        tmp_path: Path,
        mapping_reader: MappingFileReader,
        jst: ZoneInfo,
    ) -> None:
        """マッピングにあるがConfEngineにないセッションは未使用として警告する"""
        session = create_session(
            title="Session 1",
            speakers=[("", "Speaker")],
            abstract="Content",
            timeslot=datetime(year=2026, month=1, day=7, hour=10, minute=0, tzinfo=jst),
            room="Hall A",
            url="https://example.com/1",
        )
        mock_confengine_api = create_mock_confengine_api(
            sessions=(session,),
            timezone=jst,
        )

        # マッピングには2セッション (1つは使われない)
        yaml_content = """
conf_id: test-conf
sessions:
  "2026-01-07":
    "Hall A":
      "10:00":
        video_id: "video1"
      "14:00":
        video_id: "video_unused"
"""
        mapping_file = write_yaml_file(
            tmp_path=tmp_path,
            content=yaml_content,
            filename="unused_mapping.yaml",
        )

        usecase = UpdateYouTubeDescriptionsUseCase(
            confengine_api=mock_confengine_api,
            mapping_reader=mapping_reader,
            youtube_api=mock_youtube_api,
        )

        result = usecase.execute(
            mapping_file=mapping_file,
            dry_run=False,
        )

        assert result.updated_count == 1
        assert result.unused_mappings_count == 1

    def test_execute_with_hashtags_in_mapping(
        self,
        mock_youtube_api: YouTubeApiProtocol,
        tmp_path: Path,
        mapping_reader: MappingFileReader,
        jst: ZoneInfo,
    ) -> None:
        """マッピングファイルにhashtagsがある場合、descriptionに含まれる"""
        session = create_session(
            title="Session 1",
            speakers=[("Speaker", "A")],
            abstract="Abstract 1",
            timeslot=datetime(year=2026, month=1, day=7, hour=10, minute=0, tzinfo=jst),
            room="Hall A",
            url="https://example.com/1",
        )
        mock_confengine_api = create_mock_confengine_api(
            sessions=(session,),
            timezone=jst,
        )

        yaml_content = """
conf_id: test-conf
hashtags:
  - "#RSGT2026"
  - "#Agile"
  - "#Scrum"
sessions:
  "2026-01-07":
    "Hall A":
      "10:00":
        video_id: "video1"
"""
        mapping_file = write_yaml_file(
            tmp_path=tmp_path,
            content=yaml_content,
            filename="mapping_with_hashtags.yaml",
        )

        usecase = UpdateYouTubeDescriptionsUseCase(
            confengine_api=mock_confengine_api,
            mapping_reader=mapping_reader,
            youtube_api=mock_youtube_api,
        )

        result = usecase.execute(
            mapping_file=mapping_file,
            dry_run=True,
        )

        assert len(result.previews) == 1
        expected_description = (
            "Speaker: Speaker A\n\n"
            "Abstract 1\n\n"
            "***\n\n"
            "https://example.com/1\n\n"
            "#RSGT2026 #Agile #Scrum\n\n"
            "***"
        )
        assert result.previews[0].new_description == expected_description
