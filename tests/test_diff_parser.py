"""Unit tests for diff parser and diff-to-symbol mapping.

Phase 2 Task 2.10: core, edge, failure and invalid input handling.
"""

from __future__ import annotations

from impact_tracer.core.analyzer.python.ast_parser import PythonAstParser
from impact_tracer.core.diff.diff_parser import map_diff_to_symbols, parse_unified_diff
from impact_tracer.models.diff import ChangeType


def test_parse_unified_diff_classifies_signature_change() -> None:
    """Parser classifies function signature modifications correctly."""
    diff = """--- a/a.py
+++ b/a.py
@@ -1,1 +1,1 @@
-def validate(x):
+def validate(x, strict=False):
"""
    result = parse_unified_diff(diff)

    assert result.files_changed == ["a.py"]
    assert len(result.hunks) == 1
    assert result.hunks[0].semantic_change_type == ChangeType.SIGNATURE_CHANGE


def test_parse_unified_diff_classifies_docstring_change() -> None:
    """Parser classifies docstring-only modifications as low-risk change type."""
    diff = """--- a/a.py
+++ b/a.py
@@ -2,1 +2,1 @@
-    \"\"\"Old text\"\"\"
+    \"\"\"New text\"\"\"
"""
    result = parse_unified_diff(diff)
    assert result.hunks[0].semantic_change_type == ChangeType.DOCSTRING_CHANGE


def test_parse_unified_diff_handles_empty_input() -> None:
    """Parser handles empty diff input without errors."""
    result = parse_unified_diff("")
    assert result.files_changed == []
    assert result.hunks == []
    assert result.changed_symbols == []


def test_map_diff_to_symbols_maps_by_line_overlap(tmp_path) -> None:
    """Mapper resolves changed symbols when hunk overlaps symbol line ranges."""
    source = """
def alpha():
    return 1

def beta():
    return alpha()
"""
    file_path = tmp_path / "mod.py"
    file_path.write_text(source, encoding="utf-8")

    parser = PythonAstParser()
    symbol_table = parser.parse_project(str(tmp_path))

    diff = """--- a/mod.py
+++ b/mod.py
@@ -4,1 +4,1 @@
-def beta():
+def beta(x=1):
"""
    diff_result = parse_unified_diff(diff)
    changed_symbols = map_diff_to_symbols(diff_result, symbol_table)

    assert any(symbol.symbol_id.endswith("mod.beta") for symbol in changed_symbols)
    assert changed_symbols[0].change_type == ChangeType.SIGNATURE_CHANGE
