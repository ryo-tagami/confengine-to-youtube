from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock
from zoneinfo import ZoneInfo

import pytest

from confengine_to_youtube.adapters.mapping_file_reader import MappingFileReader
from confengine_to_youtube.adapters.youtube_api import YouTubeApiGateway
from confengine_to_youtube.adapters.youtube_description_builder import (
    YouTubeDescriptionBuilder,
)
from confengine_to_youtube.adapters.youtube_title_builder import YouTubeTitleBuilder
from confengine_to_youtube.domain.abstract_markdown import AbstractMarkdown
from confengine_to_youtube.domain.schedule_slot import ScheduleSlot
from confengine_to_youtube.domain.session import Session, Speaker
from confengine_to_youtube.usecases.dto import YouTubeUpdateResult
from confengine_to_youtube.usecases.protocols import VideoInfo, YouTubeApiError
from confengine_to_youtube.usecases.update_youtube_descriptions import (
    UpdateYouTubeDescriptionsUseCase,
)

JST = ZoneInfo(key="Asia/Tokyo")


class TestUpdateYouTubeDescriptionsUseCase:
    """UpdateYouTubeDescriptionsUseCase のテスト"""

    @pytest.fixture
    def sessions(self) -> list[Session]:
        return [
            Session(
                slot=ScheduleSlot(
                    timeslot=datetime(
                        year=2026, month=1, day=7, hour=10, minute=0, tzinfo=JST
                    ),
                    room="Hall A",
                ),
                title="Session 1",
                track="Track 1",
                speakers=[Speaker(first_name="Speaker", last_name="A")],
                abstract=AbstractMarkdown(content="Abstract 1"),
                url="https://example.com/1",
            ),
            Session(
                slot=ScheduleSlot(
                    timeslot=datetime(
                        year=2026, month=1, day=7, hour=11, minute=0, tzinfo=JST
                    ),
                    room="Hall A",
                ),
                title="Session 2",
                track="Track 1",
                speakers=[Speaker(first_name="Speaker", last_name="B")],
                abstract=AbstractMarkdown(content="Abstract 2"),
                url="https://example.com/2",
            ),
        ]

    @pytest.fixture
    def mapping_file(self, tmp_path: Path) -> Path:
        """テスト用マッピングファイル"""
        yaml_content = """
sessions:
  "2026-01-07":
    "Hall A":
      "10:00":
        video_id: "video1"
      "11:00":
        video_id: "video2"
"""
        yaml_file = tmp_path / "mapping.yaml"
        yaml_file.write_text(data=yaml_content, encoding="utf-8")
        return yaml_file

    @pytest.fixture
    def mock_confengine_api(self, sessions: list[Session]) -> MagicMock:
        mock = MagicMock()
        mock.fetch_sessions.return_value = (sessions, JST)
        return mock

    @pytest.fixture
    def mock_youtube_api(self) -> MagicMock:
        """モックYouTube API"""
        mock = MagicMock(spec=YouTubeApiGateway)
        mock.get_video_info.side_effect = lambda video_id: VideoInfo(
            video_id=video_id,
            title=f"Title for {video_id}",
            description=f"Description for {video_id}",
            category_id=28,
        )
        return mock

    @pytest.fixture
    def usecase(
        self, mock_confengine_api: MagicMock, mock_youtube_api: MagicMock
    ) -> UpdateYouTubeDescriptionsUseCase:
        """テスト用ユースケース"""
        return UpdateYouTubeDescriptionsUseCase(
            confengine_api=mock_confengine_api,
            mapping_reader=MappingFileReader(),
            youtube_api=mock_youtube_api,
            description_builder=YouTubeDescriptionBuilder(),
            title_builder=YouTubeTitleBuilder(),
        )

    def test_execute_dry_run(
        self,
        usecase: UpdateYouTubeDescriptionsUseCase,
        mapping_file: Path,
    ) -> None:
        """dry-runモードでプレビューを返す"""
        result = usecase.execute(
            conf_id="test-conf",
            mapping_file=mapping_file,
            dry_run=True,
        )

        assert isinstance(result, YouTubeUpdateResult)
        assert result.is_dry_run is True
        assert result.updated_count == 0
        assert len(result.previews) == 2
        assert len(result.errors) == 0

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
        mock_youtube_api: MagicMock,
    ) -> None:
        """更新モードで動画を更新する"""
        result = usecase.execute(
            conf_id="test-conf",
            mapping_file=mapping_file,
            dry_run=False,
        )

        assert isinstance(result, YouTubeUpdateResult)
        assert result.is_dry_run is False
        assert result.updated_count == 2
        assert result.no_content_count == 0
        assert result.no_mapping_count == 0
        assert len(result.errors) == 0

        # YouTube APIが呼ばれたことを確認
        assert mock_youtube_api.update_video.call_count == 2

    def test_execute_skips_empty_sessions(
        self,
        mock_confengine_api: MagicMock,
        mock_youtube_api: MagicMock,
        mapping_file: Path,
    ) -> None:
        """abstractが空のセッションはスキップする"""
        mock_confengine_api.fetch_sessions.return_value = (
            [
                Session(
                    slot=ScheduleSlot(
                        timeslot=datetime(
                            year=2026,
                            month=1,
                            day=7,
                            hour=10,
                            minute=0,
                            second=0,
                            tzinfo=JST,
                        ),
                        room="Hall A",
                    ),
                    title="Empty Session",
                    track="Track 1",
                    speakers=[],
                    abstract=AbstractMarkdown(content=""),
                    url="https://example.com/empty",
                ),
            ],
            JST,
        )

        usecase = UpdateYouTubeDescriptionsUseCase(
            confengine_api=mock_confengine_api,
            mapping_reader=MappingFileReader(),
            youtube_api=mock_youtube_api,
            description_builder=YouTubeDescriptionBuilder(),
            title_builder=YouTubeTitleBuilder(),
        )

        result = usecase.execute(
            conf_id="test-conf",
            mapping_file=mapping_file,
            dry_run=False,
        )

        assert isinstance(result, YouTubeUpdateResult)
        assert result.updated_count == 0
        assert result.no_content_count == 1

    def test_execute_skips_unmapped_sessions(
        self,
        mock_confengine_api: MagicMock,
        mock_youtube_api: MagicMock,
        tmp_path: Path,
    ) -> None:
        """マッピングがないセッションはスキップする"""
        mock_confengine_api.fetch_sessions.return_value = (
            [
                Session(
                    slot=ScheduleSlot(
                        timeslot=datetime(
                            year=2026,
                            month=1,
                            day=8,
                            hour=14,
                            minute=0,
                            second=0,
                            tzinfo=JST,
                        ),
                        room="Hall C",
                    ),
                    title="Unmapped Session",
                    track="Track 1",
                    speakers=[Speaker(first_name="", last_name="Speaker")],
                    abstract=AbstractMarkdown(content="Content"),
                    url="https://example.com/unmapped",
                ),
            ],
            JST,
        )

        # 空のマッピングファイル
        yaml_content = """
sessions: {}
"""
        mapping_file = tmp_path / "empty_mapping.yaml"
        mapping_file.write_text(data=yaml_content, encoding="utf-8")

        usecase = UpdateYouTubeDescriptionsUseCase(
            confengine_api=mock_confengine_api,
            mapping_reader=MappingFileReader(),
            youtube_api=mock_youtube_api,
            description_builder=YouTubeDescriptionBuilder(),
            title_builder=YouTubeTitleBuilder(),
        )

        result = usecase.execute(
            conf_id="test-conf",
            mapping_file=mapping_file,
            dry_run=False,
        )

        assert isinstance(result, YouTubeUpdateResult)
        assert result.updated_count == 0
        assert result.no_mapping_count == 1

    def test_execute_warns_unused_mappings(
        self,
        mock_confengine_api: MagicMock,
        mock_youtube_api: MagicMock,
        tmp_path: Path,
    ) -> None:
        """マッピングにあるがConfEngineにないセッションは未使用として警告する"""
        mock_confengine_api.fetch_sessions.return_value = (
            [
                Session(
                    slot=ScheduleSlot(
                        timeslot=datetime(
                            year=2026,
                            month=1,
                            day=7,
                            hour=10,
                            minute=0,
                            second=0,
                            tzinfo=JST,
                        ),
                        room="Hall A",
                    ),
                    title="Session 1",
                    track="Track 1",
                    speakers=[Speaker(first_name="", last_name="Speaker")],
                    abstract=AbstractMarkdown(content="Content"),
                    url="https://example.com/1",
                ),
            ],
            JST,
        )

        # マッピングには2セッション (1つは使われない)
        yaml_content = """
sessions:
  "2026-01-07":
    "Hall A":
      "10:00":
        video_id: "video1"
      "14:00":
        video_id: "video_unused"
"""
        mapping_file = tmp_path / "unused_mapping.yaml"
        mapping_file.write_text(data=yaml_content, encoding="utf-8")

        usecase = UpdateYouTubeDescriptionsUseCase(
            confengine_api=mock_confengine_api,
            mapping_reader=MappingFileReader(),
            youtube_api=mock_youtube_api,
            description_builder=YouTubeDescriptionBuilder(),
            title_builder=YouTubeTitleBuilder(),
        )

        result = usecase.execute(
            conf_id="test-conf",
            mapping_file=mapping_file,
            dry_run=False,
        )

        assert isinstance(result, YouTubeUpdateResult)
        assert result.updated_count == 1
        assert result.unused_mappings_count == 1

    def test_execute_handles_youtube_api_error(
        self,
        usecase: UpdateYouTubeDescriptionsUseCase,
        mapping_file: Path,
        mock_youtube_api: MagicMock,
    ) -> None:
        """YouTubeApiErrorが発生してもエラーリストに追加して処理を継続する"""
        # 1つ目の動画でAPIエラー、2つ目は成功
        mock_youtube_api.get_video_info.side_effect = [
            YouTubeApiError("Rate limit exceeded"),
            VideoInfo(
                video_id="video2",
                title="Title 2",
                description="Description 2",
                category_id=28,
            ),
        ]

        result = usecase.execute(
            conf_id="test-conf",
            mapping_file=mapping_file,
            dry_run=False,
        )

        assert isinstance(result, YouTubeUpdateResult)
        assert result.updated_count == 1  # 2つ目だけ成功
        assert len(result.errors) == 1
        assert result.errors[0] == "Rate limit exceeded"

    def test_execute_dry_run_handles_youtube_api_error(
        self,
        usecase: UpdateYouTubeDescriptionsUseCase,
        mapping_file: Path,
        mock_youtube_api: MagicMock,
    ) -> None:
        """dry-runモードでもYouTubeApiErrorを適切に処理する"""
        mock_youtube_api.get_video_info.side_effect = [
            YouTubeApiError("Authentication failed"),
            VideoInfo(
                video_id="video2",
                title="Title 2",
                description="Description 2",
                category_id=28,
            ),
        ]

        result = usecase.execute(
            conf_id="test-conf",
            mapping_file=mapping_file,
            dry_run=True,
        )

        assert isinstance(result, YouTubeUpdateResult)
        assert len(result.previews) == 2  # エラー時もプレビュー生成
        # 1件目はエラー
        assert result.previews[0].error == "Authentication failed"
        assert result.previews[0].current_title is None
        assert result.previews[0].new_description is None
        # 2件目は正常
        assert result.previews[1].error is None
        assert result.previews[1].current_title == "Title 2"
        assert len(result.errors) == 1
        assert result.errors[0] == "Authentication failed"

    def test_execute_with_hashtags_in_mapping(
        self,
        mock_confengine_api: MagicMock,
        mock_youtube_api: MagicMock,
        tmp_path: Path,
    ) -> None:
        """マッピングファイルにhashtagsがある場合、descriptionに含まれる"""
        mock_confengine_api.fetch_sessions.return_value = (
            [
                Session(
                    slot=ScheduleSlot(
                        timeslot=datetime(
                            year=2026,
                            month=1,
                            day=7,
                            hour=10,
                            minute=0,
                            second=0,
                            tzinfo=JST,
                        ),
                        room="Hall A",
                    ),
                    title="Session 1",
                    track="Track 1",
                    speakers=[Speaker(first_name="Speaker", last_name="A")],
                    abstract=AbstractMarkdown(content="Abstract 1"),
                    url="https://example.com/1",
                ),
            ],
            JST,
        )

        yaml_content = """
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
        mapping_file = tmp_path / "mapping_with_hashtags.yaml"
        mapping_file.write_text(data=yaml_content, encoding="utf-8")

        usecase = UpdateYouTubeDescriptionsUseCase(
            confengine_api=mock_confengine_api,
            mapping_reader=MappingFileReader(),
            youtube_api=mock_youtube_api,
            description_builder=YouTubeDescriptionBuilder(),
            title_builder=YouTubeTitleBuilder(),
        )

        result = usecase.execute(
            conf_id="test-conf",
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
