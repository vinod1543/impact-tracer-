"""Phase 2 integration checks for orchestrator analyze pipeline."""

from __future__ import annotations

from pathlib import Path

from impact_tracer.core.orchestrator import analyze
from impact_tracer.models.impact import RiskLevel
from impact_tracer.models.report import ImpactReport


def test_analyze_returns_impact_report_for_demo_signature_change() -> None:
    """Analyze returns structured report with changed/affected symbols for demo diff."""
    diff_text = Path("demo/signature_change.diff").read_text(encoding="utf-8")
    report = analyze(diff_text, "demo/payments_service")

    assert isinstance(report, ImpactReport)
    assert report.diff_summary.files_changed >= 1
    assert len(report.changed_symbols) >= 1
    assert report.overall_risk.level in {RiskLevel.CRITICAL, RiskLevel.HIGH, RiskLevel.MEDIUM, RiskLevel.LOW}


def test_analyze_handles_invalid_diff_input_gracefully() -> None:
    """Analyze handles invalid/non-unified diff text without crashing."""
    report = analyze("not-a-unified-diff", "demo/payments_service")
    assert isinstance(report, ImpactReport)
    assert report.diff_summary.files_changed == 0
