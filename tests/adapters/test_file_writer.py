"""ファイル出力のテスト"""

from pathlib import Path

from confengine_exporter.adapters.file_writer import SessionFileWriter
from confengine_exporter.domain.session import Session


class TestSessionFileWriter:
    """SessionFileWriter のテスト"""

    def test_write_creates_file(self, tmp_path: Path, sample_session: Session) -> None:
        """ファイルが作成される"""
        writer = SessionFileWriter(output_dir=tmp_path)
        filepath = writer.write(session=sample_session, content="Test content")

        assert filepath.exists()
        assert filepath.read_text() == "Test content"

    def test_write_creates_directory(
        self, tmp_path: Path, sample_session: Session
    ) -> None:
        """出力ディレクトリが存在しない場合は作成される"""
        output_dir = tmp_path / "subdir" / "output"
        writer = SessionFileWriter(output_dir=output_dir)
        filepath = writer.write(session=sample_session, content="Test content")

        assert output_dir.exists()
        assert filepath.read_text() == "Test content"

    def test_generate_filename(self, tmp_path: Path, sample_session: Session) -> None:
        """ファイル名が正しく生成される"""
        writer = SessionFileWriter(output_dir=tmp_path)
        filename = writer._generate_filename(session=sample_session)

        assert filename == "2026-01-07_Hall-A_10-00.md"

    def test_sanitize_filename_replaces_special_chars(self, tmp_path: Path) -> None:
        """特殊文字が置換される"""
        writer = SessionFileWriter(output_dir=tmp_path)

        assert writer._sanitize_filename("Hall/A") == "Hall-A"
        assert writer._sanitize_filename("Room:1") == "Room-1"
        assert writer._sanitize_filename('Test"Name') == "Test-Name"
        assert writer._sanitize_filename("Test<>Name") == "Test-Name"

    def test_sanitize_filename_replaces_spaces(self, tmp_path: Path) -> None:
        """スペースがハイフンに置換される"""
        writer = SessionFileWriter(output_dir=tmp_path)

        assert writer._sanitize_filename("Hall A") == "Hall-A"
        assert writer._sanitize_filename("Room 3 4") == "Room-3-4"

    def test_sanitize_filename_collapses_hyphens(self, tmp_path: Path) -> None:
        """連続するハイフンが1つに"""
        writer = SessionFileWriter(output_dir=tmp_path)

        assert writer._sanitize_filename("Hall--A") == "Hall-A"
        assert writer._sanitize_filename("Room - A") == "Room-A"

    def test_write_warns_when_overwriting(
        self, tmp_path: Path, sample_session: Session, capsys: object
    ) -> None:
        """既存ファイルを上書きする場合は警告が出力される"""
        writer = SessionFileWriter(output_dir=tmp_path)

        # 1回目の書き込み
        filepath = writer.write(session=sample_session, content="First content")

        # 2回目の書き込み (上書き)
        writer.write(session=sample_session, content="Second content")

        captured = capsys.readouterr()  # type: ignore[attr-defined]

        assert "Warning: Overwriting" in captured.err
        assert filepath.read_text() == "Second content"
