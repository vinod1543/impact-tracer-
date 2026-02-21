"""Unified diff parser and symbol mapper.

Layer: Engines (Layer 3)
Responsibility: Parse unified diffs and map changed line ranges to symbols.
Implements: Phase 2 Tasks 2.3 and 2.4.
"""

from __future__ import annotations

import re

from impact_tracer.models.diff import ChangeType, ChangedSymbol, DiffResult, Hunk
from impact_tracer.models.symbol import SymbolTable

HUNK_HEADER_RE = re.compile(r"^@@\s+-(\d+)(?:,(\d+))?\s+\+(\d+)(?:,(\d+))?\s+@@")


def parse_unified_diff(diff_text: str) -> DiffResult:
	"""Parse unified diff text into structured hunks.

	Args:
		diff_text: Unified diff content.

	Returns:
		DiffResult: Parsed diff structure.
	"""
	if not diff_text.strip():
		return DiffResult()

	files_changed: list[str] = []
	hunks: list[Hunk] = []

	current_file: str | None = None
	lines = diff_text.splitlines()
	index = 0

	while index < len(lines):
		line = lines[index]
		if line.startswith("+++ "):
			current_file = line.removeprefix("+++ ").strip()
			if current_file.startswith("b/"):
				current_file = current_file[2:]
			if current_file not in files_changed:
				files_changed.append(current_file)
			index += 1
			continue

		header_match = HUNK_HEADER_RE.match(line)
		if not header_match or current_file is None:
			index += 1
			continue

		old_start = int(header_match.group(1))
		old_len = int(header_match.group(2) or 1)
		new_start = int(header_match.group(3))
		new_len = int(header_match.group(4) or 1)

		index += 1
		added_lines: list[str] = []
		deleted_lines: list[str] = []
		context_lines: list[str] = []

		while index < len(lines):
			next_line = lines[index]
			if next_line.startswith("@@") or next_line.startswith("+++"):
				break
			if next_line.startswith("+") and not next_line.startswith("+++"):
				added_lines.append(next_line[1:])
			elif next_line.startswith("-") and not next_line.startswith("---"):
				deleted_lines.append(next_line[1:])
			else:
				context_lines.append(next_line[1:] if next_line.startswith(" ") else next_line)
			index += 1

		base_change = _classify_base_change(added_lines, deleted_lines)
		semantic_change = _classify_semantic_change(base_change, added_lines, deleted_lines)

		hunks.append(
			Hunk(
				file_path=current_file,
				old_start=old_start,
				old_len=old_len,
				new_start=new_start,
				new_len=new_len,
				added_lines=added_lines,
				deleted_lines=deleted_lines,
				context_lines=context_lines,
				base_change_type=base_change,
				semantic_change_type=semantic_change,
			)
		)

	return DiffResult(files_changed=files_changed, hunks=hunks, changed_symbols=[])


def map_diff_to_symbols(diff_result: DiffResult, symbol_table: SymbolTable) -> list[ChangedSymbol]:
	"""Map diff hunks to symbols by line overlap.

	Args:
		diff_result: Parsed diff result.
		symbol_table: Parsed project symbol table.

	Returns:
		list[ChangedSymbol]: Mapped changed symbols.
	"""
	changed: list[ChangedSymbol] = []
	seen_symbol_ids: set[str] = set()

	file_map = {table.file_path.replace("\\", "/"): table for table in symbol_table.files}

	for hunk in diff_result.hunks:
		normalized_hunk_file = hunk.file_path.replace("\\", "/")
		matching_table = None
		for file_path, table in file_map.items():
			if file_path.endswith(normalized_hunk_file):
				matching_table = table
				break
		if matching_table is None:
			continue

		hunk_start = min(hunk.old_start, hunk.new_start)
		hunk_end = max(hunk.old_start + max(hunk.old_len, 1), hunk.new_start + max(hunk.new_len, 1))

		for symbol in matching_table.symbols:
			overlaps = not (symbol.line_end < hunk_start or symbol.line_start > hunk_end)
			if not overlaps:
				continue
			if symbol.id in seen_symbol_ids:
				continue
			seen_symbol_ids.add(symbol.id)
			changed.append(
				ChangedSymbol(
					symbol_id=symbol.id,
					file_path=symbol.file_path,
					line_start=symbol.line_start,
					line_end=symbol.line_end,
					change_type=hunk.semantic_change_type,
				)
			)

	# Fallback: if we couldn't map lines to symbols, mark module-level virtual symbol.
	if not changed:
		for file_name in diff_result.files_changed:
			changed.append(
				ChangedSymbol(
					symbol_id=f"module:{file_name}",
					file_path=file_name,
					line_start=0,
					line_end=0,
					change_type=ChangeType.MODIFICATION,
				)
			)

	return changed


def _classify_base_change(added_lines: list[str], deleted_lines: list[str]) -> ChangeType:
	if added_lines and not deleted_lines:
		return ChangeType.ADDITION
	if deleted_lines and not added_lines:
		return ChangeType.DELETION
	return ChangeType.MODIFICATION


def _classify_semantic_change(base_change: ChangeType, added_lines: list[str], deleted_lines: list[str]) -> ChangeType:
	all_changed_lines = [line.strip() for line in added_lines + deleted_lines if line.strip()]

	signature_changed = any(line.startswith("def ") or line.startswith("class ") for line in all_changed_lines)
	if signature_changed:
		return ChangeType.SIGNATURE_CHANGE

	docstring_only = len(all_changed_lines) > 0 and all(_looks_like_docstring_line(line) for line in all_changed_lines)
	if docstring_only:
		return ChangeType.DOCSTRING_CHANGE

	if base_change == ChangeType.ADDITION:
		return ChangeType.ADDITION
	if base_change == ChangeType.DELETION:
		return ChangeType.DELETION
	return ChangeType.BODY_CHANGE


def _looks_like_docstring_line(line: str) -> bool:
	return (
		line.startswith('"""')
		or line.endswith('"""')
		or line.startswith("'''")
		or line.endswith("'''")
		or line.startswith('r"""')
		or line.startswith("r'''")
	)
