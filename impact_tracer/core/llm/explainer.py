"""LLM explanation orchestrator.

Layer: Engines (Layer 3)
Responsibility: Build prompt, call LLM, validate JSON explanation, and gracefully degrade.
Implements: Phase 3 Tasks 3.4, 3.5, 3.6, 3.7.
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

from impact_tracer.config.settings import Settings
from impact_tracer.core.llm.client import LLMClient
from impact_tracer.core.llm.prompt_builder import build_prompt
from impact_tracer.models.report import ImpactReport, LLMExplanation


class LLMExplainer:
	"""High-level explanation orchestrator with fallback behavior."""

	def __init__(self, settings: Settings | None = None, cache_path: str = "demo/demo_cache/explanation_demo.json") -> None:
		"""Initialize LLM explainer.

		Args:
			settings: Optional settings instance.
			cache_path: Cached explanation path used in demo mode.
		"""
		self.settings = settings or Settings()
		self.cache_path = cache_path

	def explain(self, report: ImpactReport) -> LLMExplanation | None:
		"""Generate explanation from impact report.

		Args:
			report: Structured impact report.

		Returns:
			LLMExplanation | None: Parsed explanation or None on failure/unavailable backend.
		"""
		if self.settings.demo_mode == 1:
			return self._load_from_cache()

		if not self.settings.openai_api_key:
			return None

		prompt = build_prompt(report)
		try:
			client = LLMClient(api_key=self.settings.openai_api_key)
			raw_text = asyncio.run(client.call_openai(prompt))
			return LLMExplanation.model_validate_json(raw_text)
		except Exception:
			return None

	def _load_from_cache(self) -> LLMExplanation | None:
		path = Path(self.cache_path)
		if not path.exists():
			return None
		try:
			payload = json.loads(path.read_text(encoding="utf-8"))
			return LLMExplanation.model_validate(payload)
		except Exception:
			return None
