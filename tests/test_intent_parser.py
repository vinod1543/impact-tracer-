"""Tests for natural language intent parsing patterns."""

from impact_tracer.cli.intent_parser import parse_intent


def test_intent_parser_detects_show_graph() -> None:
    result = parse_intent("show me the graph for payments")
    assert result["operation"] == "show_graph"


def test_intent_parser_detects_risk_score_query() -> None:
    result = parse_intent("what is risk score for payments.validator.validate")
    assert result["operation"] == "get_risk_score"
    assert result["symbol"] == "payments.validator.validate"


def test_intent_parser_detects_expand_command() -> None:
    result = parse_intent("show all")
    assert result["operation"] == "expand_last_report"


def test_intent_parser_falls_back_to_analyze() -> None:
    result = parse_intent("what breaks if I change validate")
    assert result["operation"] == "analyze_diff"
