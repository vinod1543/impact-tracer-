"""AST parser for Python source analysis.

Layer: Engines (Layer 3)
Responsibility: Parse Python files and extract symbols/imports safely.
Implements: PRD FR-SA-01..FR-SA-04, FR-SA-11 and Phase 1 Task 1.3.
"""

from __future__ import annotations

import ast
from pathlib import Path

from impact_tracer.models.symbol import (
    FileSymbolTable,
    ImportStatement,
    ImportSymbol,
    ImportType,
    Symbol,
    SymbolTable,
    SymbolType,
)


class PythonAstParser:
    """Extract symbols and imports from Python files using stdlib AST."""

    API_DECORATOR_NAMES = {
        "route",
        "api_route",
        "get",
        "post",
        "put",
        "patch",
        "delete",
        "options",
        "head",
        "websocket",
    }

    def parse_project(self, project_path: str) -> SymbolTable:
        """Parse all Python files under a project path.

        Args:
            project_path: Root path of the target project.

        Returns:
            SymbolTable: Aggregated parsed output.
        """
        root_path = Path(project_path).resolve()
        file_tables: list[FileSymbolTable] = []

        for file_path in sorted(root_path.rglob("*.py")):
            if self._should_skip_path(file_path):
                continue
            file_tables.append(self.parse_file(file_path, root_path))

        return SymbolTable(project_path=str(root_path), files=file_tables)

    def parse_file(self, file_path: Path, project_root: Path) -> FileSymbolTable:
        """Parse one Python file into symbols and imports.

        Args:
            file_path: Python file path.
            project_root: Project root used for module resolution.

        Returns:
            FileSymbolTable: Parsed symbols and imports. Syntax errors are returned in parse_error.
        """
        source = file_path.read_text(encoding="utf-8")
        module_name = self._module_name(file_path, project_root)

        try:
            tree = ast.parse(source)
        except SyntaxError as error:
            return FileSymbolTable(
                file_path=str(file_path),
                module=module_name,
                symbols=[],
                imports=[],
                parse_error=f"SyntaxError at line {error.lineno}: {error.msg}",
            )

        symbols: list[Symbol] = []
        imports: list[ImportStatement] = []

        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                symbols.append(self._build_function_symbol(node=node, module_name=module_name, file_path=file_path))
            elif isinstance(node, ast.ClassDef):
                symbols.append(self._build_class_symbol(node=node, module_name=module_name, file_path=file_path))
                symbols.extend(self._build_method_symbols(node=node, module_name=module_name, file_path=file_path))
            elif isinstance(node, ast.Import):
                imports.append(self._build_import_statement_from_import(node))
            elif isinstance(node, ast.ImportFrom):
                imports.append(self._build_import_statement_from_from(node))

        return FileSymbolTable(file_path=str(file_path), module=module_name, symbols=symbols, imports=imports)

    def _build_function_symbol(self, node: ast.FunctionDef | ast.AsyncFunctionDef, module_name: str, file_path: Path) -> Symbol:
        decorators = [self._expr_to_name(dec) for dec in node.decorator_list]
        signature = self._function_signature(node)
        symbol_name = node.name
        symbol_type = SymbolType.API_ENDPOINT if self._is_api_endpoint(decorators) else SymbolType.FUNCTION
        return Symbol(
            id=f"{module_name}.{symbol_name}",
            name=symbol_name,
            type=symbol_type,
            module=module_name,
            file_path=str(file_path),
            line_start=node.lineno,
            line_end=getattr(node, "end_lineno", node.lineno),
            is_public=not symbol_name.startswith("_"),
            decorators=decorators,
            signature=signature,
        )

    def _build_class_symbol(self, node: ast.ClassDef, module_name: str, file_path: Path) -> Symbol:
        decorators = [self._expr_to_name(dec) for dec in node.decorator_list]
        symbol_name = node.name
        return Symbol(
            id=f"{module_name}.{symbol_name}",
            name=symbol_name,
            type=SymbolType.CLASS,
            module=module_name,
            file_path=str(file_path),
            line_start=node.lineno,
            line_end=getattr(node, "end_lineno", node.lineno),
            is_public=not symbol_name.startswith("_"),
            decorators=decorators,
            signature=None,
        )

    def _build_method_symbols(self, node: ast.ClassDef, module_name: str, file_path: Path) -> list[Symbol]:
        method_symbols: list[Symbol] = []
        for child in node.body:
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                decorators = [self._expr_to_name(dec) for dec in child.decorator_list]
                signature = self._function_signature(child)
                symbol_type = SymbolType.API_ENDPOINT if self._is_api_endpoint(decorators) else SymbolType.METHOD
                method_symbols.append(
                    Symbol(
                        id=f"{module_name}.{node.name}.{child.name}",
                        name=child.name,
                        type=symbol_type,
                        module=module_name,
                        file_path=str(file_path),
                        line_start=child.lineno,
                        line_end=getattr(child, "end_lineno", child.lineno),
                        is_public=not child.name.startswith("_"),
                        decorators=decorators,
                        signature=signature,
                    )
                )
        return method_symbols

    def _build_import_statement_from_import(self, node: ast.Import) -> ImportStatement:
        return ImportStatement(
            import_type=ImportType.IMPORT,
            module=None,
            level=0,
            symbols=[ImportSymbol(name=item.name, alias=item.asname) for item in node.names],
            line=node.lineno,
        )

    def _build_import_statement_from_from(self, node: ast.ImportFrom) -> ImportStatement:
        return ImportStatement(
            import_type=ImportType.FROM_IMPORT,
            module=node.module,
            level=node.level,
            symbols=[ImportSymbol(name=item.name, alias=item.asname) for item in node.names],
            line=node.lineno,
        )

    def _module_name(self, file_path: Path, project_root: Path) -> str:
        relative_path = file_path.relative_to(project_root)
        return ".".join(relative_path.with_suffix("").parts)

    def _should_skip_path(self, file_path: Path) -> bool:
        skip_tokens = {".venv", "venv", "site-packages", "__pycache__"}
        return any(token in skip_tokens for token in file_path.parts)

    def _expr_to_name(self, expression: ast.expr) -> str:
        if isinstance(expression, ast.Name):
            return expression.id
        if isinstance(expression, ast.Attribute):
            if isinstance(expression.value, ast.Name):
                return f"{expression.value.id}.{expression.attr}"
            return expression.attr
        if isinstance(expression, ast.Call):
            return self._expr_to_name(expression.func)
        return ast.dump(expression, annotate_fields=False)

    def _function_signature(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> str:
        arg_names = [arg.arg for arg in node.args.args]
        return_annotation = self._annotation_to_text(node.returns)
        args_text = ", ".join(arg_names)
        if return_annotation:
            return f"({args_text}) -> {return_annotation}"
        return f"({args_text})"

    def _annotation_to_text(self, annotation: ast.expr | None) -> str | None:
        if annotation is None:
            return None
        if isinstance(annotation, ast.Name):
            return annotation.id
        if isinstance(annotation, ast.Attribute):
            return annotation.attr
        return ast.dump(annotation, annotate_fields=False)

    def _is_api_endpoint(self, decorators: list[str]) -> bool:
        for decorator in decorators:
            normalized = decorator.split("(", 1)[0].strip().lower()
            suffix = normalized.split(".")[-1]
            if suffix in self.API_DECORATOR_NAMES:
                return True
        return False


def parse_project(project_path: str) -> SymbolTable:
    """Compatibility helper for project parsing.

    Args:
        project_path: Root path of project.

    Returns:
        SymbolTable: Aggregated project symbols and imports.
    """
    parser = PythonAstParser()
    return parser.parse_project(project_path)
