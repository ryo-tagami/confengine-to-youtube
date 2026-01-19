"""Adapters 層のプロトコル定義

Clean Architecture の依存方向を守るため、adapters 層で Protocol を定義し、
infrastructure 層でこれらを実装する。
"""

from __future__ import annotations

from typing import Any, Protocol


class HttpClientProtocol(Protocol):  # pragma: no cover
    """HTTP クライアントプロトコル"""

    def get_json(self, url: str) -> Any:  # noqa: ANN401
        """URL から JSON を取得する"""
        ...


class YouTubeAuthProvider(Protocol):  # pragma: no cover
    """YouTube 認証プロバイダープロトコル"""

    def get_credentials(self) -> Any:  # noqa: ANN401
        """認証情報を取得する"""
        ...
