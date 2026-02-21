"""Smoke tests for baseline scaffold."""

from impact_tracer.core.orchestrator import analyze, build_graph


def test_build_graph_stub() -> None:
    """Ensure build_graph returns a basic stub response."""
    result = build_graph("demo/payments_service")
    assert result["status"] == "stub"


def test_analyze_stub() -> None:
    """Ensure analyze returns a basic stub response."""
    result = analyze("@@ -1,1 +1,1 @@", "demo/payments_service")
    assert result["status"] == "stub"
