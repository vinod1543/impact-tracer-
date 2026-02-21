"""Unit tests for call graph builder.

Phase 1, Task 1.5: Validate caller/callee extraction and unresolved-call accounting.
"""

from __future__ import annotations

from impact_tracer.core.analyzer.python.ast_parser import PythonAstParser
from impact_tracer.core.analyzer.python.call_graph_builder import build_call_edges


def test_build_call_edges_resolves_direct_and_attribute_calls(tmp_path) -> None:
    """Builder resolves direct function calls and method attribute calls."""
    source = """
def helper() -> None:
    return None

class Service:
    def run(self) -> None:
        helper()

def entrypoint() -> None:
    service = Service()
    service.run()
"""
    module_path = tmp_path / "module.py"
    module_path.write_text(source, encoding="utf-8")

    parser = PythonAstParser()
    symbol_table = parser.parse_project(str(tmp_path))
    result = build_call_edges(symbol_table)

    assert ("module.Service.run", "module.helper") in result.edges
    assert ("module.entrypoint", "module.Service.run") in result.edges
    assert result.total_calls >= 2
    assert result.call_resolution_rate > 0.0


def test_build_call_edges_tracks_unresolved_calls(tmp_path) -> None:
    """Builder increments unresolved counter when callee cannot be mapped."""
    source = """
def call_unknown() -> None:
    missing_symbol()
"""
    module_path = tmp_path / "missing.py"
    module_path.write_text(source, encoding="utf-8")

    parser = PythonAstParser()
    symbol_table = parser.parse_project(str(tmp_path))
    result = build_call_edges(symbol_table)

    assert result.total_calls == 1
    assert result.unresolved_calls == 1
    assert result.edges == []


def test_build_call_edges_skips_files_with_parse_error(tmp_path) -> None:
    """Builder safely skips files marked with parse errors in symbol table."""
    good_source = """
def ok() -> None:
    return None
"""
    bad_source = """
def broken(
    return 1
"""

    (tmp_path / "good.py").write_text(good_source, encoding="utf-8")
    (tmp_path / "bad.py").write_text(bad_source, encoding="utf-8")

    parser = PythonAstParser()
    symbol_table = parser.parse_project(str(tmp_path))
    result = build_call_edges(symbol_table)

    assert result.total_calls == 0
    assert result.unresolved_calls == 0
    assert result.call_resolution_rate == 1.0
