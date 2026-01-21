"""YouTubeAuthClient のテスト

NOTE: このテストではプライベートメソッド (_load_token, _save_token) を
直接テストしている。

理由:
- これらのメソッドは「トークンの永続化」という独立した責務を持つ
- パーミッション設定やディレクトリ作成などのエッジケースを個別にテスト可能
- get_credentials 経由でテストすると OAuth フローのモックが必要で複雑化する
"""

from __future__ import annotations

import stat
from pathlib import Path
from unittest.mock import create_autospec

import pytest
from google.oauth2.credentials import Credentials

from confengine_to_youtube.infrastructure.youtube_auth import YouTubeAuthClient


class TestYouTubeAuthClient:
    """YouTubeAuthClient のテスト"""

    @pytest.fixture
    def client(self, tmp_path: Path) -> YouTubeAuthClient:
        return YouTubeAuthClient(
            credentials_path=tmp_path / "credentials.json",
            token_path=tmp_path / "token.json",
        )

    def test_load_token_returns_none_when_file_not_exists(
        self,
        client: YouTubeAuthClient,
    ) -> None:
        """トークンファイルが存在しない場合はNoneを返す"""
        result = client._load_token()

        assert result is None

    def test_load_token_loads_credentials_from_file(
        self,
        client: YouTubeAuthClient,
    ) -> None:
        """トークンファイルが存在する場合はCredentialsを読み込む"""
        token_content = '{"token": "t", "refresh_token": "r", "client_id": "i", "client_secret": "s"}'  # noqa: S105, E501
        client.token_path.write_text(data=token_content, encoding="utf-8")

        result = client._load_token()

        assert isinstance(result, Credentials)

    def test_save_token_writes_json_to_file(self, client: YouTubeAuthClient) -> None:
        """トークンをJSONファイルに書き込む"""
        mock_credentials = create_autospec(Credentials, spec_set=True)
        mock_credentials.to_json.return_value = '{"token": "saved_token"}'

        client._save_token(credentials=mock_credentials)

        assert client.token_path.exists()
        content = client.token_path.read_text(encoding="utf-8")
        assert content == '{"token": "saved_token"}'

    def test_save_token_creates_parent_directories(self, tmp_path: Path) -> None:
        """親ディレクトリが存在しない場合は作成する"""
        nested_path = tmp_path / "nested" / "dir" / "token.json"
        client = YouTubeAuthClient(
            credentials_path=tmp_path / "credentials.json",
            token_path=nested_path,
        )
        mock_credentials = create_autospec(Credentials, spec_set=True)
        mock_credentials.to_json.return_value = "{}"

        client._save_token(credentials=mock_credentials)

        assert nested_path.exists()

    def test_save_token_sets_file_permissions_to_0600(
        self,
        client: YouTubeAuthClient,
    ) -> None:
        """トークンファイルのパーミッションを0600に設定する"""
        mock_credentials = create_autospec(Credentials, spec_set=True)
        mock_credentials.to_json.return_value = "{}"

        client._save_token(credentials=mock_credentials)

        file_stat = client.token_path.stat()
        file_mode = stat.S_IMODE(file_stat.st_mode)
        expected_mode = stat.S_IRUSR | stat.S_IWUSR  # 0600
        assert file_mode == expected_mode
