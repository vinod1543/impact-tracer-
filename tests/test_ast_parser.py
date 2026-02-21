"""Unit tests for Python AST parser.

Phase 1, Task 1.9: Validate symbol and import extraction behavior.
"""

from __future__ import annotations

from impact_tracer.core.analyzer.python.ast_parser import PythonAstParser
from impact_tracer.models.symbol import ImportType, SymbolType


def test_parse_file_extracts_functions_classes_methods_and_decorators(tmp_path) -> None:
    """Parser extracts top-level function, class, and methods with metadata."""
    source = """
from app.services import billing as bill

def top_level(user_id: str) -> bool:
    return True

class PaymentService:
    @staticmethod
    def validate(amount: float) -> bool:
        return amount > 0
"""
    project_root = tmp_path
    target_file = project_root / "payments.py"
    target_file.write_text(source, encoding="utf-8")

    parser = PythonAstParser()
    file_table = parser.parse_file(target_file, project_root)

    assert file_table.parse_error is None
    assert file_table.module == "payments"

    extracted_types = {item.type for item in file_table.symbols}
    assert SymbolType.FUNCTION in extracted_types
    assert SymbolType.CLASS in extracted_types
    assert SymbolType.METHOD in extracted_types

    method_symbol = next(item for item in file_table.symbols if item.id.endswith("PaymentService.validate"))
    assert "staticmethod" in method_symbol.decorators
    assert method_symbol.signature == "(amount) -> bool"


def test_parse_file_extracts_import_and_from_import(tmp_path) -> None:
    """Parser captures both import styles with aliases and levels."""
    source = """
import json as js
from .helpers import format_amount as fmt
"""
    project_root = tmp_path
    pkg_dir = project_root / "pkg"
    pkg_dir.mkdir()
    target_file = pkg_dir / "module.py"
    target_file.write_text(source, encoding="utf-8")

    parser = PythonAstParser()
    file_table = parser.parse_file(target_file, project_root)

    assert len(file_table.imports) == 2
    direct_import = file_table.imports[0]
    from_import = file_table.imports[1]

    assert direct_import.import_type == ImportType.IMPORT
    assert direct_import.symbols[0].name == "json"
    assert direct_import.symbols[0].alias == "js"

    assert from_import.import_type == ImportType.FROM_IMPORT
    assert from_import.module == "helpers"
    assert from_import.level == 1
    assert from_import.symbols[0].name == "format_amount"
    assert from_import.symbols[0].alias == "fmt"


def test_parse_file_handles_syntax_error_without_crash(tmp_path) -> None:
    """Parser returns parse_error and empty symbol lists for invalid files."""
    source = """
def broken(
    return 1
"""
    project_root = tmp_path
    target_file = project_root / "broken.py"
    target_file.write_text(source, encoding="utf-8")

    parser = PythonAstParser()
    file_table = parser.parse_file(target_file, project_root)

    assert file_table.parse_error is not None
    assert file_table.symbols == []
    assert file_table.imports == []


def test_parse_project_skips_virtual_environment_paths(tmp_path) -> None:
    """Project parser excludes .venv files from analysis."""
    project_root = tmp_path
    (project_root / "main.py").write_text("def keep():\n    return 1\n", encoding="utf-8")

    venv_path = project_root / ".venv" / "lib"
    venv_path.mkdir(parents=True)
    (venv_path / "ignored.py").write_text("def skip():\n    return 2\n", encoding="utf-8")

    parser = PythonAstParser()
    result = parser.parse_project(str(project_root))

    parsed_files = {item.file_path for item in result.files}
    assert any(path.endswith("main.py") for path in parsed_files)
    assert all(".venv" not in path for path in parsed_files)
