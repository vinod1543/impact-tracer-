"""Layer 2 runtime models for trace/log-derived relationships.

Layer: Models (Layer 2)
Responsibility: Typed schemas for runtime nodes/edges before unified graph merge.
Implements: PRD unified graph requirements for runtime-derived dependencies.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class RuntimeNodeType(str, Enum):
	"""Supported runtime node categories."""

	SERVICE = "SERVICE"
	ENDPOINT = "ENDPOINT"
	TABLE = "TABLE"
	QUEUE = "QUEUE"
	EXTERNAL = "EXTERNAL"


class RuntimeNode(BaseModel):
	"""One runtime entity discovered from traces/logs."""

	id: str
	label: str
	node_type: RuntimeNodeType
	metadata: dict[str, str | int | float | bool | None] = Field(default_factory=dict)


class RuntimeEdge(BaseModel):
	"""Directed runtime interaction edge."""

	source: str
	target: str
	edge_type: str = "RUNTIME_CALL"
	confidence: float = 0.8
	call_count: int | None = None
	latency_ms: float | None = None
	metadata: dict[str, str | int | float | bool | None] = Field(default_factory=dict)


class RuntimeTraceGraph(BaseModel):
	"""Runtime dependency graph from trace/log mining."""

	nodes: list[RuntimeNode] = Field(default_factory=list)
	edges: list[RuntimeEdge] = Field(default_factory=list)
