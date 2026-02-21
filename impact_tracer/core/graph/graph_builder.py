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
from impact_tracer.models.infra import InfraTopology
from impact_tracer.models.runtime import RuntimeNodeType, RuntimeTraceGraph
from impact_tracer.models.symbol import SymbolTable, SymbolType


def build_dependency_graph(
	symbol_table: SymbolTable,
	call_graph: CallGraphResult | None = None,
	infra_topology: InfraTopology | None = None,
	runtime_graph: RuntimeTraceGraph | None = None,
) -> DependencyGraph:
	"""Build module and symbol dependency graph from extracted AST data.

	Args:
		symbol_table: Parsed symbols and imports.
		call_graph: Optional call graph result.
		infra_topology: Optional infrastructure topology from config parsers.
		runtime_graph: Optional runtime topology from trace/log miners.

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
				layer=_symbol_layer(symbol.type),
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

	if runtime_graph is not None:
		for runtime_node in runtime_graph.nodes:
			node_id = _external_node_id(runtime_node.id, "runtime")
			graph_nodes[node_id] = GraphNode(
				id=node_id,
				label=runtime_node.label,
				layer=_runtime_layer(runtime_node.node_type),
				metadata={
					"runtime_type": runtime_node.node_type.value,
					**runtime_node.metadata,
				},
			)

		for runtime_edge in runtime_graph.edges:
			edge_metadata = dict(runtime_edge.metadata)
			if runtime_edge.call_count is not None:
				edge_metadata["call_count"] = runtime_edge.call_count
			if runtime_edge.latency_ms is not None:
				edge_metadata["latency_ms"] = runtime_edge.latency_ms

			graph_edges.append(
				GraphEdge(
					source=_external_node_id(runtime_edge.source, "runtime"),
					target=_external_node_id(runtime_edge.target, "runtime"),
					edge_type=runtime_edge.edge_type,
					source_type=EdgeSource.RUNTIME,
					confidence=runtime_edge.confidence,
					metadata=edge_metadata,
				)
			)

	if infra_topology is not None:
		for infra_node in infra_topology.nodes:
			node_id = _external_node_id(infra_node.id, "infra")
			node_metadata = dict(infra_node.metadata)
			node_metadata["infra_type"] = infra_node.node_type.value
			if infra_node.provider is not None:
				node_metadata["provider"] = infra_node.provider

			graph_nodes[node_id] = GraphNode(
				id=node_id,
				label=infra_node.label,
				layer=NodeLayer.INFRA,
				metadata=node_metadata,
			)

		for infra_edge in infra_topology.edges:
			graph_edges.append(
				GraphEdge(
					source=_external_node_id(infra_edge.source, "infra"),
					target=_external_node_id(infra_edge.target, "infra"),
					edge_type=infra_edge.edge_type,
					source_type=EdgeSource.CONFIG,
					confidence=infra_edge.confidence,
					metadata=infra_edge.metadata,
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


def _external_node_id(raw_node_id: str, namespace: str) -> str:
	if ":" in raw_node_id:
		return raw_node_id
	return f"{namespace}:{raw_node_id}"


def _runtime_layer(node_type: RuntimeNodeType) -> NodeLayer:
	if node_type == RuntimeNodeType.SERVICE:
		return NodeLayer.SERVICE
	if node_type == RuntimeNodeType.TABLE:
		return NodeLayer.TABLE
	return NodeLayer.SYMBOL


def _symbol_layer(symbol_type: SymbolType) -> NodeLayer:
	if symbol_type == SymbolType.API_ENDPOINT:
		return NodeLayer.SERVICE
	return NodeLayer.SYMBOL
