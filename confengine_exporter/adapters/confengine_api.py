"""ConfEngine API Gateway"""

from __future__ import annotations

from typing import TYPE_CHECKING

from confengine_exporter.adapters.confengine_schema import ScheduleResponse
from confengine_exporter.domain.session import Session

if TYPE_CHECKING:
    from confengine_exporter.infrastructure.http_client import HttpClient


class ConfEngineApiGateway:
    """ConfEngine APIからセッション情報を取得"""

    BASE_URL = "https://confengine.com/api/v3"

    def __init__(self, http_client: HttpClient) -> None:
        self.http_client = http_client

    def fetch_sessions(self, conf_id: str) -> list[Session]:
        """指定カンファレンスのセッション一覧を取得"""
        url = f"{self.BASE_URL}/conferences/{conf_id}/schedule"

        schedule_data = self.http_client.get_json(url=url)
        response = ScheduleResponse.model_validate(obj=schedule_data)

        return self._extract_sessions(response=response)

    def _extract_sessions(self, response: ScheduleResponse) -> list[Session]:
        """APIレスポンスからセッション情報を抽出"""
        sessions: list[Session] = []

        for day_data in response.conf_schedule:
            for schedule_day in day_data.schedule_days:
                for slot_item in schedule_day.sessions:
                    for api_sessions in slot_item.values():
                        for api_session in api_sessions:
                            sessions.append(  # noqa: PERF401
                                Session(
                                    title=api_session.title,
                                    timeslot=api_session.timeslot,
                                    room=api_session.room,
                                    track=api_session.track,
                                    speakers=api_session.speaker_names,
                                    abstract=api_session.abstract_markdown,
                                    url=api_session.url,
                                )
                            )

        sessions.sort(key=lambda s: (s.timeslot, s.room))

        return sessions
