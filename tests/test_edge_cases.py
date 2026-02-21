"""Edge case tests for stabilization phase."""

from __future__ import annotations

from pathlib import Path

from impact_tracer.core.orchestrator import analyze


def test_edge_empty_diff_returns_valid_report() -> None:
    """Empty diff should not crash and should return zero file changes."""
    report = analyze("", "demo/payments_service", enable_llm=False)
    assert report.diff_summary.files_changed == 0


def test_edge_no_change_diff_headers_only() -> None:
    """Diff with headers but no hunks should still return valid report."""
    diff_text = """--- a/demo/payments_service/validator.py
+++ b/demo/payments_service/validator.py
"""
    report = analyze(diff_text, "demo/payments_service", enable_llm=False)
    assert report.diff_summary.hunks == 0


def test_edge_syntax_error_file_project_does_not_crash(tmp_path) -> None:
    """Project containing syntax error files should be analyzed gracefully."""
    (tmp_path / "good.py").write_text("def ok():\n    return 1\n", encoding="utf-8")
    (tmp_path / "broken.py").write_text("def broken(\n    return 1\n", encoding="utf-8")

    diff_text = """--- a/good.py
+++ b/good.py
@@ -1,1 +1,1 @@
-def ok():
+def ok(x=1):
"""
    report = analyze(diff_text, str(tmp_path), enable_llm=False)
    assert report.metadata.total_files >= 1


def test_edge_circular_import_project_no_infinite_loop(tmp_path) -> None:
    """Circular import projects should complete analysis without infinite traversal."""
    (tmp_path / "a.py").write_text("from b import f2\ndef f1():\n    return f2()\n", encoding="utf-8")
    (tmp_path / "b.py").write_text("from a import f1\ndef f2():\n    return 1\n", encoding="utf-8")

    diff_text = """--- a/a.py
+++ b/a.py
@@ -2,1 +2,1 @@
-def f1():
+def f1(x=0):
"""
    report = analyze(diff_text, str(tmp_path), enable_llm=False)
    assert report.diff_summary.changed_symbols >= 1
