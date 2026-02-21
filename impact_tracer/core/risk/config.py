"""Risk configuration loader.

Layer: Engines (Layer 3)
Responsibility: Load and validate risk weights for scoring.
Implements: Phase 2 Task 2.7.
"""

from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import BaseModel


class RiskWeights(BaseModel):
	"""Weighted factors for risk scoring formula."""

	fan_in: float = 0.30
	depth: float = 0.20
	change_type: float = 0.20
	symbol_type: float = 0.20
	test_coverage: float = 0.10


def load_risk_weights(weights_path: str = "risk_weights.yaml") -> RiskWeights:
	"""Load risk weights from YAML file.

	Args:
		weights_path: YAML file path.

	Returns:
		RiskWeights: Validated risk weights.
	"""
	path = Path(weights_path)
	if not path.exists():
		return RiskWeights()

	with path.open("r", encoding="utf-8") as file_pointer:
		payload = yaml.safe_load(file_pointer) or {}

	return RiskWeights.model_validate(payload)
