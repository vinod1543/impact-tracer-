"""LLM explanation orchestrator.

Layer: Engines (Layer 3)
Responsibility: Build prompt, call LLM, validate JSON explanation, and gracefully degrade.
Implements: Phase 3 Tasks 3.4, 3.5, 3.6, 3.7.
"""

from __future__ import annotations

import asyncio
import json
import re
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
		models = self._candidate_models()
		for model in models:
			try:
				client = LLMClient(api_key=self.settings.openai_api_key, model=model)
				raw_text = asyncio.run(client.call_openai(prompt))
				parsed = self._parse_llm_json(raw_text)
				if parsed is not None:
					return parsed
			except Exception:
				continue
		return None

	def _parse_llm_json(self, raw_text: str) -> LLMExplanation | None:
		"""Parse LLM JSON safely, including fenced JSON outputs.

		Args:
			raw_text: Raw model output.

		Returns:
			LLMExplanation | None: Parsed explanation if valid.
		"""
		try:
			return LLMExplanation.model_validate_json(raw_text)
		except Exception:
			pass

		match = re.search(r"```(?:json)?\s*(\{.*\})\s*```", raw_text, re.DOTALL)
		if match:
			candidate = match.group(1)
			try:
				return LLMExplanation.model_validate_json(candidate)
			except Exception:
				pass

		first = raw_text.find("{")
		last = raw_text.rfind("}")
		if first != -1 and last != -1 and last > first:
			candidate = raw_text[first:last + 1]
			try:
				payload = json.loads(candidate)
				return LLMExplanation.model_validate(payload)
			except Exception:
				return None

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

	def _candidate_models(self) -> list[str]:
		configured_model = (self.settings.openai_model or "").strip()
		fallback_models = ["gpt-4o-mini", "gpt-4o"]
		models = [configured_model, *fallback_models]
		ordered_unique: list[str] = []
		for model in models:
			if not model:
				continue
			if model not in ordered_unique:
				ordered_unique.append(model)
		return ordered_unique
