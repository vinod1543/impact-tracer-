"""LLM prompt builder.

Layer: Engines (Layer 3)
Responsibility: Build grounded prompt from structured report data only.
Implements: Phase 3 Task 3.2.
"""

from __future__ import annotations

from impact_tracer.models.report import ImpactReport

SYSTEM_PROMPT = (
	"You are a senior software architect analyzing Python code change impact. "
	"Only reference symbols that exist in the provided context. "
	"Return valid JSON only."
)


def build_prompt(report: ImpactReport) -> str:
	"""Build a structured LLM prompt from report metadata.

	Args:
		report: Structured impact report.

	Returns:
		str: Prompt containing only symbol/risk/path context.
	"""
	changed_lines = []
	for item in report.changed_symbols[:20]:
		changed_lines.append(f"- {item.symbol_id} ({item.change_type.value})")

	top_affected = sorted(report.affected_symbols, key=lambda node: node.risk_score, reverse=True)[:10]
	affected_lines = []
	for item in top_affected:
		affected_lines.append(
			f"- {item.symbol.id} | risk={item.risk_score:.2f} | depth={item.propagation_depth} "
			f"| path={' -> '.join(item.propagation_path)}"
		)

	prompt = "\n".join(
		[
			f"[SYSTEM]\n{SYSTEM_PROMPT}",
			"[USER]",
			"CHANGED SYMBOLS:",
			*changed_lines,
			"",
			"TOP AFFECTED SYMBOLS:",
			*affected_lines,
			"",
			f"OVERALL_RISK: {report.overall_risk.level.value} ({report.overall_risk.value:.2f})",
			f"CONFIDENCE: {report.confidence.value}",
			"",
			"Return JSON with exact keys:",
			"{",
			'  "summary": "<2 sentence summary>",',
			'  "blast_radius": "<2-3 sentence blast radius>",',
			'  "top_risks": [{"symbol": "<id>", "reason": "<one line>"}],',
			'  "recommended_actions": ["<action1>", "<action2>", "<action3>"]',
			"}",
		]
	)
	return prompt
