"""Risk scoring engine.

Layer: Engines (Layer 3)
Responsibility: Score affected symbols and compute aggregate risk/confidence.
Implements: Phase 2 Task 2.6 and 2.8.
"""

from __future__ import annotations

import networkx as nx

from impact_tracer.core.risk.config import RiskWeights
from impact_tracer.models.diff import ChangeType
from impact_tracer.models.impact import AffectedSymbol, ConfidenceLevel, RiskLevel, RiskScore, ScoringInput
from impact_tracer.models.symbol import SymbolType

MAX_FAN_IN = 50

CHANGE_TYPE_SCORES = {
	ChangeType.SIGNATURE_CHANGE: 1.0,
	ChangeType.DELETION: 1.0,
	ChangeType.BODY_CHANGE: 0.6,
	ChangeType.MODIFICATION: 0.6,
	ChangeType.ADDITION: 0.5,
	ChangeType.DOCSTRING_CHANGE: 0.05,
	ChangeType.RENAME: 0.7,
}

SYMBOL_TYPE_SCORES = {
	SymbolType.MODULE: 0.7,
	SymbolType.CLASS: 0.7,
	SymbolType.METHOD: 0.4,
	SymbolType.FUNCTION: 0.4,
	SymbolType.API_ENDPOINT: 0.8,
}


def score_affected_symbols(
	graph: nx.DiGraph,
	affected_symbols: list[AffectedSymbol],
	changed_type_map: dict[str, ChangeType],
	weights: RiskWeights,
) -> list[AffectedSymbol]:
	"""Score each affected symbol in-place.

	Args:
		graph: Dependency graph.
		affected_symbols: Symbols impacted by propagation.
		changed_type_map: Mapping for root changed symbols.
		weights: Risk weights configuration.

	Returns:
		list[AffectedSymbol]: Scored affected symbols.
	"""
	for affected in affected_symbols:
		implied_change_type = _infer_change_type(changed_type_map)
		has_tests = _estimate_has_tests(affected.symbol.file_path)
		fan_in = graph.in_degree(affected.symbol.id) if affected.symbol.id in graph else 0

		score_input = ScoringInput(
			fan_in=fan_in,
			depth=affected.propagation_depth,
			change_type=implied_change_type,
			is_public=affected.symbol.is_public,
			has_tests=has_tests,
		)
		score_value = score_symbol(affected.symbol.type, score_input, weights)
		affected.risk_score = score_value
		affected.risk_level = risk_level(score_value)

	return affected_symbols


def score_symbol(symbol_type: SymbolType, score_input: ScoringInput, weights: RiskWeights) -> float:
	"""Compute risk score using weighted 5-factor formula.

	Args:
		symbol_type: Target symbol type.
		score_input: Input scoring factors.
		weights: Risk weights.

	Returns:
		float: Risk score in [0.0, 1.0].
	"""
	fan_in_factor = min(score_input.fan_in / MAX_FAN_IN, 1.0)
	depth_factor = 1.0 / (score_input.depth + 1)
	change_factor = CHANGE_TYPE_SCORES.get(score_input.change_type, 0.5)
	symbol_factor = 1.0 if score_input.is_public else SYMBOL_TYPE_SCORES.get(symbol_type, 0.4)
	test_factor = 0.3 if score_input.has_tests else 1.0

	raw_score = (
		weights.fan_in * fan_in_factor
		+ weights.depth * depth_factor
		+ weights.change_type * change_factor
		+ weights.symbol_type * symbol_factor
		+ weights.test_coverage * test_factor
	)
	return min(round(raw_score, 4), 1.0)


def aggregate_overall_risk(
	affected_symbols: list[AffectedSymbol],
	import_resolution_rate: float,
	ast_parse_success_rate: float,
	call_resolution_rate: float,
) -> RiskScore:
	"""Aggregate overall risk and confidence.

	Args:
		affected_symbols: Scored affected symbols.
		import_resolution_rate: Import resolution success rate.
		ast_parse_success_rate: AST parse success rate.
		call_resolution_rate: Call resolution success rate.

	Returns:
		RiskScore: Aggregated risk object.
	"""
	if not affected_symbols:
		confidence = compute_confidence(import_resolution_rate, ast_parse_success_rate, call_resolution_rate)
		return RiskScore(value=0.0, level=RiskLevel.LOW, confidence=confidence, factors={})

	max_score = max(symbol.risk_score for symbol in affected_symbols)
	confidence = compute_confidence(import_resolution_rate, ast_parse_success_rate, call_resolution_rate)
	factors = {
		"max_affected_risk": max_score,
		"import_resolution_rate": import_resolution_rate,
		"ast_parse_success_rate": ast_parse_success_rate,
		"call_resolution_rate": call_resolution_rate,
	}
	return RiskScore(value=max_score, level=risk_level(max_score), confidence=confidence, factors=factors)


def compute_confidence(import_resolution_rate: float, ast_parse_success_rate: float, call_resolution_rate: float) -> ConfidenceLevel:
	"""Compute confidence level from parser/resolution quality metrics.

	Args:
		import_resolution_rate: Import resolution success rate.
		ast_parse_success_rate: AST parse success rate.
		call_resolution_rate: Call resolution success rate.

	Returns:
		ConfidenceLevel: Confidence bucket.
	"""
	weighted = (
		import_resolution_rate * 0.30
		+ ast_parse_success_rate * 0.40
		+ call_resolution_rate * 0.30
	)
	if weighted >= 0.8:
		return ConfidenceLevel.HIGH
	if weighted >= 0.5:
		return ConfidenceLevel.MEDIUM
	return ConfidenceLevel.LOW


def risk_level(score: float) -> RiskLevel:
	"""Map risk score to risk level bucket.

	Args:
		score: Risk score value.

	Returns:
		RiskLevel: Risk level bucket.
	"""
	if score >= 0.8:
		return RiskLevel.CRITICAL
	if score >= 0.6:
		return RiskLevel.HIGH
	if score >= 0.3:
		return RiskLevel.MEDIUM
	return RiskLevel.LOW


def _infer_change_type(changed_type_map: dict[str, ChangeType]) -> ChangeType:
	if not changed_type_map:
		return ChangeType.MODIFICATION
	# Conservative: take highest-severity type among changed roots.
	severity_order = [
		ChangeType.SIGNATURE_CHANGE,
		ChangeType.DELETION,
		ChangeType.BODY_CHANGE,
		ChangeType.MODIFICATION,
		ChangeType.ADDITION,
		ChangeType.DOCSTRING_CHANGE,
	]
	present = set(changed_type_map.values())
	for change_type in severity_order:
		if change_type in present:
			return change_type
	return ChangeType.MODIFICATION


def _estimate_has_tests(file_path: str) -> bool:
	return "test_" in file_path or "tests/" in file_path.replace("\\", "/")
