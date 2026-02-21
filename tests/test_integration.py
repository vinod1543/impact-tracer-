"""Integration tests for end-to-end impact analysis pipeline."""

from __future__ import annotations

from pathlib import Path

from impact_tracer.core.orchestrator import analyze
from impact_tracer.models.report import ImpactReport


def test_integration_demo_signature_change_pipeline() -> None:
    """Full pipeline should return a valid ImpactReport for demo signature change."""
    diff_text = Path("demo/signature_change.diff").read_text(encoding="utf-8")
    report = analyze(diff_text, "demo/payments_service", enable_llm=False)

    assert isinstance(report, ImpactReport)
    assert report.diff_summary.files_changed >= 1
    assert report.diff_summary.changed_symbols >= 1
    assert report.metadata.total_files >= 1


def test_integration_demo_docstring_change_pipeline() -> None:
    """Docstring-only demo diff should produce a report without runtime errors."""
    diff_text = Path("demo/trivial.diff").read_text(encoding="utf-8")
    report = analyze(diff_text, "demo/payments_service", enable_llm=False)

    assert isinstance(report, ImpactReport)
    assert report.overall_risk.value <= 1.0
