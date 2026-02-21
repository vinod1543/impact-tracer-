"""Unit tests for LLM phase behavior.

Phase 3: prompt building, graceful degradation, and demo cache mode.
"""

from __future__ import annotations

import json
from pathlib import Path

from impact_tracer.config.settings import Settings
from impact_tracer.core.llm.explainer import LLMExplainer
from impact_tracer.core.llm.prompt_builder import build_prompt
from impact_tracer.core.orchestrator import analyze
from impact_tracer.models.report import ImpactReport


def test_prompt_builder_uses_structured_fields_only() -> None:
    """Prompt includes changed/affected symbols and excludes raw source snippets."""
    diff = """--- a/demo/payments_service/validator.py
+++ b/demo/payments_service/validator.py
@@ -6,1 +6,1 @@
-    def validate(self, payment_data: dict) -> bool:
+    def validate(self, payment_data: dict, strict: bool = False) -> bool:
"""
    report = analyze(diff, "demo/payments_service", enable_llm=False)
    prompt = build_prompt(report)

    assert "CHANGED SYMBOLS:" in prompt
    assert "TOP AFFECTED SYMBOLS:" in prompt
    assert "return \"amount\" in payment_data" not in prompt


def test_explainer_returns_none_without_api_key() -> None:
    """Explainer should degrade gracefully when no API key is configured."""
    settings = Settings(openai_api_key=None, demo_mode=0)
    explainer = LLMExplainer(settings=settings)

    diff = """--- a/demo/payments_service/validator.py
+++ b/demo/payments_service/validator.py
@@ -6,1 +6,1 @@
-    def validate(self, payment_data: dict) -> bool:
+    def validate(self, payment_data: dict, strict: bool = False) -> bool:
"""
    report = analyze(diff, "demo/payments_service", enable_llm=False)
    result = explainer.explain(report)

    assert result is None


def test_explainer_loads_demo_cache_when_demo_mode_enabled(tmp_path) -> None:
    """Explainer returns cached explanation in demo mode without network call."""
    cache_path = tmp_path / "cached_explanation.json"
    cache_payload = {
        "summary": "Demo summary",
        "blast_radius": "Demo blast radius",
        "top_risks": [{"symbol": "a.b", "reason": "demo"}],
        "recommended_actions": ["act1", "act2", "act3"],
    }
    cache_path.write_text(json.dumps(cache_payload), encoding="utf-8")

    settings = Settings(openai_api_key=None, demo_mode=1)
    explainer = LLMExplainer(settings=settings, cache_path=str(cache_path))

    diff = """--- a/demo/payments_service/validator.py
+++ b/demo/payments_service/validator.py
@@ -6,1 +6,1 @@
-    def validate(self, payment_data: dict) -> bool:
+    def validate(self, payment_data: dict, strict: bool = False) -> bool:
"""
    report = analyze(diff, "demo/payments_service", enable_llm=False)
    result = explainer.explain(report)

    assert result is not None
    assert result.summary == "Demo summary"


def test_orchestrator_analyze_can_skip_llm() -> None:
    """Analyze supports explicit LLM skip path for offline/test execution."""
    diff = Path("demo/signature_change.diff").read_text(encoding="utf-8")
    report = analyze(diff, "demo/payments_service", enable_llm=False)
    assert isinstance(report, ImpactReport)
    assert report.explanation is None
