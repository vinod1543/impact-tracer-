"""Unit tests for risk scoring engine.

Phase 2 Task 2.10: core scoring logic, edge thresholds, and confidence mapping.
"""

from __future__ import annotations

import networkx as nx

from impact_tracer.core.risk.config import RiskWeights
from impact_tracer.core.risk.scorer import compute_confidence, risk_level, score_affected_symbols, score_symbol
from impact_tracer.models.diff import ChangeType
from impact_tracer.models.impact import AffectedSymbol, ConfidenceLevel, RiskLevel, ScoringInput
from impact_tracer.models.symbol import Symbol, SymbolType


def _symbol(symbol_id: str, symbol_type: SymbolType = SymbolType.FUNCTION, is_public: bool = True) -> Symbol:
    return Symbol(
        id=symbol_id,
        name=symbol_id.split(".")[-1],
        type=symbol_type,
        module=symbol_id.split(".")[0],
        file_path=f"{symbol_id.split('.')[0]}.py",
        line_start=1,
        line_end=10,
        is_public=is_public,
    )


def test_score_symbol_docstring_change_is_low() -> None:
    """Docstring-only changes should stay in low-risk range."""
    weights = RiskWeights()
    score_input = ScoringInput(
        fan_in=1,
        depth=1,
        change_type=ChangeType.DOCSTRING_CHANGE,
        is_public=False,
        has_tests=True,
    )
    score_value = score_symbol(SymbolType.FUNCTION, score_input, weights)
    assert score_value < 0.3
    assert risk_level(score_value) == RiskLevel.LOW


def test_score_symbol_signature_high_fanin_is_critical() -> None:
    """Signature changes with high fan-in should elevate to critical risk."""
    weights = RiskWeights()
    score_input = ScoringInput(
        fan_in=120,
        depth=0,
        change_type=ChangeType.SIGNATURE_CHANGE,
        is_public=True,
        has_tests=False,
    )
    score_value = score_symbol(SymbolType.FUNCTION, score_input, weights)
    assert score_value >= 0.8
    assert risk_level(score_value) == RiskLevel.CRITICAL


def test_score_affected_symbols_applies_scores() -> None:
    """Scorer assigns non-zero values and risk levels to affected symbols."""
    graph = nx.DiGraph()
    graph.add_edge("caller.func", "target.func")

    affected = [
        AffectedSymbol(
            symbol=_symbol("caller.func"),
            propagation_depth=1,
            propagation_path=["target.func", "caller.func"],
        )
    ]
    changed_type_map = {"target.func": ChangeType.SIGNATURE_CHANGE}
    scored = score_affected_symbols(graph, affected, changed_type_map, RiskWeights())
    assert scored[0].risk_score > 0.0
    assert isinstance(scored[0].risk_level, RiskLevel)


def test_compute_confidence_buckets() -> None:
    """Confidence buckets map correctly to weighted quality rates."""
    assert compute_confidence(0.9, 0.9, 0.9) == ConfidenceLevel.HIGH
    assert compute_confidence(0.6, 0.6, 0.6) == ConfidenceLevel.MEDIUM
    assert compute_confidence(0.2, 0.2, 0.2) == ConfidenceLevel.LOW
