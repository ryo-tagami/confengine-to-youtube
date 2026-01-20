from __future__ import annotations

from typing import TYPE_CHECKING
from zoneinfo import ZoneInfo

from confengine_to_youtube.adapters.confengine_schema import ScheduleResponse
from confengine_to_youtube.domain.schedule_slot import ScheduleSlot
from confengine_to_youtube.domain.session import Session, Speaker

if TYPE_CHECKING:
    from confengine_to_youtube.adapters.protocols import HttpClientProtocol
    from confengine_to_youtube.usecases.protocols import MarkdownConverterProtocol


class ConfEngineApiGateway:
    BASE_URL = "https://confengine.com/api/v3"

    def __init__(
        self,
        http_client: HttpClientProtocol,
        markdown_converter: MarkdownConverterProtocol,
    ) -> None:
        self._http_client = http_client
        self._markdown_converter = markdown_converter

    def fetch_sessions(self, conf_id: str) -> tuple[list[Session], ZoneInfo]:
        url = f"{self.BASE_URL}/conferences/{conf_id}/schedule"

        schedule_data = self._http_client.get_json(url=url)
        response = ScheduleResponse.model_validate(obj=schedule_data)

        timezone = ZoneInfo(key=response.conf_timezone)
        sessions = self._extract_sessions(response=response, timezone=timezone)

        return sessions, timezone

    def _extract_sessions(
        self,
        response: ScheduleResponse,
        timezone: ZoneInfo,
    ) -> list[Session]:
        sessions: list[Session] = []

        for day_data in response.conf_schedule:
            for schedule_day in day_data.schedule_days:
                for slot_sessions in schedule_day.sessions:
                    for api_sessions in slot_sessions.values():
                        for api_session in api_sessions:
                            slot = ScheduleSlot(
                                timeslot=api_session.timeslot.replace(tzinfo=timezone),
                                room=api_session.room,
                            )
                            abstract = self._markdown_converter.convert(
                                html=api_session.abstract
                            )
                            sessions.append(
                                Session(
                                    slot=slot,
                                    title=api_session.title,
                                    track=api_session.track,
                                    speakers=[
                                        Speaker(
                                            first_name=speaker.first_name,
                                            last_name=speaker.last_name,
                                        )
                                        for speaker in api_session.speakers
                                    ],
                                    abstract=abstract,
                                    url=api_session.url,
                                )
                            )

        sessions.sort(key=lambda s: (s.slot.timeslot, s.slot.room))

        return sessions
