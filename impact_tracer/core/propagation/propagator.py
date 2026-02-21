"""Change propagation engine.

Layer: Engines (Layer 3)
Responsibility: Traverse dependency graph from changed symbols to affected dependents.
Implements: Phase 2 Task 2.5.
"""

from __future__ import annotations

from collections import deque

import networkx as nx

from impact_tracer.models.impact import AffectedSymbol, PropagationChangeType, PropagationPath
from impact_tracer.models.symbol import Symbol


def propagate_changes(
	graph: nx.DiGraph,
	changed_symbol_ids: list[str],
	symbol_index: dict[str, Symbol],
	max_depth: int | None = None,
) -> tuple[list[AffectedSymbol], list[PropagationPath]]:
	"""Propagate changes through graph predecessors using BFS.

	Args:
		graph: Dependency graph.
		changed_symbol_ids: Root changed symbol ids.
		symbol_index: Symbol lookup by id.
		max_depth: Optional max traversal depth.

	Returns:
		tuple[list[AffectedSymbol], list[PropagationPath]]: Affected symbols and propagation paths.
	"""
	results: dict[str, AffectedSymbol] = {}
	paths: list[PropagationPath] = []
	queue: deque[tuple[str, int, list[str], str]] = deque()
	visited: set[tuple[str, str]] = set()

	for root_symbol in changed_symbol_ids:
		queue.append((root_symbol, 0, [root_symbol], root_symbol))

	while queue:
		node_id, depth, path, source_symbol_id = queue.popleft()
		state = (source_symbol_id, node_id)
		if state in visited:
			continue
		visited.add(state)

		if max_depth is not None and depth >= max_depth:
			continue

		if node_id not in graph:
			continue

		for predecessor in graph.predecessors(node_id):
			next_depth = depth + 1
			new_path = path + [predecessor]

			if predecessor in symbol_index and predecessor not in changed_symbol_ids:
				previous = results.get(predecessor)
				if previous is None or previous.propagation_depth > next_depth:
					results[predecessor] = AffectedSymbol(
						symbol=symbol_index[predecessor],
						propagation_depth=next_depth,
						propagation_path=new_path,
						change_type=(
							PropagationChangeType.DIRECT if next_depth == 1 else PropagationChangeType.TRANSITIVE
						),
					)
				paths.append(
					PropagationPath(
						source_symbol_id=source_symbol_id,
						target_symbol_id=predecessor,
						path=new_path,
					)
				)

			queue.append((predecessor, next_depth, new_path, source_symbol_id))

	return sorted(results.values(), key=lambda item: (item.propagation_depth, item.symbol.id)), paths
