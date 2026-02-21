"""Interactive graph visualizer.

Layer: Interfaces/Output (Layer 5)
Responsibility: Export dynamic interactive graph HTML for impact report exploration.
Implements: Phase 4 graph visualization requirement.
"""

from __future__ import annotations

from pathlib import Path

from pyvis.network import Network

from impact_tracer.models.impact import RiskLevel
from impact_tracer.models.report import ImpactReport


def generate_interactive_graph(report: ImpactReport, output_path: str = "graph.html") -> str:
	"""Generate interactive graph HTML from impact report data.

	Args:
		report: Structured impact report.
		output_path: Destination HTML file path.

	Returns:
		str: Generated HTML path.
	"""
	net = Network(
		height="800px",
		width="100%",
		directed=True,
		bgcolor="#111827",
		font_color="white",
		cdn_resources="in_line",
	)
	net.force_atlas_2based()

	changed_ids = {item.symbol_id for item in report.changed_symbols}
	affected_by_id = {item.symbol.id: item for item in report.affected_symbols}

	node_ids: set[str] = set()
	edge_pairs: set[tuple[str, str]] = set()

	for path_item in report.propagation_paths:
		for node_id in path_item.path:
			node_ids.add(node_id)
		for idx in range(len(path_item.path) - 1):
			edge_pairs.add((path_item.path[idx], path_item.path[idx + 1]))

	for changed_id in changed_ids:
		node_ids.add(changed_id)

	for node_id in sorted(node_ids):
		color = _node_color(node_id, changed_ids, affected_by_id)
		title = _node_title(node_id, changed_ids, affected_by_id)
		size = 30 if node_id in changed_ids else 18
		net.add_node(node_id, label=_short_label(node_id), color=color, title=title, size=size)

	for source, target in sorted(edge_pairs):
		net.add_edge(source, target, color="#9CA3AF", width=2)

	output = Path(output_path)
	output.parent.mkdir(parents=True, exist_ok=True)
	html_content = net.generate_html(notebook=False)
	output.write_text(html_content, encoding="utf-8")
	return str(output)


def _node_color(node_id: str, changed_ids: set[str], affected_by_id: dict[str, object]) -> str:
	if node_id in changed_ids:
		return "#F97316"  # orange
	affected = affected_by_id.get(node_id)
	if affected is None:
		return "#3B82F6"  # blue
	if affected.risk_level == RiskLevel.CRITICAL:
		return "#EF4444"  # red
	if affected.risk_level == RiskLevel.HIGH:
		return "#F59E0B"  # amber
	if affected.risk_level == RiskLevel.MEDIUM:
		return "#EAB308"  # yellow
	return "#22C55E"  # green


def _node_title(node_id: str, changed_ids: set[str], affected_by_id: dict[str, object]) -> str:
	if node_id in changed_ids:
		return f"Changed symbol: {node_id}"
	affected = affected_by_id.get(node_id)
	if affected is None:
		return f"Observed symbol: {node_id}"
	return (
		f"Affected symbol: {node_id}<br>"
		f"Risk: {affected.risk_level.value} ({affected.risk_score:.2f})<br>"
		f"Depth: {affected.propagation_depth}"
	)


def _short_label(node_id: str) -> str:
	parts = node_id.split(".")
	if len(parts) <= 2:
		return node_id
	return ".".join(parts[-2:])
