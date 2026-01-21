"""カスタムimport-linterコントラクト: 外部パッケージのサブモジュールを禁止

grimp (import-linter が使用するライブラリ) は外部パッケージをトップレベルでのみ
追跡するため、外部パッケージのサブモジュール (例: returns.unsafe) を区別できない。
このコントラクトは AST を直接解析して、実際のインポート文を検査する。
"""

from __future__ import annotations

import ast
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from importlinter import Contract, ContractCheck, fields, output

if TYPE_CHECKING:
    from collections.abc import Callable

    from grimp import ImportGraph

    # モジュール名をファイルパスに変換する関数の型
    ModulePathResolver = Callable[[str], Path | None]


def default_module_path_resolver(module: str) -> Path | None:
    """デフォルトのモジュールパス解決関数

    sys.path を走査して、モジュール名に対応するファイルパスを返す。
    """
    for path in sys.path:
        base = Path(path)
        module_path = base / module.replace(".", "/")

        # パッケージ (__init__.py) の場合
        init_file = module_path / "__init__.py"
        if init_file.exists():
            return init_file

        # モジュール (.py)
        py_file = module_path.with_suffix(".py")
        if py_file.exists():
            return py_file

    return None


@dataclass(frozen=True)
class ForbiddenImportChecker:
    """外部パッケージのサブモジュールへのインポートを検出するチェッカー

    AST を直接解析して、指定されたサブモジュールへのインポートを検出する。
    依存性注入によりテスト可能な設計。
    """

    module_path_resolver: ModulePathResolver

    def find_violations(
        self,
        source_modules: list[str],
        forbidden_modules: list[str],
        graph: ImportGraph,
        *,
        verbose: bool,
    ) -> list[tuple[str, str, int]]:
        """指定されたソースモジュールから禁止モジュールへのインポートを検出"""
        violations: list[tuple[str, str, int]] = []

        for source_module in source_modules:
            descendants = graph.find_descendants(source_module)
            modules_to_check = {source_module} | descendants

            for module in modules_to_check:
                file_path = self.module_path_resolver(module)
                if file_path is None or not file_path.exists():
                    continue

                module_violations = self._check_file(
                    file_path=file_path,
                    module_name=module,
                    forbidden_modules=forbidden_modules,
                    verbose=verbose,
                )
                violations.extend(module_violations)

        return violations

    def _check_file(
        self,
        file_path: Path,
        module_name: str,
        forbidden_modules: list[str],
        *,
        verbose: bool,
    ) -> list[tuple[str, str, int]]:
        """ファイルの AST を解析してインポートを検査"""
        try:
            source = file_path.read_text(encoding="utf-8")
            tree = ast.parse(source)
        except OSError as e:
            if verbose:
                output.print(f"Warning: Cannot read {file_path}: {e}")
            return []
        except SyntaxError as e:
            if verbose:
                output.print(f"Warning: Syntax error in {file_path}: {e}")
            return []

        return self._find_violations(
            tree=tree,
            module_name=module_name,
            forbidden_modules=forbidden_modules,
            verbose=verbose,
        )

    def _find_violations(
        self,
        tree: ast.AST,
        module_name: str,
        forbidden_modules: list[str],
        *,
        verbose: bool,
    ) -> list[tuple[str, str, int]]:
        """AST から違反を検出"""
        violations: list[tuple[str, str, int]] = []

        for node in ast.walk(tree):
            if not isinstance(node, (ast.Import, ast.ImportFrom)):
                continue

            for imported_module in self._get_imported_modules(node):
                if self._is_forbidden(imported_module, forbidden_modules):
                    violations.append((module_name, imported_module, node.lineno))
                    if verbose:
                        output.print(
                            f"Found violation: {module_name}:{node.lineno} "
                            f"imports {imported_module}",
                        )

        return violations

    def _is_forbidden(self, module: str, forbidden_modules: list[str]) -> bool:
        """モジュールが禁止リストに含まれるかチェック"""
        return any(
            module == forbidden or module.startswith(f"{forbidden}.")
            for forbidden in forbidden_modules
        )

    def _get_imported_modules(
        self,
        node: ast.Import | ast.ImportFrom,
    ) -> list[str]:
        """AST ノードからインポートされたモジュール名のリストを取得

        - ast.Import: 'import foo, bar.baz' -> ['foo', 'bar.baz']
        - ast.ImportFrom: 'from foo.bar import baz' -> ['foo.bar', 'foo.bar.baz']
        - ast.ImportFrom: 'from foo import bar' -> ['foo', 'foo.bar']
        """
        if isinstance(node, ast.Import):
            return [alias.name for alias in node.names]
        if isinstance(node, ast.ImportFrom) and node.module:
            # "from foo.bar import baz, qux" の場合、
            # "foo.bar" と "foo.bar.baz", "foo.bar.qux" をすべて返す
            return [
                node.module,
                *[f"{node.module}.{alias.name}" for alias in node.names],
            ]
        return []


class ForbiddenExternalSubmoduleContract(Contract):
    """外部パッケージのサブモジュールへのインポートを禁止するコントラクト

    使用例:
        [[tool.importlinter.contracts]]
        name = "unsafe_perform_io is only allowed in infrastructure"
        type = "forbidden_external_submodule"
        source_modules = [
            "confengine_to_youtube.domain",
            "confengine_to_youtube.usecases",
            "confengine_to_youtube.adapters",
        ]
        forbidden_external_modules = [
            "returns.unsafe",
        ]
    """

    type_name = "forbidden_external_submodule"

    source_modules = fields.ListField(subfield=fields.StringField())
    forbidden_external_modules = fields.ListField(subfield=fields.StringField())

    def check(
        self,
        graph: ImportGraph,
        verbose: bool,  # noqa: FBT001
    ) -> ContractCheck:
        checker = ForbiddenImportChecker(
            module_path_resolver=default_module_path_resolver,
        )
        violations = checker.find_violations(
            source_modules=list(self.source_modules),  # type: ignore[call-overload]
            forbidden_modules=list(self.forbidden_external_modules),  # type: ignore[call-overload]
            graph=graph,
            verbose=verbose,
        )

        return ContractCheck(
            kept=len(violations) == 0,
            metadata={"violations": violations},
        )

    def render_broken_contract(self, check: ContractCheck) -> None:
        output.print_error(
            "The following modules import forbidden external submodules:",
        )
        output.new_line()
        for module, imported, line in check.metadata["violations"]:
            output.indent_cursor()
            output.print_error(f"{module}:{line} -> {imported}")
            output.new_line()
