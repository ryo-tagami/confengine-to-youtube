"""HTTPクライアント"""

from __future__ import annotations

import json
import urllib.request
from typing import Any

from returns.io import IOResult, impure_safe


def _fetch_url(req: urllib.request.Request) -> str:
    # URLの安全性検証は呼び出し側の責務
    with urllib.request.urlopen(url=req, timeout=30) as response:  # noqa: S310
        return response.read().decode(encoding="utf-8")  # type: ignore[no-any-return]


class HttpClient:
    # API提供者側でのリクエスト識別用。バージョンの厳密性は要件ではない
    def __init__(self, user_agent: str = "ConfEngine-to-YouTube/1.0") -> None:
        self.user_agent = user_agent

    def get_json(self, url: str) -> IOResult[Any, Exception]:
        """URLからJSONを取得する"""
        # S310: URLの安全性検証は呼び出し側の責務。渡されたURLをそのまま使用する
        req = urllib.request.Request(  # noqa: S310
            url=url,
            headers={"User-Agent": self.user_agent},
        )

        return impure_safe(_fetch_url)(req).bind(
            lambda body: impure_safe(json.loads)(body),
        )
