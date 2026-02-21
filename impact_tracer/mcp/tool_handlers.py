"""MCP tool handlers wired to orchestrator and graph query helpers."""

from __future__ import annotations

from impact_tracer.core.orchestrator import analyze, build_graph
from impact_tracer.models.report import ImpactReport

_REPORT_STORE: dict[str, ImpactReport] = {}


def analyze_change(diff_text: str, project_path: str) -> dict[str, object]:
	"""Analyze code change and store report.

	Args:
		diff_text: Unified diff text.
		project_path: Project root path.

	Returns:
		dict[str, object]: Report metadata and report id.
	"""
	report = analyze(diff_text, project_path)
	report_id = f"rep-{len(_REPORT_STORE) + 1}"
	_REPORT_STORE[report_id] = report
	return {
		"report_id": report_id,
		"overall_risk": report.overall_risk.level.value,
		"risk_score": report.overall_risk.value,
		"changed_symbols": len(report.changed_symbols),
		"affected_symbols": len(report.affected_symbols),
	}


def get_impact_report(report_id: str) -> dict[str, object]:
	"""Fetch stored impact report by id.

	Args:
		report_id: Report identifier.

	Returns:
		dict[str, object]: Full report payload.
	"""
	report = _REPORT_STORE.get(report_id)
	if report is None:
		return {"error": f"Report id not found: {report_id}"}
	return report.model_dump()


def query_dependency_graph(project_path: str, symbol_id: str | None = None) -> dict[str, object]:
	"""Query dependency graph summary or neighbors for a symbol.

	Args:
		project_path: Project root path.
		symbol_id: Optional symbol id.

	Returns:
		dict[str, object]: Graph summary/query payload.
	"""
	graph = build_graph(project_path)
	if symbol_id is None:
		return {
			"node_count": len(graph.nodes),
			"edge_count": len(graph.edges),
		}

	outgoing = [edge.target for edge in graph.edges if edge.source == symbol_id]
	incoming = [edge.source for edge in graph.edges if edge.target == symbol_id]
	return {
		"symbol_id": symbol_id,
		"incoming": incoming,
		"outgoing": outgoing,
	}


def get_risk_score(diff_text: str, project_path: str, symbol_id: str) -> dict[str, object]:
	"""Get risk score for one symbol from a fresh analysis.

	Args:
		diff_text: Unified diff text.
		project_path: Project path.
		symbol_id: Symbol id to check.

	Returns:
		dict[str, object]: Risk score for symbol or fallback response.
	"""
	report = analyze(diff_text, project_path)
	for item in report.affected_symbols:
		if item.symbol.id == symbol_id:
			return {
				"symbol_id": symbol_id,
				"risk_score": item.risk_score,
				"risk_level": item.risk_level.value,
				"depth": item.propagation_depth,
			}
	return {"symbol_id": symbol_id, "risk_score": 0.0, "risk_level": "LOW", "depth": 0}
