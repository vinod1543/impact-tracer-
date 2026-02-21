"""Layer 2 graph models for dependency graph representation.

Layer: Models (Layer 2)
Responsibility: Typed schemas for graph nodes, edges, and metadata.
Implements: PRD §11.2 and Phase 1 Task 1.2.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class NodeLayer(str, Enum):
	"""Graph layer for a node in the unified graph."""

	MODULE = "MODULE"
	SYMBOL = "SYMBOL"
	SERVICE = "SERVICE"
	INFRA = "INFRA"
	TABLE = "TABLE"


class EdgeSource(str, Enum):
	"""Provenance source for an edge."""

	AST = "ast"
	CONFIG = "config"
	RUNTIME = "runtime"


class GraphNode(BaseModel):
	"""Represents a node in dependency graph."""

	id: str
	label: str
	layer: NodeLayer
	metadata: dict[str, str | int | float | bool | None] = Field(default_factory=dict)


class GraphEdge(BaseModel):
	"""Represents a directed edge in dependency graph."""

	source: str
	target: str
	edge_type: str
	source_type: EdgeSource = EdgeSource.AST
	confidence: float = 1.0
	metadata: dict[str, str | int | float | bool | None] = Field(default_factory=dict)


class DependencyGraph(BaseModel):
	"""Serializable dependency graph model."""

	nodes: list[GraphNode] = Field(default_factory=list)
	edges: list[GraphEdge] = Field(default_factory=list)

