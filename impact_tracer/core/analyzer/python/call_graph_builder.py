"""Call graph builder for Python symbol dependencies.

Layer: Engines (Layer 3)
Responsibility: Build caller → callee relationships from AST call sites.
Implements: PRD FR-SA-06 and Phase 1 Task 1.5.
"""

from __future__ import annotations

import ast
from pathlib import Path

from pydantic import BaseModel, Field

from impact_tracer.models.symbol import FileSymbolTable, SymbolTable


class CallGraphResult(BaseModel):
    """Result payload for call graph construction."""

    edges: list[tuple[str, str]] = Field(default_factory=list)
    unresolved_calls: int = 0
    total_calls: int = 0

    @property
    def call_resolution_rate(self) -> float:
        """Return the ratio of resolved call sites.

        Returns:
            float: Resolution rate in [0.0, 1.0].
        """
        if self.total_calls == 0:
            return 1.0
        resolved_calls = self.total_calls - self.unresolved_calls
        return resolved_calls / self.total_calls


class CallGraphBuilder:
    """Build call graph edges from symbol tables and source AST."""

    def build(self, symbol_table: SymbolTable) -> CallGraphResult:
        """Build caller/callee edges from project symbols.

        Args:
            symbol_table: Project symbol table from AST parser.

        Returns:
            CallGraphResult: Resolved edges and resolution stats.
        """
        name_index = self._build_symbol_name_index(symbol_table)
        edges: set[tuple[str, str]] = set()
        unresolved_calls = 0
        total_calls = 0

        for file_table in symbol_table.files:
            if file_table.parse_error:
                continue

            source_path = Path(file_table.file_path)
            source_code = source_path.read_text(encoding="utf-8")
            module_tree = ast.parse(source_code)

            file_edges, file_unresolved, file_total = self._extract_file_call_edges(
                tree=module_tree,
                file_table=file_table,
                name_index=name_index,
            )
            edges.update(file_edges)
            unresolved_calls += file_unresolved
            total_calls += file_total

        return CallGraphResult(edges=sorted(edges), unresolved_calls=unresolved_calls, total_calls=total_calls)

    def _extract_file_call_edges(
        self,
        tree: ast.Module,
        file_table: FileSymbolTable,
        name_index: dict[str, list[str]],
    ) -> tuple[list[tuple[str, str]], int, int]:
        file_edges: list[tuple[str, str]] = []
        unresolved_calls = 0
        total_calls = 0

        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue

            caller_id = self._resolve_caller_id(file_table, node)
            if caller_id is None:
                continue

            for call_node in ast.walk(node):
                if not isinstance(call_node, ast.Call):
                    continue

                total_calls += 1
                callee_name = self._callee_name(call_node.func)
                if callee_name is None:
                    unresolved_calls += 1
                    continue

                target_symbols = name_index.get(callee_name, [])
                if not target_symbols:
                    unresolved_calls += 1
                    continue

                for callee_id in target_symbols:
                    if callee_id != caller_id:
                        file_edges.append((caller_id, callee_id))

        return file_edges, unresolved_calls, total_calls

    def _resolve_caller_id(self, file_table: FileSymbolTable, node: ast.FunctionDef | ast.AsyncFunctionDef) -> str | None:
        function_name = node.name
        for symbol in file_table.symbols:
            if symbol.name != function_name:
                continue
            if symbol.line_start == node.lineno:
                return symbol.id
        return None

    def _callee_name(self, expression: ast.expr) -> str | None:
        if isinstance(expression, ast.Name):
            return expression.id
        if isinstance(expression, ast.Attribute):
            return expression.attr
        return None

    def _build_symbol_name_index(self, symbol_table: SymbolTable) -> dict[str, list[str]]:
        name_index: dict[str, list[str]] = {}
        for symbol in symbol_table.symbols:
            name_index.setdefault(symbol.name, []).append(symbol.id)
        return name_index


def build_call_edges(symbol_table: SymbolTable) -> CallGraphResult:
    """Compatibility helper to build call edges.

    Args:
        symbol_table: Parsed project symbol table.

    Returns:
        CallGraphResult: Edges and resolution metrics.
    """
    builder = CallGraphBuilder()
    return builder.build(symbol_table)
