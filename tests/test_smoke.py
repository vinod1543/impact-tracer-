"""Smoke tests for baseline scaffold."""

from impact_tracer.core.orchestrator import analyze, build_graph
from impact_tracer.models.graph import DependencyGraph
from impact_tracer.models.report import ImpactReport


def test_build_graph_stub() -> None:
    """Ensure build_graph returns a dependency graph model."""
    result = build_graph("demo/payments_service")
    assert isinstance(result, DependencyGraph)
    assert len(result.nodes) > 0
    assert len(result.edges) > 0


def test_analyze_stub() -> None:
    """Ensure analyze returns a structured impact report."""
    diff = """--- a/demo/payments_service/validator.py
+++ b/demo/payments_service/validator.py
@@ -6,1 +6,1 @@
-    def validate(self, payment_data: dict) -> bool:
+    def validate(self, payment_data: dict, strict: bool = False) -> bool:
"""
    result = analyze(diff, "demo/payments_service")
    assert isinstance(result, ImpactReport)
    assert result.diff_summary.files_changed >= 1
