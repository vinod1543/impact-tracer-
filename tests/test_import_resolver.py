"""Unit tests for Python import resolver.

Phase 1, Task 1.4: Validate relative and absolute import mapping.
"""

from __future__ import annotations

from impact_tracer.core.analyzer.python.import_resolver import resolve_imports
from impact_tracer.models.symbol import ImportStatement, ImportSymbol, ImportType


def test_resolve_import_statement_with_alias() -> None:
    """Direct imports keep canonical target with local alias mapping."""
    imports = [
        ImportStatement(
            import_type=ImportType.IMPORT,
            symbols=[ImportSymbol(name="payments.utils", alias="utils")],
            line=1,
        )
    ]

    result = resolve_imports("payments.validator", imports)

    assert result.import_map["utils"] == "payments.utils"
    assert result.unresolved == []


def test_resolve_from_import_absolute() -> None:
    """Absolute from-import resolves module and symbol id."""
    imports = [
        ImportStatement(
            import_type=ImportType.FROM_IMPORT,
            module="payments.shared",
            level=0,
            symbols=[ImportSymbol(name="helper", alias=None)],
            line=1,
        )
    ]

    result = resolve_imports("payments.validator", imports)

    assert result.import_map["helper"] == "payments.shared.helper"


def test_resolve_from_import_relative_multilevel() -> None:
    """Relative import climbs package by dot level and appends target module."""
    imports = [
        ImportStatement(
            import_type=ImportType.FROM_IMPORT,
            module="utils",
            level=2,
            symbols=[ImportSymbol(name="helper", alias="format_helper")],
            line=5,
        )
    ]

    result = resolve_imports("package.payments.validator", imports)

    assert result.import_map["format_helper"] == "package.utils.helper"


def test_resolve_from_import_unresolved_when_climb_exceeds_root() -> None:
    """Resolver marks unresolved when relative level exceeds package root."""
    imports = [
        ImportStatement(
            import_type=ImportType.FROM_IMPORT,
            module="x",
            level=5,
            symbols=[ImportSymbol(name="y", alias=None)],
            line=1,
        )
    ]

    result = resolve_imports("pkg.mod", imports)

    assert result.import_map == {}
    assert result.unresolved == ["y"]
