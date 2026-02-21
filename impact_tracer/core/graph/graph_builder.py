"""Dependency graph builder.

Layer: Engines (Layer 3)
Responsibility: Build module and symbol dependency graph from AST analysis artifacts.
Implements: PRD FR-DG-01, FR-DG-02 and Phase 1 Task 1.6.
"""

from __future__ import annotations

import networkx as nx

from impact_tracer.core.analyzer.python.call_graph_builder import CallGraphResult
from impact_tracer.core.analyzer.python.import_resolver import resolve_imports
from impact_tracer.models.graph import DependencyGraph, EdgeSource, GraphEdge, GraphNode, NodeLayer
from impact_tracer.models.symbol import SymbolTable


def build_dependency_graph(symbol_table: SymbolTable, call_graph: CallGraphResult | None = None) -> DependencyGraph:
	"""Build module and symbol dependency graph from extracted AST data.

	Args:
		symbol_table: Parsed symbols and imports.
		call_graph: Optional call graph result.

	Returns:
		DependencyGraph: Serializable dependency graph model.
	"""
	graph_nodes: dict[str, GraphNode] = {}
	graph_edges: list[GraphEdge] = []

	for file_table in symbol_table.files:
		module_node_id = f"module:{file_table.module}"
		graph_nodes[module_node_id] = GraphNode(
			id=module_node_id,
			label=file_table.module,
			layer=NodeLayer.MODULE,
			metadata={"file_path": file_table.file_path},
		)

		for symbol in file_table.symbols:
			graph_nodes[symbol.id] = GraphNode(
				id=symbol.id,
				label=symbol.name,
				layer=NodeLayer.SYMBOL,
				metadata={
					"symbol_type": symbol.type.value,
					"module": symbol.module,
					"line_start": symbol.line_start,
					"line_end": symbol.line_end,
				},
			)

		resolution = resolve_imports(file_table.module, file_table.imports)
		for target in resolution.import_map.values():
			imported_module = _to_module_name(target)
			imported_node_id = f"module:{imported_module}"
			graph_nodes.setdefault(
				imported_node_id,
				GraphNode(id=imported_node_id, label=imported_module, layer=NodeLayer.MODULE),
			)
			graph_edges.append(
				GraphEdge(
					source=module_node_id,
					target=imported_node_id,
					edge_type="IMPORT",
					source_type=EdgeSource.AST,
					confidence=1.0,
				)
			)

	if call_graph is not None:
		for caller_id, callee_id in call_graph.edges:
			graph_edges.append(
				GraphEdge(
					source=caller_id,
					target=callee_id,
					edge_type="CALL",
					source_type=EdgeSource.AST,
					confidence=1.0,
				)
			)

	return DependencyGraph(nodes=list(graph_nodes.values()), edges=graph_edges)


def to_networkx(dependency_graph: DependencyGraph) -> nx.DiGraph:
	"""Convert DependencyGraph model into NetworkX directed graph.

	Args:
		dependency_graph: Serializable graph model.

	Returns:
		nx.DiGraph: Directed graph with node/edge attributes.
	"""
	graph = nx.DiGraph()
	for node in dependency_graph.nodes:
		graph.add_node(node.id, label=node.label, layer=node.layer.value, **node.metadata)
	for edge in dependency_graph.edges:
		graph.add_edge(
			edge.source,
			edge.target,
			edge_type=edge.edge_type,
			source=edge.source_type.value,
			confidence=edge.confidence,
			**edge.metadata,
		)
	return graph


def _to_module_name(import_target: str) -> str:
	if import_target.endswith(".*"):
		return import_target[:-2]
	parts = import_target.split(".")
	if len(parts) <= 1:
		return import_target
	return ".".join(parts[:-1])
