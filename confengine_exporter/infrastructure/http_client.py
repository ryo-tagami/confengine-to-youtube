"""HTTPクライアント"""

import json
import urllib.request
from typing import Any


class HttpClient:
    """HTTPリクエストを行うクライアント"""

    def __init__(self, user_agent: str = "ConfEngine-Exporter/1.0") -> None:
        self.user_agent = user_agent

    def get_json(self, url: str) -> Any:  # noqa: ANN401
        """GETリクエストを行いJSONを返す"""
        req = urllib.request.Request(  # noqa: S310
            url,
            headers={"User-Agent": self.user_agent},
        )

        with urllib.request.urlopen(req, timeout=30) as response:  # noqa: S310
            return json.loads(response.read().decode("utf-8"))
