"""Graph query helpers.

Layer: Engines (Layer 3)
Responsibility: Query graph neighborhood and transitive relationships.
Implements: PRD FR-DG-07 and Phase 1 Task 1.8.
"""

from __future__ import annotations

import networkx as nx


def predecessors(graph: nx.DiGraph, node_id: str) -> list[str]:
	"""Return direct predecessors for a node.

	Args:
		graph: Target directed graph.
		node_id: Node identifier.

	Returns:
		list[str]: Sorted predecessor node ids.
	"""
	if node_id not in graph:
		return []
	return sorted(graph.predecessors(node_id))


def descendants(graph: nx.DiGraph, node_id: str) -> list[str]:
	"""Return transitive descendants for a node.

	Args:
		graph: Target directed graph.
		node_id: Node identifier.

	Returns:
		list[str]: Sorted descendant node ids.
	"""
	if node_id not in graph:
		return []
	return sorted(nx.descendants(graph, node_id))


def ancestors(graph: nx.DiGraph, node_id: str) -> list[str]:
	"""Return transitive ancestors for a node.

	Args:
		graph: Target directed graph.
		node_id: Node identifier.

	Returns:
		list[str]: Sorted ancestor node ids.
	"""
	if node_id not in graph:
		return []
	return sorted(nx.ancestors(graph, node_id))


def shortest_path(graph: nx.DiGraph, source_id: str, target_id: str) -> list[str]:
	"""Return shortest path between two nodes.

	Args:
		graph: Target directed graph.
		source_id: Source node id.
		target_id: Target node id.

	Returns:
		list[str]: Shortest path node ids, or empty list when disconnected.
	"""
	if source_id not in graph or target_id not in graph:
		return []
	try:
		return nx.shortest_path(graph, source=source_id, target=target_id)
	except nx.NetworkXNoPath:
		return []
