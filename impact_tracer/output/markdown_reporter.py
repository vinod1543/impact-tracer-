"""Markdown report renderer.

Layer: Interfaces/Output (Layer 5)
Responsibility: Produce a clear, detailed markdown report for impact analysis.
Implements: Phase 4 markdown reporting requirement while keeping JSON support.
"""

from __future__ import annotations

from pathlib import Path

from impact_tracer.models.report import ImpactReport


def render_markdown_report(report: ImpactReport, interactive_graph_path: str | None = None) -> str:
	"""Render a markdown impact report using simple, detailed language.

	Args:
		report: Structured impact report.
		interactive_graph_path: Optional path to interactive graph HTML.

	Returns:
		str: Markdown report content.
	"""
	changed_lines = []
	for item in report.changed_symbols:
		changed_lines.append(f"- `{item.symbol_id}` ({item.change_type.value})")

	affected_lines = []
	sorted_affected = sorted(report.affected_symbols, key=lambda node: node.risk_score, reverse=True)
	for item in sorted_affected:
		affected_lines.append(
			f"- **{item.risk_level.value}** `{item.symbol.id}` — score `{item.risk_score:.2f}`, depth `{item.propagation_depth}`"
		)

	mermaid_lines = _build_mermaid_lines(report)

	graph_section = "No interactive graph file generated in this run."
	if interactive_graph_path:
		graph_section = (
			f"Interactive graph: [{interactive_graph_path}]({interactive_graph_path})\n\n"
			"The Mermaid diagram below is a quick visual summary. Use the interactive graph link for zoom, pan, and node details."
		)

	explanation_section = "No LLM explanation available for this run."
	if report.explanation is not None:
		def _render_list(items: list[str]) -> str:
			return "\n".join([f"- {item}" for item in items]) if items else "- (none)"

		top_risks = "\n".join(
			[f"- `{risk['symbol']}`: {risk['reason']}" for risk in report.explanation.top_risks]
		)
		actions = "\n".join([f"- {action}" for action in report.explanation.recommended_actions])
		explanation_section = (
			f"**Summary**\n\n{report.explanation.summary}\n\n"
			f"**Blast Radius**\n\n{report.explanation.blast_radius}\n\n"
			f"**Impacted APIs**\n{_render_list(report.explanation.impacted_apis)}\n\n"
			f"**Impacted Modules/Functions**\n{_render_list(report.explanation.impacted_modules_or_functions)}\n\n"
			f"**Downstream Dependencies**\n{_render_list(report.explanation.downstream_dependencies)}\n\n"
			f"**Known Impact Zones**\n{_render_list(report.explanation.known_impact_zones)}\n\n"
			f"**Unknown Impact Zones**\n{_render_list(report.explanation.unknown_impact_zones)}\n\n"
			f"**High-Risk/Uncertain Areas**\n{_render_list(report.explanation.high_risk_or_uncertain_areas)}\n\n"
			f"**Top Risks**\n{top_risks}\n\n"
			f"**Recommended Actions**\n{actions}"
		)

	markdown = (
		"# Impact Tracer Report\n\n"
		"## 1) Quick Result\n\n"
		f"- Overall risk: **{report.overall_risk.level.value}** (`{report.overall_risk.value:.2f}`)\n"
		f"- Confidence: **{report.confidence.value}**\n"
		f"- Files changed: `{report.diff_summary.files_changed}`\n"
		f"- Changed symbols: `{report.diff_summary.changed_symbols}`\n"
		f"- Affected symbols: `{len(report.affected_symbols)}`\n\n"
		"## 2) What Changed\n\n"
		f"{'\n'.join(changed_lines) if changed_lines else '- No mapped changed symbols found.'}\n\n"
		"## 3) What Might Break (Ranked)\n\n"
		f"{'\n'.join(affected_lines) if affected_lines else '- No affected symbols detected.'}\n\n"
		"## 4) Visual Graph\n\n"
		f"{graph_section}\n\n"
		"```mermaid\n"
		f"{mermaid_lines}\n"
		"```\n\n"
		"## 5) Plain-English Explanation\n\n"
		f"{explanation_section}\n"
	)
	return markdown


def write_markdown_report(report: ImpactReport, output_path: str, interactive_graph_path: str | None = None) -> str:
	"""Write markdown report to file.

	Args:
		report: Structured impact report.
		output_path: Markdown file output path.
		interactive_graph_path: Optional graph HTML path.

	Returns:
		str: Output markdown file path.
	"""
	content = render_markdown_report(report, interactive_graph_path=interactive_graph_path)
	output = Path(output_path)
	output.parent.mkdir(parents=True, exist_ok=True)
	output.write_text(content, encoding="utf-8")
	return str(output)


def _build_mermaid_lines(report: ImpactReport) -> str:
	edges: list[tuple[str, str]] = []
	for path in report.propagation_paths[:40]:
		if len(path.path) < 2:
			continue
		for idx in range(len(path.path) - 1):
			source = path.path[idx]
			target = path.path[idx + 1]
			edges.append((source, target))

	unique_edges = list(dict.fromkeys(edges))
	if not unique_edges:
		return "graph LR\n  A[No propagation path data]"

	lines = ["graph LR"]
	for source, target in unique_edges:
		lines.append(f"  {sanitize_id(source)}[{trim_label(source)}] --> {sanitize_id(target)}[{trim_label(target)}]")
	return "\n".join(lines)


def sanitize_id(value: str) -> str:
	"""Create Mermaid-safe node id from symbol id.

	Args:
		value: Raw symbol id.

	Returns:
		str: Mermaid-safe id.
	"""
	return value.replace(".", "_").replace(":", "_").replace("-", "_")


def trim_label(value: str, max_len: int = 40) -> str:
	"""Trim labels for cleaner Mermaid display.

	Args:
		value: Label text.
		max_len: Maximum length.

	Returns:
		str: Trimmed label.
	"""
	if len(value) <= max_len:
		return value
	return f"...{value[-(max_len-3):]}"
