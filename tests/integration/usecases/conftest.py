"""usecases テスト用の共通フィクスチャ"""

from unittest.mock import create_autospec
from zoneinfo import ZoneInfo

from confengine_to_youtube.domain.conference_schedule import ConferenceSchedule
from confengine_to_youtube.domain.session import Session
from confengine_to_youtube.usecases.protocols import ConfEngineApiProtocol


def create_mock_confengine_api(
    sessions: tuple[Session, ...],
    timezone: ZoneInfo,
    conf_id: str = "test-conf",
) -> ConfEngineApiProtocol:
    """ConfEngine API のモックを作成するヘルパー"""
    mock = create_autospec(ConfEngineApiProtocol, spec_set=True)
    mock.fetch_schedule.return_value = ConferenceSchedule(
        conf_id=conf_id,
        timezone=timezone,
        sessions=sessions,
    )
    return mock  # type: ignore[no-any-return]
