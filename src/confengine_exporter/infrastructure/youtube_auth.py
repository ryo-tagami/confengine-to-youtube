from __future__ import annotations

import logging
import stat
from typing import TYPE_CHECKING, ClassVar

from google.auth.exceptions import RefreshError
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

logger = logging.getLogger(name=__name__)

if TYPE_CHECKING:
    from pathlib import Path


class YouTubeAuthClient:
    SCOPES: ClassVar[list[str]] = ["https://www.googleapis.com/auth/youtube.force-ssl"]

    def __init__(
        self,
        credentials_path: Path,
        token_path: Path,
    ) -> None:
        self.credentials_path = credentials_path
        self.token_path = token_path

    def get_credentials(self) -> Credentials:
        if (creds := self._load_token()) and creds.valid:
            return creds

        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(request=Request())
            except RefreshError:
                logger.warning(
                    "Token refresh failed, falling back to OAuth flow",
                    exc_info=True,
                )
            else:
                self._save_token(credentials=creds)
                return creds

        # 認証情報がない、または期限切れでリフレッシュ不可の場合
        creds = self._run_oauth_flow()
        self._save_token(credentials=creds)
        return creds

    def _load_token(self) -> Credentials | None:
        if not self.token_path.exists():
            return None

        return Credentials.from_authorized_user_file(  # type: ignore[no-any-return,no-untyped-call]
            filename=str(self.token_path),
            scopes=self.SCOPES,
        )

    def _save_token(self, credentials: Credentials) -> None:
        self.token_path.parent.mkdir(parents=True, exist_ok=True)
        self.token_path.write_text(data=credentials.to_json())  # type: ignore[no-untyped-call]
        self.token_path.chmod(mode=stat.S_IRUSR | stat.S_IWUSR)  # 0600

    def _run_oauth_flow(self) -> Credentials:
        # 認証失敗時の例外はCLI層でキャッチされ、エラーメッセージが表示される
        flow = InstalledAppFlow.from_client_secrets_file(
            client_secrets_file=str(self.credentials_path),
            scopes=self.SCOPES,
        )
        return flow.run_local_server(port=0)  # type: ignore[no-any-return]
