"""LLM-powered diff generator from natural language change descriptions.

Layer: Engines (Layer 3)
Responsibility: Convert a natural language change description into a unified diff
by reading actual project source files and asking the LLM to produce the diff.
"""

from __future__ import annotations

import asyncio
from pathlib import Path

from impact_tracer.config.settings import Settings
from impact_tracer.core.llm.client import LLMClient


DIFF_GEN_SYSTEM_PROMPT = (
    "You are a senior Python developer. The user will describe a code change they want to make "
    "to a Python project. You will be given the actual source files of the project. "
    "Generate a valid unified diff (the kind produced by `git diff` or `diff -u`) that implements "
    "the described change. Output ONLY the raw unified diff text, nothing else — no markdown fences, "
    "no explanation, no commentary. The diff must use correct --- a/ and +++ b/ headers."
)


class DiffGenerator:
    """Generate unified diffs from natural language descriptions using LLM."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or Settings()

    def generate(self, description: str, project_path: str) -> str | None:
        """Generate a unified diff from a natural language change description.

        Args:
            description: Natural language description of the desired change.
            project_path: Path to the project directory.

        Returns:
            str | None: Generated unified diff text, or None on failure.
        """
        if not self.settings.openai_api_key:
            return None

        source_context = self._read_project_sources(project_path)
        if not source_context:
            return None

        prompt = self._build_prompt(description, source_context)

        models = self._candidate_models()
        for model in models:
            try:
                client = LLMClient(api_key=self.settings.openai_api_key, model=model)
                raw = asyncio.run(client.call_openai(prompt))
                diff_text = self._clean_diff_output(raw)
                if self._looks_like_valid_diff(diff_text):
                    return diff_text
            except Exception:
                continue
        return None

    def _read_project_sources(self, project_path: str, max_files: int = 20) -> str:
        """Read Python source files from the project for LLM context."""
        root = Path(project_path)
        if not root.exists():
            return ""

        parts: list[str] = []
        py_files = sorted(root.rglob("*.py"))[:max_files]
        for py_file in py_files:
            try:
                content = py_file.read_text(encoding="utf-8")
                rel_path = py_file.relative_to(root)
                parts.append(f"=== {rel_path} ===\n{content}")
            except Exception:
                continue
        return "\n\n".join(parts)

    def _build_prompt(self, description: str, source_context: str) -> str:
        return "\n".join([
            f"[SYSTEM]\n{DIFF_GEN_SYSTEM_PROMPT}",
            "",
            "[USER]",
            "PROJECT SOURCE FILES:",
            source_context,
            "",
            f"DESIRED CHANGE: {description}",
            "",
            "Generate the unified diff that implements this change. Output ONLY the raw diff.",
        ])

    def _clean_diff_output(self, raw: str) -> str:
        """Strip markdown fences or extra whitespace from LLM output."""
        text = raw.strip()
        if text.startswith("```"):
            lines = text.split("\n")
            # Remove first line (```diff or ```) and last line (```)
            if lines[-1].strip() == "```":
                lines = lines[1:-1]
            else:
                lines = lines[1:]
            text = "\n".join(lines)
        return text.strip()

    def _looks_like_valid_diff(self, text: str) -> bool:
        """Basic check that the text looks like a unified diff."""
        return "---" in text and "+++" in text and ("@@" in text or "---" in text)

    def _candidate_models(self) -> list[str]:
        configured = (self.settings.openai_model or "").strip()
        fallbacks = ["gpt-4o-mini", "gpt-4o"]
        ordered: list[str] = []
        for m in [configured, *fallbacks]:
            if m and m not in ordered:
                ordered.append(m)
        return ordered
