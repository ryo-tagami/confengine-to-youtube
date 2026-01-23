from __future__ import annotations

from confengine_to_youtube.adapters.confengine_api import ConfEngineApiGateway
from confengine_to_youtube.adapters.markdown_converter import MarkdownConverter
from confengine_to_youtube.infrastructure.http_client import HttpClient


def create_confengine_api() -> ConfEngineApiGateway:
    """ConfEngineApiGatewayのインスタンスを生成する"""
    return ConfEngineApiGateway(
        http_client=HttpClient(),
        markdown_converter=MarkdownConverter(),
    )
