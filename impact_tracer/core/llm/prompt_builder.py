"""LLM prompt builder.

Layer: Engines (Layer 3)
Responsibility: Build grounded prompt from structured report data only.
Implements: Phase 3 Task 3.2.
"""

from __future__ import annotations

from impact_tracer.models.report import ImpactReport

SYSTEM_PROMPT = (
	"You are a senior software architect analyzing Python code change impact. "
	"Only reference symbols that exist in the provided context; never invent symbols, files, or services. "
	"Your response must be structured, explainable, and engineer-readable. "
	"Prioritize technical accuracy, completeness of direct+indirect impact, and minimal-but-correct graph reasoning. "
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

	impacted_apis = []
	impacted_modules = []
	for item in report.changed_symbols:
		symbol_id = item.symbol_id
		if ".api." in symbol_id or symbol_id.startswith("api."):
			if symbol_id not in impacted_apis:
				impacted_apis.append(symbol_id)
		module_name = symbol_id.split(".")[0] if "." in symbol_id else symbol_id
		if module_name not in impacted_modules:
			impacted_modules.append(module_name)

	top_affected = sorted(report.affected_symbols, key=lambda node: node.risk_score, reverse=True)[:10]
	affected_lines = []
	downstream_lines = []
	for item in top_affected:
		if item.symbol.id not in downstream_lines:
			downstream_lines.append(item.symbol.id)
		affected_lines.append(
			f"- {item.symbol.id} | risk={item.risk_score:.2f} | depth={item.propagation_depth} "
			f"| path={' -> '.join(item.propagation_path)}"
		)

	prompt = "\n".join(
		[
			f"[SYSTEM]\n{SYSTEM_PROMPT}",
			"[USER]",
			"TASK:",
			"Produce a clear blast-radius report from the structured impact data below.",
			"Include: impacted APIs, impacted modules/functions, downstream dependencies,",
			"high-risk/uncertain areas, and known vs unknown impact zones.",
			"",
			"CHANGED SYMBOLS:",
			*changed_lines,
			"",
			"IMPACTED APIS (observed from changed symbols):",
			*([f"- {item}" for item in impacted_apis[:10]] or ["- (none detected)"]),
			"",
			"IMPACTED MODULES (observed from changed symbols):",
			*([f"- {item}" for item in impacted_modules[:10]] or ["- (none detected)"]),
			"",
			"TOP AFFECTED SYMBOLS:",
			*affected_lines,
			"",
			"DOWNSTREAM DEPENDENCIES (top affected symbols):",
			*([f"- {item}" for item in downstream_lines] or ["- (none detected)"]),
			"",
			f"OVERALL_RISK: {report.overall_risk.level.value} ({report.overall_risk.value:.2f})",
			f"CONFIDENCE: {report.confidence.value}",
			"",
			"QUALITY CRITERIA:",
			"- Accuracy: impacted items must be technically plausible from the provided symbols/paths.",
			"- Completeness: include direct and indirect (downstream) impacts when evidence exists.",
			"- Explainability: each risk should include why it is impacted.",
			"- Graph Design: keep dependency reasoning minimal and avoid speculative chain inflation.",
			"",
			"RULES:",
			"- If an item is uncertain, put it under unknown_impact_zones or high_risk_or_uncertain_areas.",
			"- If evidence is missing, explicitly say unknown instead of guessing.",
			"- Keep summary concise (2-3 sentences) and action-oriented.",
			"",
			"Return JSON with EXACT keys:",
			"{",
			'  "summary": "<2-3 sentence summary>",',
			'  "blast_radius": "<2-4 sentence blast radius explanation>",',
			'  "impacted_apis": ["<api_or_handler_symbol>", "..."],',
			'  "impacted_modules_or_functions": ["<module.or.function>", "..."],',
			'  "downstream_dependencies": ["<dependent_symbol>", "..."],',
			'  "high_risk_or_uncertain_areas": ["<risk/uncertainty statement>", "..."],',
			'  "known_impact_zones": ["<confirmed zone>", "..."],',
			'  "unknown_impact_zones": ["<unknown zone or assumption>", "..."],',
			'  "top_risks": [{"symbol": "<id>", "reason": "<one-line why impacted>"}],',
			'  "recommended_actions": ["<specific action 1>", "<specific action 2>", "<specific action 3>"]',
			"}",
		]
	)
	return prompt
