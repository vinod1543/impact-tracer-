"""Unit tests for dependency graph builder and query functions.

Phase 1, Tasks 1.6, 1.7, 1.8, 1.10.
"""

from __future__ import annotations

from impact_tracer.core.analyzer.python.ast_parser import PythonAstParser
from impact_tracer.core.analyzer.python.call_graph_builder import build_call_edges
from impact_tracer.core.graph.graph_builder import build_dependency_graph, to_networkx
from impact_tracer.core.graph.graph_query import ancestors, descendants, predecessors, shortest_path
from impact_tracer.core.graph.graph_store import (
    load_graph_model,
    save_graph_model,
)
from impact_tracer.models.graph import EdgeSource
from impact_tracer.models.infra import InfraEdge, InfraNode, InfraNodeType, InfraTopology
from impact_tracer.models.runtime import RuntimeEdge, RuntimeNode, RuntimeNodeType, RuntimeTraceGraph


def test_graph_builder_creates_module_and_symbol_edges(tmp_path) -> None:
    """Builder creates import and call edges from a 3-module fixture."""
    (tmp_path / "a.py").write_text(
        "from b import helper\n\n"
        "def start():\n"
        "    helper()\n",
        encoding="utf-8",
    )
    (tmp_path / "b.py").write_text(
        "from c import ping\n\n"
        "def helper():\n"
        "    ping()\n",
        encoding="utf-8",
    )
    (tmp_path / "c.py").write_text(
        "def ping():\n"
        "    return None\n",
        encoding="utf-8",
    )

    parser = PythonAstParser()
    symbol_table = parser.parse_project(str(tmp_path))
    call_graph = build_call_edges(symbol_table)
    dependency_graph = build_dependency_graph(symbol_table, call_graph)

    import_edges = [edge for edge in dependency_graph.edges if edge.edge_type == "IMPORT"]
    call_edges = [edge for edge in dependency_graph.edges if edge.edge_type == "CALL"]
    contains_edges = [edge for edge in dependency_graph.edges if edge.edge_type == "CONTAINS"]

    assert len(dependency_graph.nodes) >= 6
    assert len(import_edges) >= 2
    assert ("a.start", "b.helper") in call_graph.edges
    assert len(call_edges) >= 2
    assert len(contains_edges) >= 3

    edge_keys = {(edge.source, edge.target, edge.edge_type, edge.source_type) for edge in dependency_graph.edges}
    assert len(edge_keys) == len(dependency_graph.edges)


def test_graph_query_functions_return_expected_relationships(tmp_path) -> None:
    """Graph query helpers return direct and transitive relationships."""
    (tmp_path / "alpha.py").write_text(
        "from beta import b\n\n"
        "def a():\n"
        "    b()\n",
        encoding="utf-8",
    )
    (tmp_path / "beta.py").write_text(
        "from gamma import c\n\n"
        "def b():\n"
        "    c()\n",
        encoding="utf-8",
    )
    (tmp_path / "gamma.py").write_text("def c():\n    return None\n", encoding="utf-8")

    parser = PythonAstParser()
    symbol_table = parser.parse_project(str(tmp_path))
    call_graph = build_call_edges(symbol_table)
    dependency_graph = build_dependency_graph(symbol_table, call_graph)
    nx_graph = to_networkx(dependency_graph)

    assert predecessors(nx_graph, "gamma.c") == ["beta.b"]
    assert "gamma.c" in descendants(nx_graph, "alpha.a")
    assert "alpha.a" in ancestors(nx_graph, "gamma.c")
    assert shortest_path(nx_graph, "alpha.a", "gamma.c") == ["alpha.a", "beta.b", "gamma.c"]


def test_graph_store_json_round_trip(tmp_path) -> None:
    """Graph store can persist and load dependency model losslessly."""
    (tmp_path / "module.py").write_text("def run():\n    return None\n", encoding="utf-8")

    parser = PythonAstParser()
    symbol_table = parser.parse_project(str(tmp_path))
    dependency_graph = build_dependency_graph(symbol_table, build_call_edges(symbol_table))

    output_path = tmp_path / "graph.json"
    save_graph_model(dependency_graph, str(output_path))
    loaded_graph = load_graph_model(str(output_path))

    assert len(loaded_graph.nodes) == len(dependency_graph.nodes)
    assert len(loaded_graph.edges) == len(dependency_graph.edges)


def test_graph_builder_merges_static_runtime_and_infra_into_unified_graph(tmp_path) -> None:
    """Builder creates one graph containing static, runtime, and infra layers."""
    (tmp_path / "app.py").write_text(
        "def helper():\n"
        "    return True\n\n"
        "def process_payment():\n"
        "    return helper()\n",
        encoding="utf-8",
    )

    parser = PythonAstParser()
    symbol_table = parser.parse_project(str(tmp_path))

    runtime_graph = RuntimeTraceGraph(
        nodes=[
            RuntimeNode(id="payments-api", label="payments-api", node_type=RuntimeNodeType.SERVICE),
            RuntimeNode(id="orders-db", label="orders-db", node_type=RuntimeNodeType.TABLE),
        ],
        edges=[
            RuntimeEdge(source="payments-api", target="orders-db", edge_type="READS", call_count=12, latency_ms=3.7),
        ],
    )

    infra_topology = InfraTopology(
        nodes=[
            InfraNode(id="k8s-service", label="payments-service", node_type=InfraNodeType.SERVICE, provider="k8s"),
            InfraNode(id="redis-cache", label="redis-cache", node_type=InfraNodeType.QUEUE, provider="k8s"),
        ],
        edges=[InfraEdge(source="k8s-service", target="redis-cache", edge_type="DEPENDS_ON")],
    )

    unified_graph = build_dependency_graph(
        symbol_table,
        build_call_edges(symbol_table),
        infra_topology=infra_topology,
        runtime_graph=runtime_graph,
    )

    node_ids = {node.id for node in unified_graph.nodes}
    edge_sources = {edge.source_type for edge in unified_graph.edges}

    assert "runtime:payments-api" in node_ids
    assert "infra:k8s-service" in node_ids
    assert EdgeSource.AST in edge_sources
    assert EdgeSource.RUNTIME in edge_sources
    assert EdgeSource.CONFIG in edge_sources
