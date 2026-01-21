"""ForbiddenImportChecker のユニットテスト

import-linter コントラクトの AST 解析ロジックをテストする。
ForbiddenImportChecker は依存性注入可能な設計のため、
モックを使わずに直接テストできる。

Note:
    プライベートメソッド (_get_imported_modules, _is_forbidden, _find_violations) を
    直接テストしている。これは AST 解析ロジックの各ステップを個別に検証するためであり、
    公開インターフェース (find_violations) 経由では検証が困難な細かい挙動を
    確認する目的で行っている。

"""

import ast

import pytest
from importlinter import ContractCheck

from confengine_to_youtube.import_contracts import (
    ForbiddenExternalSubmoduleContract,
    ForbiddenImportChecker,
)


@pytest.fixture
def checker() -> ForbiddenImportChecker:
    """テスト用チェッカーインスタンス"""
    return ForbiddenImportChecker(
        module_path_resolver=lambda _: None,
    )


class TestGetImportedModules:
    """_get_imported_modules メソッドのテスト"""

    def test_import_single_module(
        self,
        checker: ForbiddenImportChecker,
    ) -> None:
        """単一モジュールの import"""
        tree = ast.parse("import foo")
        node = next(n for n in ast.walk(tree) if isinstance(n, ast.Import))

        result = checker._get_imported_modules(node)

        assert result == ["foo"]

    def test_import_multiple_modules(
        self,
        checker: ForbiddenImportChecker,
    ) -> None:
        """複数モジュールの import (カンマ区切り)"""
        tree = ast.parse("import foo, bar.baz, qux")
        node = next(n for n in ast.walk(tree) if isinstance(n, ast.Import))

        result = checker._get_imported_modules(node)

        assert result == ["foo", "bar.baz", "qux"]

    def test_import_from(
        self,
        checker: ForbiddenImportChecker,
    ) -> None:
        """From ... import 形式"""
        tree = ast.parse("from foo.bar import baz")
        node = next(n for n in ast.walk(tree) if isinstance(n, ast.ImportFrom))

        result = checker._get_imported_modules(node)

        # "foo.bar" と "foo.bar.baz" の両方を返す
        assert result == ["foo.bar", "foo.bar.baz"]

    def test_import_from_multiple_names(
        self,
        checker: ForbiddenImportChecker,
    ) -> None:
        """From ... import で複数の名前をインポート"""
        tree = ast.parse("from foo import bar, baz")
        node = next(n for n in ast.walk(tree) if isinstance(n, ast.ImportFrom))

        result = checker._get_imported_modules(node)

        # "foo", "foo.bar", "foo.baz" をすべて返す
        assert result == ["foo", "foo.bar", "foo.baz"]

    def test_import_from_without_module(
        self,
        checker: ForbiddenImportChecker,
    ) -> None:
        """相対インポート (from . import xxx)"""
        tree = ast.parse("from . import foo", mode="exec")
        node = next(n for n in ast.walk(tree) if isinstance(n, ast.ImportFrom))

        result = checker._get_imported_modules(node)

        # 相対インポートは module が None なので空リストを返す
        assert result == []


class TestIsForbidden:
    """_is_forbidden メソッドのテスト"""

    def test_exact_match(
        self,
        checker: ForbiddenImportChecker,
    ) -> None:
        """完全一致"""
        result = checker._is_forbidden(
            module="returns.unsafe",
            forbidden_modules=["returns.unsafe"],
        )

        assert result is True

    def test_submodule_match(
        self,
        checker: ForbiddenImportChecker,
    ) -> None:
        """サブモジュールの一致"""
        result = checker._is_forbidden(
            module="returns.unsafe.perform",
            forbidden_modules=["returns.unsafe"],
        )

        assert result is True

    def test_no_match(
        self,
        checker: ForbiddenImportChecker,
    ) -> None:
        """一致しない場合"""
        result = checker._is_forbidden(
            module="returns.result",
            forbidden_modules=["returns.unsafe"],
        )

        assert result is False

    def test_partial_name_no_match(
        self,
        checker: ForbiddenImportChecker,
    ) -> None:
        """部分一致 (前方一致でない) は禁止されない"""
        result = checker._is_forbidden(
            module="returns.unsafety",
            forbidden_modules=["returns.unsafe"],
        )

        # "returns.unsafety" は "returns.unsafe." で始まらないので許可
        assert result is False


class TestFindViolations:
    """_find_violations メソッドのテスト"""

    def test_detects_forbidden_import(
        self,
        checker: ForbiddenImportChecker,
    ) -> None:
        """禁止されたインポートを検出"""
        code = "from returns.unsafe import unsafe_perform_io"
        tree = ast.parse(code)

        violations = checker._find_violations(
            tree=tree,
            module_name="test_module",
            forbidden_modules=["returns.unsafe"],
            verbose=False,
        )

        # "returns.unsafe" と "returns.unsafe.unsafe_perform_io" の両方が検出される
        assert len(violations) >= 1
        assert ("test_module", "returns.unsafe", 1) in violations

    def test_detects_from_parent_import_submodule(
        self,
        checker: ForbiddenImportChecker,
    ) -> None:
        """'from returns import unsafe' 形式を検出"""
        code = "from returns import unsafe"
        tree = ast.parse(code)

        violations = checker._find_violations(
            tree=tree,
            module_name="test_module",
            forbidden_modules=["returns.unsafe"],
            verbose=False,
        )

        assert len(violations) == 1
        assert violations[0] == ("test_module", "returns.unsafe", 1)

    def test_detects_multiple_violations(
        self,
        checker: ForbiddenImportChecker,
    ) -> None:
        """複数の違反を検出"""
        code = """from returns.unsafe import unsafe_perform_io
import returns.unsafe
"""
        tree = ast.parse(code)

        violations = checker._find_violations(
            tree=tree,
            module_name="test_module",
            forbidden_modules=["returns.unsafe"],
            verbose=False,
        )

        # 2行あり、少なくとも2つの違反がある
        assert len(violations) >= 2
        lines_with_violations = {v[2] for v in violations}
        assert lines_with_violations == {1, 2}

    def test_allows_non_forbidden_import(
        self,
        checker: ForbiddenImportChecker,
    ) -> None:
        """許可されたインポートは違反として検出しない"""
        code = """from returns.result import Result
from returns.io import IOResult
"""
        tree = ast.parse(code)

        violations = checker._find_violations(
            tree=tree,
            module_name="test_module",
            forbidden_modules=["returns.unsafe"],
            verbose=False,
        )

        assert len(violations) == 0

    def test_handles_comma_separated_imports(
        self,
        checker: ForbiddenImportChecker,
    ) -> None:
        """カンマ区切りインポートの処理"""
        code = "import foo, bar.baz, qux"
        tree = ast.parse(code)

        violations = checker._find_violations(
            tree=tree,
            module_name="test_module",
            forbidden_modules=["foo", "bar.baz"],
            verbose=False,
        )

        assert len(violations) == 2
        modules = {v[1] for v in violations}
        assert modules == {"foo", "bar.baz"}


class TestRenderBrokenContract:
    """render_broken_contract メソッドのテスト"""

    def test_renders_single_violation(
        self,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """単一の違反を正しくレンダリング"""
        contract = ForbiddenExternalSubmoduleContract.__new__(
            ForbiddenExternalSubmoduleContract,
        )
        check = ContractCheck(
            kept=False,
            metadata={
                "violations": [
                    ("mymodule.foo", "returns.unsafe", 42),
                ],
            },
        )

        contract.render_broken_contract(check)

        captured = capsys.readouterr()
        lines = captured.out.splitlines()
        # ヘッダー行を確認
        assert any(
            "the following modules import forbidden external submodules" in line.lower()
            for line in lines
        )
        # 違反行を確認 (形式: "{module}:{line} -> {imported}")
        assert any("mymodule.foo:42 -> returns.unsafe" in line for line in lines)

    def test_renders_multiple_violations(
        self,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """複数の違反を正しくレンダリング"""
        contract = ForbiddenExternalSubmoduleContract.__new__(
            ForbiddenExternalSubmoduleContract,
        )
        check = ContractCheck(
            kept=False,
            metadata={
                "violations": [
                    ("module_a", "returns.unsafe", 10),
                    ("module_b.sub", "returns.unsafe", 25),
                ],
            },
        )

        contract.render_broken_contract(check)

        captured = capsys.readouterr()
        lines = captured.out.splitlines()
        # 違反行を確認 (形式: "{module}:{line} -> {imported}")
        assert any("module_a:10 -> returns.unsafe" in line for line in lines)
        assert any("module_b.sub:25 -> returns.unsafe" in line for line in lines)
