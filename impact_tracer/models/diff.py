"""Layer 2 diff and change-detection models.

Layer: Models (Layer 2)
Responsibility: Typed schemas for unified diff parsing and changed symbols.
Implements: Phase 2 Task 2.1.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class ChangeType(str, Enum):
	"""Supported change classifications."""

	ADDITION = "ADDITION"
	DELETION = "DELETION"
	MODIFICATION = "MODIFICATION"
	RENAME = "RENAME"
	SIGNATURE_CHANGE = "SIGNATURE_CHANGE"
	BODY_CHANGE = "BODY_CHANGE"
	DOCSTRING_CHANGE = "DOCSTRING_CHANGE"


class Hunk(BaseModel):
	"""Represents one unified diff hunk."""

	file_path: str
	old_start: int
	old_len: int
	new_start: int
	new_len: int
	added_lines: list[str] = Field(default_factory=list)
	deleted_lines: list[str] = Field(default_factory=list)
	context_lines: list[str] = Field(default_factory=list)
	base_change_type: ChangeType
	semantic_change_type: ChangeType


class ChangedSymbol(BaseModel):
	"""Represents a symbol inferred as changed from diff hunks."""

	symbol_id: str
	file_path: str
	line_start: int
	line_end: int
	change_type: ChangeType


class DiffResult(BaseModel):
	"""Parsed unified diff result."""

	files_changed: list[str] = Field(default_factory=list)
	hunks: list[Hunk] = Field(default_factory=list)
	changed_symbols: list[ChangedSymbol] = Field(default_factory=list)
