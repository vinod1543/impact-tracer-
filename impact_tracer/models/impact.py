"""Layer 2 impact analysis models.

Layer: Models (Layer 2)
Responsibility: Typed schemas for affected symbols and risk output.
Implements: Phase 2 Task 2.2.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field

from impact_tracer.models.diff import ChangeType
from impact_tracer.models.symbol import Symbol


class RiskLevel(str, Enum):
	"""Risk severity levels."""

	CRITICAL = "CRITICAL"
	HIGH = "HIGH"
	MEDIUM = "MEDIUM"
	LOW = "LOW"


class ConfidenceLevel(str, Enum):
	"""Confidence bucket for impact output."""

	HIGH = "HIGH"
	MEDIUM = "MEDIUM"
	LOW = "LOW"


class PropagationChangeType(str, Enum):
	"""Depth type for propagated dependencies."""

	DIRECT = "DIRECT"
	TRANSITIVE = "TRANSITIVE"


class PropagationPath(BaseModel):
	"""Represents one propagation chain from changed to affected symbol."""

	source_symbol_id: str
	target_symbol_id: str
	path: list[str] = Field(default_factory=list)


class AffectedSymbol(BaseModel):
	"""Represents a symbol impacted by the change."""

	symbol: Symbol
	propagation_depth: int
	risk_score: float = 0.0
	risk_level: RiskLevel = RiskLevel.LOW
	propagation_path: list[str] = Field(default_factory=list)
	change_type: PropagationChangeType = PropagationChangeType.DIRECT


class RiskScore(BaseModel):
	"""Aggregated risk output with factor breakdown."""

	value: float
	level: RiskLevel
	confidence: ConfidenceLevel
	factors: dict[str, float] = Field(default_factory=dict)


class ScoringInput(BaseModel):
	"""Inputs used for per-symbol scoring."""

	fan_in: int
	depth: int
	change_type: ChangeType
	is_public: bool
	has_tests: bool
