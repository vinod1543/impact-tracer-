"""Layer 2 report models for final impact output.

Layer: Models (Layer 2)
Responsibility: Final report schema shared by CLI and downstream integrations.
Implements: PRD §11.2 ImpactReport and Phase 2 Task 2.9 output contract.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from impact_tracer.models.diff import ChangedSymbol, DiffResult
from impact_tracer.models.impact import AffectedSymbol, ConfidenceLevel, PropagationPath, RiskLevel, RiskScore


class LLMExplanation(BaseModel):
	"""LLM-generated explanation payload."""

	summary: str
	blast_radius: str
	top_risks: list[dict[str, str]] = Field(default_factory=list)
	recommended_actions: list[str] = Field(default_factory=list)


class AnalysisMetadata(BaseModel):
	"""Execution metadata for one analysis run."""

	total_files: int = 0
	parse_success_rate: float = 1.0
	import_resolution_rate: float = 1.0
	call_resolution_rate: float = 1.0


class DiffSummary(BaseModel):
	"""Summary of diff-level changes."""

	files_changed: int = 0
	hunks: int = 0
	changed_symbols: int = 0


class ImpactReport(BaseModel):
	"""Final impact analysis report."""

	project_path: str
	diff_result: DiffResult
	diff_summary: DiffSummary
	changed_symbols: list[ChangedSymbol] = Field(default_factory=list)
	affected_symbols: list[AffectedSymbol] = Field(default_factory=list)
	propagation_paths: list[PropagationPath] = Field(default_factory=list)
	overall_risk: RiskScore
	confidence: ConfidenceLevel
	explanation: LLMExplanation | None = None
	metadata: AnalysisMetadata

	@property
	def overall_risk_level(self) -> RiskLevel:
		"""Return overall risk level.

		Returns:
			RiskLevel: Computed overall risk level.
		"""
		return self.overall_risk.level
