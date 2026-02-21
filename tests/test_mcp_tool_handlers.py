"""Tests for MCP tool handler wiring."""

from pathlib import Path

from impact_tracer.mcp.tool_handlers import analyze_change, get_impact_report, get_risk_score, query_dependency_graph


def test_analyze_change_and_get_impact_report_roundtrip() -> None:
    diff_text = Path("demo/signature_change.diff").read_text(encoding="utf-8")
    metadata = analyze_change(diff_text, "demo/payments_service")
    assert "report_id" in metadata
    payload = get_impact_report(metadata["report_id"])
    assert "overall_risk" in payload
    assert "changed_symbols" in payload


def test_query_dependency_graph_summary_and_symbol_lookup() -> None:
    summary = query_dependency_graph("demo/payments_service")
    assert summary["node_count"] >= 1
    assert summary["edge_count"] >= 0

    lookup = query_dependency_graph("demo/payments_service", "validator.BasePaymentValidator.validate")
    assert "incoming" in lookup
    assert "outgoing" in lookup


def test_get_risk_score_returns_symbol_payload() -> None:
    diff_text = Path("demo/signature_change.diff").read_text(encoding="utf-8")
    payload = get_risk_score(diff_text, "demo/payments_service", "api.process_payment")
    assert payload["symbol_id"] == "api.process_payment"
    assert "risk_score" in payload
