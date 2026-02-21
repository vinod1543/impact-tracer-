"""Layer 2 infrastructure models for parsed infra entities and relationships.

Layer: Models (Layer 2)
Responsibility: Typed schemas for infrastructure nodes/edges before graph merge.
Implements: PRD unified graph requirements for config-derived dependencies.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class InfraNodeType(str, Enum):
	"""Supported infrastructure node categories."""

	SERVICE = "SERVICE"
	DATABASE = "DATABASE"
	QUEUE = "QUEUE"
	TOPIC = "TOPIC"
	GATEWAY = "GATEWAY"
	NETWORK = "NETWORK"
	OTHER = "OTHER"


class InfraNode(BaseModel):
	"""One infrastructure node from config parsing outputs."""

	id: str
	label: str
	node_type: InfraNodeType
	provider: str | None = None
	metadata: dict[str, str | int | float | bool | None] = Field(default_factory=dict)


class InfraEdge(BaseModel):
	"""Directed relationship between two infra nodes."""

	source: str
	target: str
	edge_type: str = "DEPENDS_ON"
	confidence: float = 1.0
	metadata: dict[str, str | int | float | bool | None] = Field(default_factory=dict)


class InfraTopology(BaseModel):
	"""Parsed infrastructure dependency topology."""

	nodes: list[InfraNode] = Field(default_factory=list)
	edges: list[InfraEdge] = Field(default_factory=list)
