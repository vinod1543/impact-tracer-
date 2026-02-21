"""Graph persistence helpers.

Layer: Engines (Layer 3)
Responsibility: Persist and restore dependency graphs.
Implements: PRD FR-DG-06 and Phase 1 Task 1.7.
"""

from __future__ import annotations

from pathlib import Path

import networkx as nx

from impact_tracer.core.graph.graph_builder import to_networkx
from impact_tracer.models.graph import DependencyGraph


def save_graph_model(dependency_graph: DependencyGraph, output_path: str) -> None:
	"""Save DependencyGraph model to JSON file.

	Args:
		dependency_graph: Graph model to persist.
		output_path: Destination file path.
	"""
	path = Path(output_path)
	path.parent.mkdir(parents=True, exist_ok=True)
	path.write_text(dependency_graph.model_dump_json(indent=2), encoding="utf-8")


def load_graph_model(input_path: str) -> DependencyGraph:
	"""Load DependencyGraph model from JSON file.

	Args:
		input_path: Source file path.

	Returns:
		DependencyGraph: Restored graph model.
	"""
	payload = Path(input_path).read_text(encoding="utf-8")
	return DependencyGraph.model_validate_json(payload)


def save_networkx_graph(dependency_graph: DependencyGraph, output_path: str) -> None:
	"""Save dependency graph as NetworkX pickle.

	Args:
		dependency_graph: Graph model to convert and persist.
		output_path: Destination pickle path.
	"""
	nx_graph = to_networkx(dependency_graph)
	path = Path(output_path)
	path.parent.mkdir(parents=True, exist_ok=True)
	nx.write_gpickle(nx_graph, path)


def load_networkx_graph(input_path: str) -> nx.DiGraph:
	"""Load NetworkX graph from pickle file.

	Args:
		input_path: Pickle path.

	Returns:
		nx.DiGraph: Restored directed graph.
	"""
	return nx.read_gpickle(Path(input_path))
