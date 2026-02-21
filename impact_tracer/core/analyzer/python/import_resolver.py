"""Import resolver for Python AST imports.

Layer: Engines (Layer 3)
Responsibility: Resolve absolute and relative imports into canonical symbol targets.
Implements: PRD FR-SA-04, FR-SA-05 and Phase 1 Task 1.4.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from impact_tracer.models.symbol import ImportStatement, ImportType


class ImportResolutionResult(BaseModel):
    """Resolved import map for a module."""

    module: str
    import_map: dict[str, str] = Field(default_factory=dict)
    unresolved: list[str] = Field(default_factory=list)


def resolve_imports(current_module: str, imports: list[ImportStatement]) -> ImportResolutionResult:
    """Resolve import statements for a module.

    Args:
        current_module: Current module path (for example, ``package.payments.validator``).
        imports: Import statements extracted from AST.

    Returns:
        ImportResolutionResult: Canonical mapping of local names to absolute targets.
    """
    import_map: dict[str, str] = {}
    unresolved: list[str] = []

    for statement in imports:
        if statement.import_type == ImportType.IMPORT:
            _resolve_direct_import(statement, import_map)
            continue

        resolved_module = _resolve_from_module(current_module, statement.module, statement.level)
        if resolved_module is None:
            unresolved.extend([item.name for item in statement.symbols])
            continue

        for imported_symbol in statement.symbols:
            local_name = imported_symbol.alias or imported_symbol.name
            if imported_symbol.name == "*":
                import_map[local_name] = f"{resolved_module}.*"
                continue
            import_map[local_name] = f"{resolved_module}.{imported_symbol.name}"

    return ImportResolutionResult(module=current_module, import_map=import_map, unresolved=unresolved)


def _resolve_direct_import(statement: ImportStatement, import_map: dict[str, str]) -> None:
    for imported_symbol in statement.symbols:
        local_name = imported_symbol.alias or imported_symbol.name.split(".")[-1]
        import_map[local_name] = imported_symbol.name


def _resolve_from_module(current_module: str, target_module: str | None, level: int) -> str | None:
    if level <= 0:
        return target_module

    package_parts = current_module.split(".")[:-1]
    climb = max(level - 1, 0)
    prefix_length = len(package_parts) - climb
    if prefix_length < 0:
        return None

    base_parts = package_parts[:prefix_length]
    target_parts = target_module.split(".") if target_module else []
    resolved_parts = base_parts + target_parts
    if not resolved_parts:
        return None

    return ".".join(resolved_parts)
