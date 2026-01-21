"""ForbiddenImportChecker の統合テスト

find_violations メソッドの動作を実際のファイルI/O (tmp_path) を使ってテストする。
ForbiddenImportChecker は依存性注入可能な設計のため、
module_path_resolver をコンストラクタで注入してテストできる。
"""

import sys
from pathlib import Path
from unittest.mock import create_autospec

import pytest
from grimp import ImportGraph

from confengine_to_youtube.import_contracts import (
    ForbiddenImportChecker,
    default_module_path_resolver,
)


class TestFindViolationsIntegration:
    """find_violations メソッドの統合テスト"""

    @pytest.fixture
    def mock_graph(self) -> ImportGraph:
        """ImportGraph のモック"""
        mock = create_autospec(ImportGraph, spec_set=True)
        mock.find_descendants.return_value = set()
        return mock  # type: ignore[no-any-return]

    def test_find_violations_with_no_violations(
        self,
        tmp_path: Path,
        mock_graph: ImportGraph,
    ) -> None:
        """違反がない場合は空リストを返す"""
        test_file = tmp_path / "test_module.py"
        test_file.write_text("from returns.result import Result\n")

        checker = ForbiddenImportChecker(
            module_path_resolver=lambda m: test_file if m == "test_module" else None,
        )

        violations = checker.find_violations(
            source_modules=["test_module"],
            forbidden_modules=["returns.unsafe"],
            graph=mock_graph,
            verbose=False,
        )

        assert violations == []
        mock_graph.find_descendants.assert_called_once_with(  # type: ignore[attr-defined]
            "test_module",
        )

    def test_find_violations_with_violations(
        self,
        tmp_path: Path,
        mock_graph: ImportGraph,
    ) -> None:
        """違反がある場合は違反リストを返す"""
        test_file = tmp_path / "test_module.py"
        test_file.write_text("from returns.unsafe import unsafe_perform_io\n")

        checker = ForbiddenImportChecker(
            module_path_resolver=lambda m: test_file if m == "test_module" else None,
        )

        violations = checker.find_violations(
            source_modules=["test_module"],
            forbidden_modules=["returns.unsafe"],
            graph=mock_graph,
            verbose=False,
        )

        # "returns.unsafe" と "returns.unsafe.unsafe_perform_io" の両方が検出される
        assert len(violations) >= 1
        assert ("test_module", "returns.unsafe", 1) in violations

    def test_find_violations_detects_from_parent_import(
        self,
        tmp_path: Path,
        mock_graph: ImportGraph,
    ) -> None:
        """'from returns import unsafe' 形式を検出"""
        test_file = tmp_path / "test_module.py"
        test_file.write_text("from returns import unsafe\n")

        checker = ForbiddenImportChecker(
            module_path_resolver=lambda m: test_file if m == "test_module" else None,
        )

        violations = checker.find_violations(
            source_modules=["test_module"],
            forbidden_modules=["returns.unsafe"],
            graph=mock_graph,
            verbose=False,
        )

        assert len(violations) == 1
        assert violations[0][1] == "returns.unsafe"


class TestDefaultModulePathResolver:
    """default_module_path_resolver 関数のテスト"""

    def test_resolves_module_file(self, tmp_path: Path) -> None:
        """モジュールファイル (.py) を正しく解決"""
        module_file = tmp_path / "my_module.py"
        module_file.write_text("# test module\n")

        # sys.path に一時ディレクトリを追加
        original_path = sys.path.copy()
        sys.path.insert(0, str(tmp_path))

        try:
            result = default_module_path_resolver("my_module")

            assert result == module_file
        finally:
            sys.path[:] = original_path

    def test_resolves_package_init(self, tmp_path: Path) -> None:
        """パッケージの __init__.py を正しく解決"""
        package_dir = tmp_path / "my_package"
        package_dir.mkdir()
        init_file = package_dir / "__init__.py"
        init_file.write_text("# package init\n")

        original_path = sys.path.copy()
        sys.path.insert(0, str(tmp_path))

        try:
            result = default_module_path_resolver("my_package")

            assert result == init_file
        finally:
            sys.path[:] = original_path

    def test_resolves_submodule(self, tmp_path: Path) -> None:
        """サブモジュールを正しく解決"""
        package_dir = tmp_path / "parent"
        package_dir.mkdir()
        (package_dir / "__init__.py").write_text("")
        submodule = package_dir / "child.py"
        submodule.write_text("# submodule\n")

        original_path = sys.path.copy()
        sys.path.insert(0, str(tmp_path))

        try:
            result = default_module_path_resolver("parent.child")

            assert result == submodule
        finally:
            sys.path[:] = original_path

    def test_returns_none_for_nonexistent_module(self) -> None:
        """存在しないモジュールは None を返す"""
        result = default_module_path_resolver(
            "nonexistent_module_that_does_not_exist_12345",
        )

        assert result is None


class TestCheckFileErrorHandling:
    """_check_file メソッドのエラーハンドリングテスト"""

    def test_handles_syntax_error(self, tmp_path: Path) -> None:
        """構文エラーのあるファイルを graceful に処理"""
        bad_file = tmp_path / "bad_syntax.py"
        bad_file.write_text("def broken(\n")  # 構文エラー

        checker = ForbiddenImportChecker(
            module_path_resolver=lambda _: bad_file,
        )

        # エラーを投げずに空リストを返す
        result = checker._check_file(
            file_path=bad_file,
            module_name="bad_syntax",
            forbidden_modules=["returns.unsafe"],
            verbose=False,
        )

        assert result == []

    def test_handles_unreadable_file(self, tmp_path: Path) -> None:
        """読み取れないファイルを graceful に処理"""
        unreadable = tmp_path / "unreadable.py"
        unreadable.write_text("import os\n")
        unreadable.chmod(0o000)  # 読み取り権限を削除

        checker = ForbiddenImportChecker(
            module_path_resolver=lambda _: unreadable,
        )

        try:
            # エラーを投げずに空リストを返す
            result = checker._check_file(
                file_path=unreadable,
                module_name="unreadable",
                forbidden_modules=["returns.unsafe"],
                verbose=False,
            )

            assert result == []
        finally:
            # 権限を戻してクリーンアップできるようにする
            unreadable.chmod(0o644)

    def test_verbose_output_on_syntax_error(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """verbose=True で構文エラー時に警告を出力"""
        bad_file = tmp_path / "bad_syntax.py"
        bad_file.write_text("def broken(\n")

        checker = ForbiddenImportChecker(
            module_path_resolver=lambda _: bad_file,
        )

        checker._check_file(
            file_path=bad_file,
            module_name="bad_syntax",
            forbidden_modules=["returns.unsafe"],
            verbose=True,
        )

        captured = capsys.readouterr()
        lines = captured.out.splitlines()
        # 出力形式: "Warning: Syntax error in {file_path}: {e}"
        assert any(line.startswith("Warning: Syntax error in") for line in lines)

    def test_verbose_output_on_violation(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """verbose=True で違反検出時に出力"""
        test_file = tmp_path / "test_module.py"
        test_file.write_text("from returns.unsafe import unsafe_perform_io\n")

        checker = ForbiddenImportChecker(
            module_path_resolver=lambda _: test_file,
        )

        checker._check_file(
            file_path=test_file,
            module_name="test_module",
            forbidden_modules=["returns.unsafe"],
            verbose=True,
        )

        captured = capsys.readouterr()
        lines = captured.out.splitlines()
        # 出力形式: "Found violation: {module}:{line} imports {imported}"
        assert any(
            "Found violation: test_module:1 imports returns.unsafe" in line
            for line in lines
        )
