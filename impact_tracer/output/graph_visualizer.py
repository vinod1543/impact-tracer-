"""Interactive graph visualizer.

Layer: Interfaces/Output (Layer 5)
Responsibility: Export dynamic interactive graph HTML for impact report exploration.
Implements: Phase 4 graph visualization requirement.
"""

from __future__ import annotations

from collections import Counter
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
	net.force_atlas_2based(gravity=-40, central_gravity=0.01, spring_length=160, spring_strength=0.05)
	net.set_options(
		"""
		const options = {
		  "interaction": {"hover": true, "navigationButtons": true, "keyboard": true},
		  "physics": {
		    "enabled": true,
		    "stabilization": {"enabled": true, "iterations": 500}
		  },
		  "edges": {
		    "smooth": {"type": "dynamic"},
		    "arrows": {"to": {"enabled": true, "scaleFactor": 0.6}}
		  }
		}
		"""
	)

	changed_ids = {item.symbol_id for item in report.changed_symbols}
	affected_by_id = {item.symbol.id: item for item in report.affected_symbols}

	node_ids: set[str] = set()
	edge_counter: Counter[tuple[str, str]] = Counter()

	for path_item in report.propagation_paths:
		for node_id in path_item.path:
			node_ids.add(node_id)
		for idx in range(len(path_item.path) - 1):
			edge_counter[(path_item.path[idx], path_item.path[idx + 1])] += 1

	for changed_id in changed_ids:
		node_ids.add(changed_id)

	for affected_id in affected_by_id:
		node_ids.add(affected_id)

	module_ids: set[str] = set()
	for node_id in list(node_ids):
		if ":" in node_id:
			continue
		parts = node_id.split(".")
		if len(parts) < 2:
			continue
		module_id = f"module:{parts[0]}"
		module_ids.add(module_id)
		edge_counter[(module_id, node_id)] += 1

	node_ids.update(module_ids)

	for node_id in sorted(node_ids):
		if node_id.startswith("module:"):
			label = node_id.removeprefix("module:")
			net.add_node(
				node_id,
				label=label,
				color="#8B5CF6",
				title=f"Module: {label}",
				size=20,
				shape="box",
			)
			continue

		color = _node_color(node_id, changed_ids, affected_by_id)
		title = _node_title(node_id, changed_ids, affected_by_id)
		size = _node_size(node_id, changed_ids, affected_by_id)
		net.add_node(node_id, label=_short_label(node_id), color=color, title=title, size=size)

	for (source, target), freq in sorted(edge_counter.items()):
		module_edge = source.startswith("module:")
		edge_color = "#6B7280" if module_edge else "#9CA3AF"
		width = 1 if module_edge else min(6, 1 + freq)
		title = "Module contains symbol" if module_edge else f"Propagation frequency: {freq}"
		net.add_edge(source, target, color=edge_color, width=width, title=title, dashes=module_edge)

	output = Path(output_path)
	output.parent.mkdir(parents=True, exist_ok=True)
	html_content = net.generate_html(notebook=False)
	html_content = _inject_legend(html_content)
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


def _node_size(node_id: str, changed_ids: set[str], affected_by_id: dict[str, object]) -> int:
	if node_id in changed_ids:
		return 34
	affected = affected_by_id.get(node_id)
	if affected is None:
		return 16
	if affected.risk_level == RiskLevel.CRITICAL:
		return 30
	if affected.risk_level == RiskLevel.HIGH:
		return 26
	if affected.risk_level == RiskLevel.MEDIUM:
		return 22
	return 18


def _short_label(node_id: str) -> str:
	parts = node_id.split(".")
	if len(parts) <= 2:
		return node_id
	return ".".join(parts[-2:])


def _inject_legend(html_content: str) -> str:
	legend = """
<div style="
	position: fixed;
	top: 12px;
	right: 12px;
	z-index: 9999;
	background: rgba(17,24,39,0.9);
	color: #fff;
	border: 1px solid #374151;
	border-radius: 8px;
	padding: 10px 12px;
	font-family: Arial, sans-serif;
	font-size: 12px;
	line-height: 1.4;
">
	<div style="font-weight: 700; margin-bottom: 6px;">Legend</div>
	<div>🟠 Changed symbol</div>
	<div>🔴/🟡/🟢 Affected risk (critical/high/low)</div>
	<div>🟣 Module</div>
	<div>Solid edge: propagation</div>
	<div>Dashed edge: module contains symbol</div>
</div>
"""
	if "</body>" in html_content:
		return html_content.replace("</body>", f"{legend}\n</body>")
	return html_content + legend
