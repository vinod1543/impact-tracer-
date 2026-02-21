"""LLM API client.

Layer: Engines (Layer 3)
Responsibility: Call LLM backend for explanation generation.
Implements: Phase 3 Task 3.3.
"""

from __future__ import annotations

from openai import AsyncOpenAI


class LLMClient:
	"""OpenAI-backed async LLM client."""

	def __init__(self, api_key: str, model: str = "gpt-4o", timeout_seconds: float = 30.0) -> None:
		"""Initialize client.

		Args:
			api_key: OpenAI API key.
			model: Model identifier.
			timeout_seconds: Request timeout.
		"""
		self.model = model
		self.client = AsyncOpenAI(api_key=api_key, timeout=timeout_seconds)

	async def call_openai(self, prompt: str) -> str:
		"""Send prompt to OpenAI and return raw text response.

		Args:
			prompt: Prompt text.

		Returns:
			str: Model output text.
		"""
		response = await self.client.responses.create(
			model=self.model,
			input=prompt,
			temperature=0.2,
		)
		return response.output_text
