"""HTTPクライアント"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any


class HttpClientError(Exception):
    """HTTPクライアントのエラー"""


class NetworkError(HttpClientError):
    """ネットワーク接続エラー"""


class HttpError(HttpClientError):
    """HTTPエラー (4xx/5xx)"""

    def __init__(self, message: str, status_code: int) -> None:
        super().__init__(message)
        self.status_code = status_code


class InvalidResponseError(HttpClientError):
    """不正なレスポンス (JSONデコードエラーなど)"""


class HttpClient:
    # API提供者側でのリクエスト識別用。バージョンの厳密性は要件ではない
    def __init__(self, user_agent: str = "ConfEngine-Exporter/1.0") -> None:
        self.user_agent = user_agent

    def get_json(self, url: str) -> Any:  # noqa: ANN401
        # S310: URLの安全性検証は呼び出し側の責務。渡されたURLをそのまま使用する
        req = urllib.request.Request(  # noqa: S310
            url=url,
            headers={"User-Agent": self.user_agent},
        )

        try:
            with urllib.request.urlopen(url=req, timeout=30) as response:  # noqa: S310
                body = response.read().decode(encoding="utf-8")
        except urllib.error.HTTPError as e:
            msg = f"HTTP {e.code}: {url}"
            raise HttpError(message=msg, status_code=e.code) from e
        except urllib.error.URLError as e:
            msg = f"Network error: {e.reason} ({url})"
            raise NetworkError(msg) from e
        except TimeoutError as e:
            msg = f"Request timeout: {url}"
            raise NetworkError(msg) from e

        try:
            return json.loads(s=body)
        except json.JSONDecodeError as e:
            msg = f"Invalid JSON response: {e}"
            raise InvalidResponseError(msg) from e
