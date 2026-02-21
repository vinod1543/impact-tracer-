"""Unit tests for propagation engine.

Phase 2 Task 2.10: core, edge, and failure-safe traversal behavior.
"""

from __future__ import annotations

import networkx as nx

from impact_tracer.core.propagation.propagator import propagate_changes
from impact_tracer.models.symbol import Symbol, SymbolType


def _symbol(symbol_id: str) -> Symbol:
    return Symbol(
        id=symbol_id,
        name=symbol_id.split(".")[-1],
        type=SymbolType.FUNCTION,
        module=symbol_id.split(".")[0],
        file_path=f"{symbol_id.split('.')[0]}.py",
        line_start=1,
        line_end=2,
        is_public=True,
    )


def test_propagate_changes_direct_and_transitive() -> None:
    """Propagation marks depth 1 as direct and depth 2+ as transitive."""
    graph = nx.DiGraph()
    graph.add_edge("b.func", "a.func")
    graph.add_edge("c.func", "b.func")

    symbol_index = {
        "a.func": _symbol("a.func"),
        "b.func": _symbol("b.func"),
        "c.func": _symbol("c.func"),
    }

    affected, _ = propagate_changes(graph, ["a.func"], symbol_index)

    depth_map = {item.symbol.id: item.propagation_depth for item in affected}
    assert depth_map["b.func"] == 1
    assert depth_map["c.func"] == 2


def test_propagate_changes_handles_cycles_without_infinite_loop() -> None:
    """Propagation safely handles cycles using visited states."""
    graph = nx.DiGraph()
    graph.add_edge("a.func", "b.func")
    graph.add_edge("b.func", "a.func")

    symbol_index = {
        "a.func": _symbol("a.func"),
        "b.func": _symbol("b.func"),
    }

    affected, _ = propagate_changes(graph, ["a.func"], symbol_index, max_depth=5)

    assert len(affected) >= 1
    assert any(item.symbol.id == "b.func" for item in affected)


def test_propagate_changes_invalid_symbol_id_is_ignored() -> None:
    """Propagation ignores changed symbols that do not exist in graph."""
    graph = nx.DiGraph()
    symbol_index = {}

    affected, paths = propagate_changes(graph, ["missing.symbol"], symbol_index)
    assert affected == []
    assert paths == []


def test_propagate_changes_handles_multiple_roots_without_cross_root_skip() -> None:
    """Traversal should keep per-root visited state and include dependents of each root."""
    graph = nx.DiGraph()
    graph.add_edge("x.dep", "a.root")
    graph.add_edge("x.dep", "b.root")

    symbol_index = {
        "a.root": _symbol("a.root"),
        "b.root": _symbol("b.root"),
        "x.dep": _symbol("x.dep"),
    }

    affected, _ = propagate_changes(graph, ["a.root", "b.root"], symbol_index)
    affected_ids = {item.symbol.id for item in affected}
    assert "x.dep" in affected_ids
