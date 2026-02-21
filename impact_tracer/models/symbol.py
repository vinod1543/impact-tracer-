"""Layer 2 symbol models for AST-extracted code entities.

Layer: Models (Layer 2)
Responsibility: Typed Pydantic schemas for symbols and imports.
Implements: PRD §11.2 Symbol schema and Phase 1 Task 1.1.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class SymbolType(str, Enum):
    """Supported symbol categories for AST extraction."""

    FUNCTION = "FUNCTION"
    CLASS = "CLASS"
    METHOD = "METHOD"
    MODULE = "MODULE"


class ImportType(str, Enum):
    """Supported import statement categories."""

    IMPORT = "IMPORT"
    FROM_IMPORT = "FROM_IMPORT"


class ImportSymbol(BaseModel):
    """Represents one imported symbol from an import statement."""

    name: str
    alias: str | None = None


class ImportStatement(BaseModel):
    """Represents an import statement discovered in AST."""

    import_type: ImportType
    module: str | None = None
    level: int = 0
    symbols: list[ImportSymbol] = Field(default_factory=list)
    line: int = 0


class Symbol(BaseModel):
    """Represents a code symbol discovered from source files."""

    id: str
    name: str
    type: SymbolType
    module: str
    file_path: str
    line_start: int
    line_end: int
    is_public: bool
    fan_in: int = 0
    fan_out: int = 0
    decorators: list[str] = Field(default_factory=list)
    signature: str | None = None


class FileSymbolTable(BaseModel):
    """AST extraction output for a single file."""

    file_path: str
    module: str
    symbols: list[Symbol] = Field(default_factory=list)
    imports: list[ImportStatement] = Field(default_factory=list)
    parse_error: str | None = None


class SymbolTable(BaseModel):
    """Aggregated AST extraction output for a project."""

    project_path: str
    files: list[FileSymbolTable] = Field(default_factory=list)

    @property
    def symbols(self) -> list[Symbol]:
        """Return flattened symbols across all files.

        Returns:
            list[Symbol]: Flattened symbol collection.
        """
        flattened_symbols: list[Symbol] = []
        for file_table in self.files:
            flattened_symbols.extend(file_table.symbols)
        return flattened_symbols

