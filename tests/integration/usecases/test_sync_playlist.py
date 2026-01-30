from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, call, create_autospec
from zoneinfo import ZoneInfo

import pytest
from googleapiclient.errors import HttpError

from confengine_to_youtube.adapters.mapping_file_reader import MappingFileReader
from confengine_to_youtube.adapters.youtube_api import YouTubeApiGateway
from confengine_to_youtube.domain.session import Session
from confengine_to_youtube.usecases.dto import (
    PlaylistItem,
    PlaylistOperationType,
    VideoInfo,
)
from confengine_to_youtube.usecases.protocols import (
    ConfEngineApiProtocol,
    YouTubeApiProtocol,
)
from confengine_to_youtube.usecases.sync_playlist import SyncPlaylistUseCase
from tests.conftest import create_session, write_yaml_file
from tests.integration.usecases.conftest import create_mock_confengine_api


class TestSyncPlaylistUseCase:
    """SyncPlaylistUseCase のテスト"""

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
playlist_id: PLxxxxxxxxxxxxxxxx
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
        # デフォルトでは空のプレイリストを返す
        mock.list_playlist_items.return_value = {}
        return mock  # type: ignore[no-any-return]

    @pytest.fixture
    def usecase(
        self,
        mock_confengine_api: ConfEngineApiProtocol,
        mapping_reader: MappingFileReader,
        mock_youtube_api: YouTubeApiProtocol,
    ) -> SyncPlaylistUseCase:
        return SyncPlaylistUseCase(
            confengine_api=mock_confengine_api,
            mapping_reader=mapping_reader,
            youtube_api=mock_youtube_api,
        )

    def test_sync_playlist_dry_run_adds_videos(
        self,
        usecase: SyncPlaylistUseCase,
        mapping_file: Path,
    ) -> None:
        """dry-runモードでプレイリストへの追加をプレビュー"""
        result = usecase.execute(
            mapping_file=mapping_file,
            dry_run=True,
        )

        assert result.is_dry_run is True
        assert result.playlist_id == "PLxxxxxxxxxxxxxxxx"
        assert len(result.operations) == 2

        # 両方の動画がADD操作として記録される
        op1 = result.operations[0]
        assert op1.video_id == "video1"
        assert op1.operation == PlaylistOperationType.ADD
        assert op1.position == 0

        op2 = result.operations[1]
        assert op2.video_id == "video2"
        assert op2.operation == PlaylistOperationType.ADD
        assert op2.position == 1

    def test_sync_playlist_adds_videos(
        self,
        usecase: SyncPlaylistUseCase,
        mapping_file: Path,
        mock_youtube_api: YouTubeApiProtocol,
    ) -> None:
        """実際にプレイリストに動画を追加"""
        result = usecase.execute(
            mapping_file=mapping_file,
            dry_run=False,
        )

        assert result.added_count == 2

        # add_to_playlist が正しい引数で呼ばれたことを確認
        assert mock_youtube_api.add_to_playlist.call_args_list == [  # type: ignore[attr-defined]
            call(
                playlist_id="PLxxxxxxxxxxxxxxxx",
                video_id="video1",
                position=0,
            ),
            call(
                playlist_id="PLxxxxxxxxxxxxxxxx",
                video_id="video2",
                position=1,
            ),
        ]

    def test_sync_playlist_reorders_videos(
        self,
        usecase: SyncPlaylistUseCase,
        mapping_file: Path,
        mock_youtube_api: YouTubeApiProtocol,
    ) -> None:
        """プレイリスト内の動画の順番を更新"""
        # プレイリストに既に動画があるが順番が違う場合
        mock_youtube_api.list_playlist_items.return_value = {  # type: ignore[attr-defined]
            "video1": PlaylistItem(
                video_id="video1",
                playlist_item_id="item1",
                position=1,  # 間違った位置
            ),
            "video2": PlaylistItem(
                video_id="video2",
                playlist_item_id="item2",
                position=0,  # 間違った位置
            ),
        }

        result = usecase.execute(
            mapping_file=mapping_file,
            dry_run=False,
        )

        assert result.reordered_count == 2

        # update_playlist_item_position が正しい引数で呼ばれたことを確認
        assert mock_youtube_api.update_playlist_item_position.call_args_list == [  # type: ignore[attr-defined]
            call(
                playlist_item_id="item1",
                playlist_id="PLxxxxxxxxxxxxxxxx",
                video_id="video1",
                position=0,
            ),
            call(
                playlist_item_id="item2",
                playlist_id="PLxxxxxxxxxxxxxxxx",
                video_id="video2",
                position=1,
            ),
        ]

    def test_sync_playlist_unchanged_videos(
        self,
        usecase: SyncPlaylistUseCase,
        mapping_file: Path,
        mock_youtube_api: YouTubeApiProtocol,
    ) -> None:
        """正しい順番の動画は変更しない"""
        # プレイリストに既に正しい順番で動画がある
        mock_youtube_api.list_playlist_items.return_value = {  # type: ignore[attr-defined]
            "video1": PlaylistItem(
                video_id="video1",
                playlist_item_id="item1",
                position=0,
            ),
            "video2": PlaylistItem(
                video_id="video2",
                playlist_item_id="item2",
                position=1,
            ),
        }

        result = usecase.execute(
            mapping_file=mapping_file,
            dry_run=False,
        )

        assert result.unchanged_count == 2
        assert result.added_count == 0
        assert result.reordered_count == 0

        # API変更が呼ばれていないことを確認
        mock_youtube_api.add_to_playlist.assert_not_called()  # type: ignore[attr-defined]
        mock_youtube_api.update_playlist_item_position.assert_not_called()  # type: ignore[attr-defined]

    def test_sync_playlist_moves_unmapped_videos_to_end(
        self,
        usecase: SyncPlaylistUseCase,
        mapping_file: Path,
        mock_youtube_api: YouTubeApiProtocol,
    ) -> None:
        """マッピングにない動画を末尾に移動"""
        # プレイリストにマッピングにない動画がある
        mock_youtube_api.list_playlist_items.return_value = {  # type: ignore[attr-defined]
            "video1": PlaylistItem(
                video_id="video1",
                playlist_item_id="item1",
                position=0,
            ),
            "video2": PlaylistItem(
                video_id="video2",
                playlist_item_id="item2",
                position=1,
            ),
            "unmapped_video": PlaylistItem(
                video_id="unmapped_video",
                playlist_item_id="item_unmapped",
                position=0,  # 先頭にあるが末尾に移動されるべき
            ),
        }

        result = usecase.execute(
            mapping_file=mapping_file,
            dry_run=True,
        )

        # マッピング済み動画が2つ、マッピングなし動画が1つ (末尾に移動)
        move_ops = [
            op
            for op in result.operations
            if op.operation == PlaylistOperationType.MOVE_TO_END
        ]
        assert len(move_ops) == 1
        assert move_ops[0].video_id == "unmapped_video"
        assert move_ops[0].position == 2  # 末尾 (0, 1 の後)

    def test_sync_playlist_raises_error_when_playlist_not_found(
        self,
        usecase: SyncPlaylistUseCase,
        mapping_file: Path,
        mock_youtube_api: YouTubeApiProtocol,
    ) -> None:
        """プレイリストが存在しない場合はHttpErrorを発生"""
        resp = MagicMock()
        resp.status = 404
        mock_youtube_api.list_playlist_items.side_effect = HttpError(  # type: ignore[attr-defined]
            resp=resp,
            content=b'{"error": {"message": "Playlist not found"}}',
        )

        with pytest.raises(HttpError):
            usecase.execute(
                mapping_file=mapping_file,
                dry_run=False,
            )

    def test_sync_playlist_records_unchanged_for_unmapped_video_at_correct_position(
        self,
        usecase: SyncPlaylistUseCase,
        mapping_file: Path,
        mock_youtube_api: YouTubeApiProtocol,
    ) -> None:
        """マッピングなし動画がすでに正しい位置にある場合はUNCHANGEDとして記録"""
        mock_youtube_api.list_playlist_items.return_value = {  # type: ignore[attr-defined]
            "video1": PlaylistItem(
                video_id="video1",
                playlist_item_id="item1",
                position=0,
            ),
            "video2": PlaylistItem(
                video_id="video2",
                playlist_item_id="item2",
                position=1,
            ),
            "unmapped_video": PlaylistItem(
                video_id="unmapped_video",
                playlist_item_id="item_unmapped",
                position=2,  # すでに末尾にある
            ),
        }

        result = usecase.execute(
            mapping_file=mapping_file,
            dry_run=True,
        )

        # マッピングなし動画がすでに正しい位置なのでUNCHANGEDとして記録される
        unmapped_ops = [
            op for op in result.operations if op.video_id == "unmapped_video"
        ]
        assert len(unmapped_ops) == 1
        assert unmapped_ops[0].operation == PlaylistOperationType.UNCHANGED
        assert unmapped_ops[0].position == 2
        # 全動画数とoperations数が一致
        assert len(result.operations) == 3
