"""usecases テスト用の共通フィクスチャ"""

from unittest.mock import create_autospec
from zoneinfo import ZoneInfo

from returns.io import IOSuccess

from confengine_to_youtube.domain.session import Session
from confengine_to_youtube.usecases.protocols import ConfEngineApiProtocol


def create_mock_confengine_api(
    sessions: tuple[Session, ...],
    timezone: ZoneInfo,
) -> ConfEngineApiProtocol:
    """ConfEngine API のモックを作成するヘルパー"""
    mock = create_autospec(ConfEngineApiProtocol, spec_set=True)
    mock.fetch_sessions.return_value = IOSuccess((sessions, timezone))
    return mock  # type: ignore[no-any-return]
