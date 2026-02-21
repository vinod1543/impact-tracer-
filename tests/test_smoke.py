"""Smoke tests for baseline scaffold."""

from impact_tracer.core.orchestrator import analyze, build_graph
from impact_tracer.models.graph import DependencyGraph


def test_build_graph_stub() -> None:
    """Ensure build_graph returns a dependency graph model."""
    result = build_graph("demo/payments_service")
    assert isinstance(result, DependencyGraph)
    assert len(result.nodes) > 0
    assert len(result.edges) > 0


def test_analyze_stub() -> None:
    """Ensure analyze returns a basic stub response."""
    result = analyze("@@ -1,1 +1,1 @@", "demo/payments_service")
    assert result["status"] == "stub"
