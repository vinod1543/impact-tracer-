# Impact Tracer Schema Reference

Version: 0.1 (MVP)  
Last Updated: 2026-02-21T19:16:16.8986610+05:30

This document is the fixed schema baseline for implementation and tests.

## 1) Scope and Authority

- Purpose: lock the data contracts for Phase 1 and Phase 2 so later phases do not drift.
- Source hierarchy respected: PRD > Plan > Instructions > Execution context.
- Current status:
  - Phase 1 schemas: implemented
  - Phase 2 schemas: implemented
  - Phase 3 schemas: partially implemented (LLM fields present, LLM pipeline pending)

## 2) Core Symbols Schema (Phase 1)

Defined in `impact_tracer/models/symbol.py`.

- SymbolType: `FUNCTION | CLASS | METHOD | MODULE`
- ImportType: `IMPORT | FROM_IMPORT`
- ImportSymbol
  - `name: str`
  - `alias: str | None`
- ImportStatement
  - `import_type: ImportType`
  - `module: str | None`
  - `level: int`
  - `symbols: list[ImportSymbol]`
  - `line: int`
- Symbol
  - `id: str`
  - `name: str`
  - `type: SymbolType`
  - `module: str`
  - `file_path: str`
  - `line_start: int`
  - `line_end: int`
  - `is_public: bool`
  - `fan_in: int`
  - `fan_out: int`
  - `decorators: list[str]`
  - `signature: str | None`
- FileSymbolTable
  - `file_path: str`
  - `module: str`
  - `symbols: list[Symbol]`
  - `imports: list[ImportStatement]`
  - `parse_error: str | None`
- SymbolTable
  - `project_path: str`
  - `files: list[FileSymbolTable]`

## 3) Graph Schema (Phase 1)

Defined in `impact_tracer/models/graph.py`.

- NodeLayer: `MODULE | SYMBOL | SERVICE | INFRA | TABLE`
- EdgeSource: `ast | config | runtime`
- GraphNode
  - `id: str`
  - `label: str`
  - `layer: NodeLayer`
  - `metadata: dict[str, str|int|float|bool|None]`
- GraphEdge
  - `source: str`
  - `target: str`
  - `edge_type: str`
  - `source_type: EdgeSource`
  - `confidence: float`
  - `metadata: dict[str, str|int|float|bool|None]`
- DependencyGraph
  - `nodes: list[GraphNode]`
  - `edges: list[GraphEdge]`

## 4) Diff Schema (Phase 2)

Defined in `impact_tracer/models/diff.py`.

- ChangeType:
  - `ADDITION`
  - `DELETION`
  - `MODIFICATION`
  - `RENAME`
  - `SIGNATURE_CHANGE`
  - `BODY_CHANGE`
  - `DOCSTRING_CHANGE`
- Hunk
  - `file_path: str`
  - `old_start: int`
  - `old_len: int`
  - `new_start: int`
  - `new_len: int`
  - `added_lines: list[str]`
  - `deleted_lines: list[str]`
  - `context_lines: list[str]`
  - `base_change_type: ChangeType`
  - `semantic_change_type: ChangeType`
- ChangedSymbol
  - `symbol_id: str`
  - `file_path: str`
  - `line_start: int`
  - `line_end: int`
  - `change_type: ChangeType`
- DiffResult
  - `files_changed: list[str]`
  - `hunks: list[Hunk]`
  - `changed_symbols: list[ChangedSymbol]`

## 5) Impact Schema (Phase 2)

Defined in `impact_tracer/models/impact.py`.

- RiskLevel: `CRITICAL | HIGH | MEDIUM | LOW`
- ConfidenceLevel: `HIGH | MEDIUM | LOW`
- PropagationChangeType: `DIRECT | TRANSITIVE`
- PropagationPath
  - `source_symbol_id: str`
  - `target_symbol_id: str`
  - `path: list[str]`
- AffectedSymbol
  - `symbol: Symbol`
  - `propagation_depth: int`
  - `risk_score: float`
  - `risk_level: RiskLevel`
  - `propagation_path: list[str]`
  - `change_type: PropagationChangeType`
- RiskScore
  - `value: float`
  - `level: RiskLevel`
  - `confidence: ConfidenceLevel`
  - `factors: dict[str, float]`

## 6) Report Schema (Phase 2 -> Phase 3 bridge)

Defined in `impact_tracer/models/report.py`.

- LLMExplanation
  - `summary: str`
  - `blast_radius: str`
  - `top_risks: list[dict[str, str]]`
  - `recommended_actions: list[str]`
- AnalysisMetadata
  - `total_files: int`
  - `parse_success_rate: float`
  - `import_resolution_rate: float`
  - `call_resolution_rate: float`
- DiffSummary
  - `files_changed: int`
  - `hunks: int`
  - `changed_symbols: int`
- ImpactReport
  - `project_path: str`
  - `diff_result: DiffResult`
  - `diff_summary: DiffSummary`
  - `changed_symbols: list[ChangedSymbol]`
  - `affected_symbols: list[AffectedSymbol]`
  - `propagation_paths: list[PropagationPath]`
  - `overall_risk: RiskScore`
  - `confidence: ConfidenceLevel`
  - `explanation: LLMExplanation | None`
  - `metadata: AnalysisMetadata`

## 7) Contract Rules (Fixed)

- No field removals without schema version bump and migration note.
- New optional fields can be added if backward-compatible.
- `ImpactReport` remains the canonical output model.
- Runtime or infra schema additions (Phase 4+) must extend this file, not replace it.

## 8) Test Alignment

Schema-backed tests currently present:

- `tests/test_ast_parser.py`
- `tests/test_import_resolver.py`
- `tests/test_call_graph_builder.py`
- `tests/test_graph_builder.py`
- `tests/test_diff_parser.py`
- `tests/test_propagator.py`
- `tests/test_scorer.py`
- `tests/test_phase2_analyze.py`
