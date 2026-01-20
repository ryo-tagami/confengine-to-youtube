"""YouTubeAuthClient のテスト"""

from __future__ import annotations

import stat
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

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
        self, client: YouTubeAuthClient
    ) -> None:
        """トークンファイルが存在しない場合はNoneを返す"""
        result = client._load_token()

        assert result is None

    def test_load_token_loads_credentials_from_file(
        self, client: YouTubeAuthClient
    ) -> None:
        """トークンファイルが存在する場合はCredentialsを読み込む"""
        token_content = '{"token": "test"}'  # noqa: S105
        client.token_path.write_text(data=token_content, encoding="utf-8")

        with patch(
            target="confengine_to_youtube.infrastructure.youtube_auth.Credentials"
        ) as mock_credentials:
            mock_creds = MagicMock()
            mock_credentials.from_authorized_user_file.return_value = mock_creds

            result = client._load_token()

            mock_credentials.from_authorized_user_file.assert_called_once_with(
                filename=str(client.token_path),
                scopes=YouTubeAuthClient.SCOPES,
            )
            assert result == mock_creds

    def test_save_token_writes_json_to_file(self, client: YouTubeAuthClient) -> None:
        """トークンをJSONファイルに書き込む"""
        mock_credentials = MagicMock()
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
        mock_credentials = MagicMock()
        mock_credentials.to_json.return_value = "{}"

        client._save_token(credentials=mock_credentials)

        assert nested_path.exists()

    def test_save_token_sets_file_permissions_to_0600(
        self, client: YouTubeAuthClient
    ) -> None:
        """トークンファイルのパーミッションを0600に設定する"""
        mock_credentials = MagicMock()
        mock_credentials.to_json.return_value = "{}"

        client._save_token(credentials=mock_credentials)

        file_stat = client.token_path.stat()
        file_mode = stat.S_IMODE(file_stat.st_mode)
        expected_mode = stat.S_IRUSR | stat.S_IWUSR  # 0600
        assert file_mode == expected_mode
