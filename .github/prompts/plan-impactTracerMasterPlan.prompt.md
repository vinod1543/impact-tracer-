# Impact Tracer — 24-Hour Hackathon Master Execution Plan
**Version:** 1.0.0 | **Status:** ACTIVE — Master Reference  
**Date:** February 21, 2026  
**Project:** Impact Tracer — Intelligent Code Change Impact Analysis System  
**Constraint:** Python-only MVP | 24 hours | Limited manpower | Industry-expert judges  

> **AGENT DIRECTIVE:** This document is the authoritative master plan for all implementation decisions during this hackathon. Every agent, contributor, and automated step must defer to this plan and the companion PRD (`PRD.prompt.md`) at all times. When in conflict, this plan governs execution order and scope; the PRD governs correctness of features.

---

## Table of Contents

1. [Overall Strategy](#1-overall-strategy)
2. [Architecture Decisions](#2-architecture-decisions)
3. [Tech Stack](#3-tech-stack)
4. [MVP Definition](#4-mvp-definition)
5. [Risk Buffer Strategy](#5-risk-buffer-strategy)
6. [Phased Roadmap](#6-phased-roadmap)
7. [Hour-by-Hour Timeline](#7-hour-by-hour-timeline)
8. [Git Branching Strategy](#8-git-branching-strategy)
9. [Demo Preparation Guide](#9-demo-preparation-guide)
10. [Backup & Contingency Plans](#10-backup--contingency-plans)
11. [Final Submission Checklist](#11-final-submission-checklist)

---

## 1. Overall Strategy

### 1.1 Winning Philosophy

> **Build a demo that WORKS, not a system that is COMPLETE.**

Industry-expert judges will evaluate on three axes:
1. **Technical depth** — does the core engine do something genuinely hard?
2. **Product clarity** — is the problem and solution immediately understandable?
3. **Live reliability** — does the demo run without a crash in front of them?

The strategy is to nail a **narrow, deep, reliable vertical slice** of the full PRD vision, rather than a shallow sprint across all features. Every phase is designed with a "demo-safe stop point" — a state where the product can be demonstrated even if subsequent phases are incomplete.

### 1.2 Execution Priorities

| Priority | Rule |
|---|---|
| P0 — Non-negotiable | The end-to-end pipeline MUST work: NL query in → impact report out in terminal |
| P0 — Non-negotiable | The NL CLI intent parser MUST correctly handle the 7 demo query patterns |
| P0 — Non-negotiable | CLI output (Rich) must be visually impressive: coloured risk tables, propagation trees, spinners |
| P0 — Non-negotiable | The demo scenario (PRD Appendix E) must run without error |
| P1 — High value | MCP server (stdio) wired to orchestrator with all 4 tools |
| P1 — High value | Multi-turn REPL session context (follow-up questions work) |
| P1 — High value | Infrastructure config parsing + runtime trace mining fused into unified graph |
| P2 — If time allows | JSON output flag for CI/CD scriptability |
| P3 — Stretch | MCP SSE transport, Docker, GitHub Actions |

### 1.3 The "Narrative Arc" for Judges

Every engineering decision must support this story:
> *"We built an AI-native developer terminal tool that speaks plain English. You ask it what will break. It understands you, queries a live unified dependency graph spanning code + infrastructure + runtime traces, and tells you exactly what to fix — before you merge. In 24 hours."*

The demo script in Section 9 is designed around this arc.

---

## 2. Architecture Decisions

### 2.1 Decision Log

All architectural choices below are **final**. Do not re-litigate during the hackathon.

| ID | Decision | Chosen Option | Rejected Alternative | Rationale |
|---|---|---|---|---|
| AD-01 | AST parser library | Python stdlib `ast` | `tree-sitter`, `astroid` | Zero install cost; fully sufficient for Python; no dependency hell |
| AD-02 | Graph library | `NetworkX` | `igraph`, `rustworkx` | Industry standard; rich algorithm library; serializable; excellent docs |
| AD-03 | CLI framework | `prompt_toolkit` + `rich` | `Typer`, `Click` | `prompt_toolkit` enables a full interactive REPL with history and multiline input — required for conversational NL interface; `rich` handles all rendering |
| AD-04 | API framework | ~~FastAPI~~ **removed** | Flask, Django | No REST API server. MCP is the programmatic interface. Removing HTTP server eliminates a dependency and demo process management complexity. |
| AD-05 | Data models | `Pydantic v2` | `dataclasses`, `attrs` | Strict validation; JSON serialization built-in; MCP tool handler outputs use `.model_dump()` |
| AD-06 | Graph visualization | `Pyvis` (HTML) + `Vis.js` | `D3.js`, `Graphviz`, `Plotly` | Pyvis generates interactive HTML with zero frontend code; perfect for hackathon speed |
| AD-07 | LLM backend | `OpenAI GPT-4o` primary, `Ollama` fallback | Raw `httpx` calls | Official SDK; structured output JSON mode; reliability for demo |
| AD-08 | Propagation algorithm | `BFS` (Breadth-First Search) | `DFS` | BFS naturally produces depth-layered results; depth is a key risk factor; easier to reason about |
| AD-09 | Config management | `Pydantic Settings` + `risk_weights.yaml` | Hardcoded constants | Judges can see configurable weights; demonstrates production-readiness thinking |
| AD-10 | Web UI approach | ~~FastAPI + Pyvis~~ **removed** | React/Next.js | No web UI. Graph is exported as a static `graph.html` file; users open it locally. No HTTP server needed. |
| AD-11 | Dependency management | `Poetry` | `pip` + `requirements.txt` | Reproducible builds; `pyproject.toml` is modern; `poetry install` is one command |
| AD-12 | Packaging | Single installable Python package (`impact-tracer`) | Monorepo scripts | Judges can `pip install` and run `impact-tracer analyze` immediately |
| AD-13 | MCP transport | stdio (primary), SSE (secondary) | WebSocket, gRPC | stdio requires zero additional server infrastructure; works natively with Claude Desktop |
| AD-14 | MCP ↔ core communication | Direct orchestrator calls | HTTP proxy to FastAPI | Eliminates network hop; works without any HTTP server running; zero latency overhead; single process for demo |
| AD-15 | Terraform parsing | `python-hcl2` | `pyhcl`, regex | Only maintained HCL2 parser for Python; handles Terraform 0.12+ syntax cleanly |
| AD-16 | Runtime data aggregation | `pandas` | manual dicts, `polars` | Industry standard; groupby + agg is natural fit for OTEL span aggregation; zero custom code needed |
| AD-17 | Unified graph strategy | Single `networkx.DiGraph` with typed nodes/edges | separate graphs per source | One graph = one traversal algorithm; cross-layer propagation (code → service → infra) is free |

### 2.2 Layered Architecture

The system is built in strict layers. **No layer may import from a layer above it.**

```
Layer 5: Interfaces       (cli/, mcp/)
Layer 4: Orchestration    (core/orchestrator.py)
Layer 3: Engines          (analyzer/, infra/, runtime/, graph/, diff/, propagation/, risk/, llm/)
Layer 2: Models           (models/)
Layer 1: Config           (config/)
Layer 0: Tests            (tests/)
```

### 2.3 Data Flow Contract

The canonical data flow (from PRD §11.1) is the **law**. Every engine receives and emits Pydantic models. No raw dicts are passed between layers.

```
Git Diff (str) + Infra Config Files (paths) + Runtime Trace Files (paths)
  → DiffParser          → DiffResult
  → ASTParser           → SymbolTable
  → InfraParser         → List[ServiceNode | InfraNode | NetworkNode]  (parallel)
  → RuntimeMiner        → List[RuntimeEdge | DataAccessEdge]           (parallel)
  → GraphBuilder        → UnifiedDependencyGraph  (merges all four sources)
  → DiffSymbolMapper    → List[ChangedSymbol]
  → Propagator          → List[AffectedSymbol]  (crosses code → service → infra → table)
  → RiskScorer          → RiskReport
  → LLMExplainer        → LLMExplanation
  → ReportGenerator     → ImpactReport
```

---

## 3. Tech Stack

### 3.1 Core Stack (P0 — Must Install)

| Component | Library / Tool | Version | Purpose |
|---|---|---|---|
| Language | Python | 3.11+ | All code |
| CLI (REPL) | `prompt_toolkit` | ≥ 3.0 | Interactive REPL with history, multiline input |
| CLI (render) | `rich` | ≥ 13.7 | All terminal output: tables, panels, trees, spinners |
| Intent parser | `openai` | ≥ 1.14 | GPT-4o function calling for NL → operation mapping |
| MCP server | `mcp[cli]` | ≥ 1.0 | MCP protocol implementation |
| Data models | `pydantic` | v2 (≥ 2.6) | All data structures |
| Settings | `pydantic-settings` | ≥ 2.2 | Config management |
| Graph | `networkx` | ≥ 3.2 | Unified dependency graph algorithms |
| Graph viz | `pyvis` | ≥ 0.3.2 | Static graph.html export |
| YAML config | `pyyaml` | ≥ 6.0 | Risk weights config + Docker Compose/K8s parsing |
| HTTP client | `httpx` | ≥ 0.27 | Async HTTP for Ollama fallback |
| Terraform parsing | `python-hcl2` | ≥ 4.3 | Parse HCL2 resource blocks and interpolations |
| Config validation | `jsonschema` | ≥ 4.21 | Validate parsed infra config schemas |
| Runtime aggregation | `pandas` | ≥ 2.2 | Aggregate OTEL spans and log entries by service pair |

### 3.2 Development Stack (P0 — Must Install)

| Component | Library / Tool | Purpose |
|---|---|---|
| Test runner | `pytest` | Unit + integration tests |
| Test coverage | `pytest-cov` | Coverage reporting |
| Async tests | `pytest-asyncio` | Testing async functions |
| Linter | `ruff` | Fast Python linter (replaces flake8/black) |
| Type checker | `mypy` | Static type checking |
| Dependency mgmt | `poetry` | Package and dependency management |

### 3.3 Optional / P1 Stack

| Component | Library / Tool | Purpose | When to Add |
|---|---|---|---|
| Local LLM | `ollama` (external) | LLM fallback, demo safety | Phase 3 |
| Jinja2 | `jinja2` | HTML report templating | Phase 4 |
| MCP SDK | `mcp[cli]` | MCP server interface | Phase 4c |
| Starlette | `starlette` | MCP SSE transport (optional) | Phase 4c |
| Containerization | `docker` + `docker-compose` | Portable demo | Phase 5 |

### 3.4 `pyproject.toml` Skeleton

```toml
[tool.poetry]
name = "impact-tracer"
version = "0.1.0"
description = "Intelligent Python code change impact analysis"
packages = [{include = "impact_tracer"}]

[tool.poetry.scripts]
impact-tracer = "impact_tracer.cli.main:main"
impact-tracer-mcp = "impact_tracer.mcp.server:main"

[tool.poetry.dependencies]
python = "^3.11"
prompt_toolkit = "^3.0"
rich = "^13.7"
pydantic = "^2.6"
pydantic-settings = "^2.2"
networkx = "^3.2"
pyvis = "^0.3.2"
openai = "^1.14"
pyyaml = "^6.0"
httpx = "^0.27"
python-hcl2 = "^4.3"
jsonschema = "^4.21"
pandas = "^2.2"
mcp = {extras = ["cli"], version = "^1.0"}

[tool.poetry.group.dev.dependencies]
pytest = "^8.1"
pytest-cov = "^5.0"
pytest-asyncio = "^0.23"
ruff = "^0.4"
mypy = "^1.9"
```

---

## 4. MVP Definition

### 4.1 Minimum Viable Product — Hard Definition

The MVP is considered **complete** when ALL of the following are true:

| # | Condition | How to Verify |
|---|---|---|
| MVP-01 | `impact-tracer "what breaks if I change validate() in payments/"` runs end-to-end and prints an impact report | Run it |
| MVP-02 | CLI correctly identifies intent from the query, asks a clarifying question if project path is missing, then runs analysis | Interactive test |
| MVP-03 | CLI output displays: changed symbols, affected symbols ranked by risk, overall risk score, LLM explanation | Visual inspection |
| MVP-04 | At least one CRITICAL-risk symbol is correctly identified when a high-fan-in function signature is changed | Run demo scenario from PRD Appendix E |
| MVP-05 | A LOW-risk result is correctly returned for a docstring-only query | Run edge-case test |
| MVP-06 | `--format json` flag produces a valid, parseable `ImpactReport` JSON on stdout | `jq .` on output |
| MVP-07 | A static HTML dependency graph is generated with `impact-tracer "show me the graph for payments/"` | Open in browser |
| MVP-08 | All P0 unit tests pass | `pytest tests/ -v` |

### 4.2 MVP Feature Matrix

| Feature | P0 (MVP) | P1 (Enhancement) | P2 (Stretch) |
|---|---|---|---|
| AST parsing: functions, classes, imports | ✅ | | |
| Module dependency graph (MDG) | ✅ | | |
| Symbol dependency graph (SDG) | ✅ | | |
| Diff parser (unified format) | ✅ | | |
| BFS change propagation | ✅ | | |
| Risk scoring (5-factor model) | ✅ | | |
| CLI output (Rich-formatted) | ✅ | | |
| JSON output | ✅ | | |
| LLM explanation (GPT-4o) | ✅ | | |
| LLM graceful degradation | ✅ | | |
| Docker Compose config parsing (pyyaml) | | ✅ | |
| Kubernetes manifest parsing (pyyaml) | | ✅ | |
| Terraform HCL parsing (python-hcl2) | | ✅ | |
| OTEL trace mining (pandas aggregation) | | ✅ | |
| Nginx/API gateway log parsing | | ✅ | |
| Postgres query log parsing | | ✅ | |
| Unified graph (code + infra + runtime) | | ✅ | |
| Ghost dependency detection | | ✅ | |
| NL CLI: multi-turn REPL session context | | ✅ | |
| NL CLI: single-shot mode + `--format json` | | ✅ | |
| Markdown report output | | ✅ | |
| Incremental graph cache | | ✅ | |
| Circular dependency detection | | ✅ | |
| Configurable risk weights (YAML) | | ✅ | |
| MCP server (stdio transport) | | ✅ | |
| Docker container | | | ✅ |
| GitHub Actions YAML | | | ✅ |
| Ollama local fallback | | | ✅ |

---

## 5. Risk Buffer Strategy

### 5.1 Time Risk Management

Every phase has a **hard cut-off time**. When the cut-off is hit, the phase STOPS regardless of completeness, and the fallback plan activates. This is non-negotiable.

| Phase | Planned Duration | Hard Cut-off | If Cut-off Hit |
|---|---|---|---|
| Phase 0 | 1 hour | H+01:00 | Skip pre-reads; go straight to coding |
| Phase 1 | 5 hours | H+06:00 | Stub `call_graph_builder.py`; use import-only graph |
| Phase 2 | 4 hours | H+10:00 | Stub risk scorer with hardcoded weights; BFS must work |
| Phase 3 | 2 hours | H+12:00 | Precompute and cache LLM response for demo; use `--no-llm` |
| Phase 4 | 5 hours | H+17:00 | Skip web dashboard; static HTML export from Pyvis only |
| Phase 5 | 4 hours | H+21:00 | Skip coverage targets; unit tests for core engine only |
| Phase 6 | 3 hours | H+24:00 | Demo must proceed regardless |

### 5.2 Technical Risk Register

| # | Risk | Likelihood | Impact | Mitigation Strategy | Owner |
|---|---|---|---|---|---|
| TR-01 | AST call resolution fails for complex class patterns | High | Medium | Fall back to import-only graph; document as known limitation; confidence = LOW | Phase 1 |
| TR-02 | OpenAI API rate limit or outage during demo | Medium | Critical | Pre-cache demo LLM response in `demo_cache/explanation.json`; load from file if API fails | Phase 3 |
| TR-03 | NetworkX graph too slow for large demo repo | Low | High | Pre-build and serialize graph to `graph.pkl` before demo; load from cache | Phase 1 |
| TR-04 | Pyvis graph too large / unreadable | Medium | Medium | Filter to top-30 nodes by fan-in; add risk-based color filter | Phase 4 |
| TR-05 | BFS produces infinite loop on circular deps | Low | Critical | `visited` set in BFS is mandatory; add cycle detection assertion in test | Phase 2 |
| TR-06 | Demo repo's dynamic imports not resolved | High | Low | Document in demo narrative; use it as a teaching moment about confidence scores | Phase 0 |
| TR-07 | Rich CLI output breaks in judge's terminal | Low | Medium | Test on plain `cmd.exe`, PowerShell, and bash before demo; have screenshot backup | Phase 5 |
| TR-08 | Poetry install fails in demo environment | Medium | High | Provide `requirements.txt` fallback generated by `poetry export` | Phase 0 |

### 5.3 Energy Management

| Hour Range | State | Focus Mode |
|---|---|---|
| H00–H08 | Peak — Fresh | Deep work; complex algorithms |
| H08–H16 | Steady — Good | Integration; UI; testing |
| H16–H20 | Fatigue sets in | Stabilization; bug fixes; no new features |
| H20–H24 | Final push | Demo rehearsal; polish; documentation |

**No new features after H+17:00.** Only bug fixes, demo prep, and polish.

---

## 6. Phased Roadmap

> For each phase: time allocation, tasks, deliverables, validation checklist, and fallback plan.

---

### Phase 0: Preparation
**Duration:** 1 hour (H+00:00 → H+01:00)  
**Goal:** Environment ready, structure in place, team aligned, demo repo selected.

#### Tasks

| # | Task | Detail |
|---|---|---|
| 0.1 | Create project repository | `git init`; push to GitHub; set up `main` and `develop` branches |
| 0.2 | Initialize Poetry project | `poetry new impact-tracer`; configure `pyproject.toml` per Section 3.4 |
| 0.3 | Install all P0 dependencies | `poetry install` — verify no conflicts |
| 0.4 | Scaffold full directory structure | Create all directories and `__init__.py` files per PRD §10.2 |
| 0.5 | Create stub modules | Every module file must exist with a docstring and `pass`; no `ImportError` on project load |
| 0.6 | Set up `settings.py` and `.env.example` | `OPENAI_API_KEY`, `LOG_LEVEL`, `DEMO_MODE` env vars |
| 0.7 | Select and clone demo Python project | Use a FastAPI payments service with 10–20 modules; commit to `demo/` directory |
| 0.8 | Create `risk_weights.yaml` | Default values per PRD §14.2 |
| 0.9 | Set up `pytest` configuration | `pyproject.toml` `[tool.pytest.ini_options]`; create `tests/` with `conftest.py` |
| 0.10 | Create Phase 1 branch | `git checkout -b feature/phase-1-core-parsing` |

#### Deliverables

- `impact_tracer/` package directory with full scaffold (all files exist)
- `pyproject.toml` with pinned dependencies
- `demo/payments_service/` — the target Python project for all demos
- `.env.example` with all required environment variables documented
- `risk_weights.yaml` with default weights
- CI runs `pytest --collect-only` without errors (no tests yet, just collection passes)

#### Validation Checklist

- [ ] `poetry install` completes without errors
- [ ] `python -c "import impact_tracer"` succeeds  
- [ ] `impact-tracer --help` or `impact-tracer` launches the NL CLI without error (even with stubs)
- [ ] `pytest --collect-only` exits 0
- [ ] Demo project has ≥ 3 modules with real inter-imports
- [ ] Git has at least 2 commits on `main`

#### Fallback Plan

If Poetry dependency resolution takes > 20 minutes: use `pip` with a hand-written `requirements.txt` generated from the locked versions. If the demo project selection takes too long: use the project's own `impact_tracer/` source code as the demo target (self-analysis), which is always available.

---

### Phase 1: Core Parsing & Graph
**Duration:** 5 hours (H+01:00 → H+06:00)  
**Goal:** A working static analysis engine that can parse any Python project and produce a serialized dependency graph.  
**Branch:** `feature/phase-1-core-parsing`

#### Tasks

| # | Task | Module | Priority |
|---|---|---|---|
| 1.1 | Implement `models/symbol.py` | `Symbol`, `SymbolType`, `SymbolTable` Pydantic models | P0 |
| 1.2 | Implement `models/graph.py` | `DependencyGraph`, `GraphEdge`, `GraphNode` Pydantic models | P0 |
| 1.3 | Implement `core/analyzer/python/ast_parser.py` | Walk `.py` files; extract function defs, class defs, decorators, line ranges | P0 |
| 1.4 | Implement `core/analyzer/python/import_resolver.py` | Parse `import` and `from...import` statements; resolve relative imports to absolute paths | P0 |
| 1.5 | Implement `core/analyzer/python/call_graph_builder.py` | Walk AST `Call` nodes; map caller → callee by name; resolve within symbol table | P0 |
| 1.6 | Implement `core/graph/graph_builder.py` | Consume `SymbolTable`; build NetworkX `DiGraph`; populate MDG + SDG | P0 |
| 1.7 | Implement `core/graph/graph_store.py` | `save(graph, path)` and `load(path)` using `networkx` + JSON/pickle | P1 |
| 1.8 | Implement `core/graph/graph_query.py` | `predecessors(node)`, `descendants(node)`, `ancestors(node)`, `shortest_path(a,b)` | P0 |
| 1.9 | Write unit tests for `ast_parser.py` | Test with real `.py` snippets: simple function, class method, nested, decorator | P0 |
| 1.10 | Write unit tests for `graph_builder.py` | Build graph from 3-module test fixture; assert correct edge count | P0 |
| 1.11 | Integrate into `core/orchestrator.py` (stub) | `build_graph(project_path) -> DependencyGraph` entry point | P0 |

#### Key Implementation Notes

**`ast_parser.py` — Core Algorithm:**
```
FOR each .py file in project (glob **/*.py, skip venv/site-packages):
  TRY:
    tree = ast.parse(source)
    FOR node in ast.walk(tree):
      IF isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
        extract: name, args, return_annotation, decorators, lineno, end_lineno
      IF isinstance(node, ast.ClassDef):
        extract: name, bases, decorators, lineno, end_lineno
      IF isinstance(node, ast.Import | ast.ImportFrom):
        extract: module, names, level (for relative)
  EXCEPT SyntaxError:
    log warning; continue  ← NEVER crash
```

**`call_graph_builder.py` — Resolution Strategy:**
```
FOR each ast.Call in function body:
  IF call.func is ast.Name:          # simple_function()
    callee_name = call.func.id
  IF call.func is ast.Attribute:     # obj.method() or module.func()
    callee_name = call.func.attr
  Lookup callee_name in local SymbolTable
  IF found: add edge (current_func → callee)
  ELSE: log as unresolved call; increment unresolved_count
         (used for confidence calculation)
```

**`import_resolver.py` — Critical Logic:**
```
GIVEN: "from ..utils import helper" in package/payments/validator.py
  1. Count leading dots (2 = go up 2 levels)
  2. Navigate up from current file path (2 levels)
  3. Append "utils" → resolves to "package.utils"
  4. Map "helper" → "package.utils.helper"
  5. Store in import_map: {local_name: absolute_symbol_id}
```

#### Deliverables

- `ast_parser.py` — fully working, handles syntax errors gracefully
- `import_resolver.py` — resolves relative and absolute imports
- `call_graph_builder.py` — emits caller/callee edges (best-effort)
- `graph_builder.py` — produces a `networkx.DiGraph` from any Python project
- `graph_query.py` — predecessor + descendant queries working
- Unit tests: ≥ 10 tests passing
- `orchestrator.build_graph(demo_project)` works end-to-end

#### Validation Checklist

- [ ] `ast_parser` correctly extracts all function defs from `demo/` project
- [ ] `import_resolver` correctly resolves all intra-project imports in `demo/`
- [ ] `graph_builder` produces a graph with ≥ 10 nodes for the demo project
- [ ] `graph_query.predecessors("payments.validator.BasePaymentValidator.validate")` returns ≥ 2 callers
- [ ] A file with a `SyntaxError` is silently skipped; no crash
- [ ] `pytest tests/test_ast_parser.py tests/test_graph_builder.py` all green
- [ ] `graph_store.save/load` round-trips the graph losslessly

#### Fallback Plan

If `call_graph_builder.py` is not fully working by H+05:00, **drop to import-only graph** (MDG only). The propagation engine will use module-level dependencies instead of symbol-level. Risk scores will still work; accuracy is slightly lower. Document as a known limitation. The demo will still function. Mark call graph as "Phase 1b enhancement."

---

### Phase 2: Impact Engine
**Duration:** 4 hours (H+06:00 → H+10:00)  
**Goal:** Given a diff and a graph, output a ranked list of affected symbols with risk scores.  
**Branch:** `feature/phase-2-impact-engine`

#### Tasks

| # | Task | Module | Priority |
|---|---|---|---|
| 2.1 | Implement `models/diff.py` | `DiffResult`, `Hunk`, `ChangedSymbol`, `ChangeType` Pydantic models | P0 |
| 2.2 | Implement `models/impact.py` | `AffectedSymbol`, `PropagationPath`, `RiskScore`, `RiskLevel`, `ConfidenceLevel` | P0 |
| 2.3 | Implement `core/diff/diff_parser.py` | Parse unified diff string; extract files + line ranges; classify change type | P0 |
| 2.4 | Implement diff → symbol mapper | Given `DiffResult` + `SymbolTable`: map changed line ranges to enclosing AST symbols | P0 |
| 2.5 | Implement `core/propagation/propagator.py` | BFS from `ChangedSymbol[]` over `DependencyGraph`; collect `AffectedSymbol[]` with depth + path | P0 |
| 2.6 | Implement `core/risk/scorer.py` | Compute `RiskScore` per affected symbol using 5-factor weighted formula from PRD §14.2 | P0 |
| 2.7 | Implement `core/risk/config.py` | Load `risk_weights.yaml`; expose typed weight config via Pydantic Settings | P1 |
| 2.8 | Implement confidence calculator | `confidence = f(import_resolution_rate, ast_parse_success_rate, call_resolution_rate)` | P0 |
| 2.9 | Wire into `orchestrator.analyze()` | `analyze(diff_str, project_path) -> ImpactReport` full pipeline | P0 |
| 2.10 | Write unit tests | BFS propagation correctness; risk score boundary tests; diff parser tests | P0 |

#### Key Implementation Notes

**`diff_parser.py` — Unified Diff Parsing:**
```python
# Unified diff hunk header format: @@ -old_start,old_len +new_start,new_len @@
# Regex: r'@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@'
# Classification table:
CHANGE_TYPE_MAP = {
  "only additions, no deletions in hunk":  ChangeType.ADDITION,
  "only deletions, no additions":          ChangeType.DELETION,
  "mixed additions and deletions":         ChangeType.MODIFICATION,
}
# After hunk classification, check:
# - Did function/class signature line change? → SIGNATURE_CHANGE
# - Did only docstring lines change? → DOCSTRING_CHANGE
# - Other body lines changed? → BODY_CHANGE
```

**`propagator.py` — BFS with Depth Tracking:**
```python
def propagate(graph, changed_symbols) -> List[AffectedSymbol]:
    results = {}
    queue = deque()
    visited = set()    # ← MANDATORY: prevents infinite loops on cycles
    
    for sym in changed_symbols:
        queue.append((sym.id, 0, [sym.id]))
    
    while queue:
        node_id, depth, path = queue.popleft()
        if node_id in visited:
            continue
        visited.add(node_id)
        
        for predecessor in graph.predecessors(node_id):
            new_path = path + [predecessor]
            if predecessor not in results or results[predecessor].depth > depth + 1:
                results[predecessor] = AffectedSymbol(
                    symbol_id=predecessor,
                    propagation_depth=depth + 1,
                    propagation_path=new_path
                )
            queue.append((predecessor, depth + 1, new_path))
    
    return list(results.values())
```

**`scorer.py` — Risk Formula Implementation:**
```python
# From PRD §14.2:
# R = w1*F_in + w2*F_depth + w3*F_type + w4*F_symbol + w5*F_test
MAX_FAN_IN = 50  # normalize above this

def score(symbol, depth, change_type, weights) -> float:
    F_in    = min(symbol.fan_in / MAX_FAN_IN, 1.0)
    F_depth = 1.0 / (depth + 1)
    F_type  = CHANGE_TYPE_SCORES[change_type]
    F_sym   = SYMBOL_TYPE_SCORES[symbol.symbol_type]
    F_test  = 1.0 if not symbol.has_tests else 0.3
    
    raw = (weights.fan_in * F_in + weights.depth * F_depth +
           weights.change_type * F_type + weights.symbol_type * F_sym +
           weights.test_coverage * F_test)
    return min(round(raw, 4), 1.0)
```

**Special Risk Rules (from PRD §14.4):**
- Public API change (`__all__` or no leading `_` in package) → auto-elevate to CRITICAL
- Framework decorator (`@router.get`, `@app.route`) on changed symbol → elevate
- No `test_*.py` file referencing the changed module → apply full `F_test = 1.0` penalty

#### Deliverables

- `diff_parser.py` — correctly parses unified diffs
- `propagator.py` — BFS with visited set; returns depth + path per affected symbol
- `scorer.py` — 5-factor risk score; risk levels; confidence calculation
- `orchestrator.analyze(diff, project_path)` — returns a complete `ImpactReport`
- Unit tests: ≥ 15 tests passing (BFS correctness, risk boundaries, diff parsing)

#### Validation Checklist

- [ ] `diff_parser` correctly classifies SIGNATURE_CHANGE vs BODY_CHANGE vs DOCSTRING_CHANGE
- [ ] BFS on demo graph starting from `validate()` reaches ≥ 2 callers at depth 1
- [ ] Circular dependency in graph does NOT cause infinite loop (test with a synthetic cycle)
- [ ] DOCSTRING_CHANGE produces risk score < 0.2 for any symbol
- [ ] SIGNATURE_CHANGE on high-fan-in function produces risk score ≥ 0.8 (CRITICAL)
- [ ] `orchestrator.analyze()` returns a valid `ImpactReport` with all fields populated
- [ ] `pytest tests/test_propagator.py tests/test_scorer.py tests/test_diff_parser.py` all green

#### Fallback Plan

If diff → symbol mapping (line range → AST node) is complex to implement: **treat the entire file as the unit of change**. All symbols in a changed file become "changed symbols." This is slightly less precise but still functionally correct for the demo scenario. The difference is negligible for the judges.

---

### Phase 3: LLM Integration
**Duration:** 2 hours (H+10:00 → H+12:00)  
**Goal:** LLM explanation engine that generates natural-language impact summaries from structured analysis data.  
**Branch:** `feature/phase-3-llm`

#### Tasks

| # | Task | Module | Priority |
|---|---|---|---|
| 3.1 | Implement `models/report.py` | `ImpactReport`, `LLMExplanation` Pydantic models | P0 |
| 3.2 | Implement `core/llm/prompt_builder.py` | Build structured prompt from `ImpactReport` data (no raw source code!) | P0 |
| 3.3 | Implement `core/llm/client.py` | `async call_openai(prompt) -> str`; error handling; timeout = 30s | P0 |
| 3.4 | Implement `core/llm/explainer.py` | Orchestrate prompt build → API call → response parse → `LLMExplanation` | P0 |
| 3.5 | Implement graceful degradation | If `OPENAI_API_KEY` not set or API fails: return `None`; report continues without explanation | P0 |
| 3.6 | Pre-cache demo explanation | Call API once against the full demo scenario; save JSON response to `demo_cache/` | P0 |
| 3.7 | Implement `DEMO_MODE` env var | If `DEMO_MODE=1`: load explanation from `demo_cache/` instead of calling API | P0 |
| 3.8 | Wire into `orchestrator.analyze()` | Add `LLMExplainer` as final step; conditionally call based on `--no-llm` flag | P0 |

#### Key Implementation Notes

**`prompt_builder.py` — The Prompt (from PRD §13.1 Step 5):**
```python
SYSTEM_PROMPT = """You are a senior software architect analyzing Python code change impact.
You will receive structured analysis data. Only reference symbols explicitly provided.
Be precise, actionable, and use technical language suitable for senior engineers.
Return valid JSON only, no markdown, no extra text."""

def build_prompt(report: ImpactReport) -> str:
    # Include ONLY: symbol names, signatures, risk scores, propagation paths
    # NEVER include: raw source code, file contents, secrets
    top_affected = sorted(report.affected_symbols, 
                          key=lambda s: s.risk_score, reverse=True)[:10]
    return f"""
CHANGED SYMBOLS:
{format_changed_symbols(report.changed_symbols)}

TOP AFFECTED SYMBOLS (by risk):
{format_affected_symbols(top_affected)}

OVERALL RISK: {report.overall_risk.value} ({report.overall_risk.level}) 
CONFIDENCE: {report.overall_risk.confidence}

Generate a JSON response with EXACTLY this schema:
{{
  "summary": "<2-sentence change summary>",
  "blast_radius": "<3-sentence blast radius description>",
  "top_risks": [
    {{"symbol": "<id>", "reason": "<one line>"}},
    ...  (top 3 only)
  ],
  "recommended_actions": ["<action 1>", "<action 2>", "<action 3>"]
}}
"""
```

**Error Handling Contract:**
```python
class LLMExplainer:
    async def explain(self, report) -> Optional[LLMExplanation]:
        if not settings.OPENAI_API_KEY:
            return None  # ← Silent; caller handles None
        try:
            response = await self.client.call(prompt)
            return LLMExplanation.model_validate_json(response)
        except (APIError, ValidationError, TimeoutError):
            logger.warning("LLM explanation failed; continuing without")
            return None  # ← Never crashes the pipeline
```

#### Deliverables

- `prompt_builder.py` — generates a well-structured, grounded prompt
- `client.py` — async OpenAI client with retry logic and 30s timeout
- `explainer.py` — full explanation pipeline with graceful degradation
- `demo_cache/explanation_demo.json` — pre-computed explanation for the canonical demo scenario
- `DEMO_MODE` environment variable working

#### Validation Checklist

- [ ] `explain()` returns a valid `LLMExplanation` when API is available
- [ ] `explain()` returns `None` when `OPENAI_API_KEY` is not set (no crash)
- [ ] Prompt does NOT include any raw source code
- [ ] `DEMO_MODE=1 impact-tracer analyze ...` loads from cache (no API call)
- [ ] `impact-tracer analyze --no-llm ...` runs 100% offline
- [ ] JSON response is validated against `LLMExplanation` schema before use

#### Fallback Plan

If OpenAI API is inaccessible: the entire Phase 3 output is pre-cached in `demo_cache/`. Set `DEMO_MODE=1` and all demos work. The judges will never know the API is not being called live. For post-demo, the Ollama integration can be added. No blocking dependency.

---

### Phase 4: UI & Visualization
**Duration:** 5 hours (H+12:00 → H+17:00)  
**Goal:** A compelling, judge-facing interface — NL CLI REPL (opencode-style), rich terminal output, an interactive HTML graph, and a wired MCP server.  
**Branch:** `feature/phase-4-ui`

#### Tasks

##### Sub-Phase 4a: CLI Output (H+12:00 → H+13:30) — P0

| # | Task | Module |
|---|---|---|
| 4.1 | Implement `output/cli_reporter.py` | Use `rich.table`, `rich.panel`, `rich.progress` to render the impact report |
| 4.2 | Implement color-coded risk display | CRITICAL=red, HIGH=yellow, MEDIUM=blue, LOW=green using `rich.style` |
| 4.3 | Implement propagation path display | Show chain as `A → B → C` under each affected symbol |
| 4.4 | Implement LLM explanation panel | Render in a `rich.Panel` below the impact table |
| 4.5 | Implement `output/json_reporter.py` | `report.model_dump_json(indent=2)` |
| 4.6 | Implement `cli/session.py` | Pydantic session model: `{current_project, last_diff, last_report}`; enables follow-up queries |
| 4.7 | Implement `cli/intent_parser.py` | GPT-4o function calling; maps NL query → `{operation, args}`; covers 7 demo query patterns |
| 4.8 | Implement `cli/repl.py` | `prompt_toolkit` REPL loop; reads session context; dispatches to orchestrator; renders with `rich` |
| 4.9 | Implement `cli/main.py` entry point | Detects single-shot mode (arg present) vs REPL; `--format json` flag; `--project` flag |

**Target CLI Output (reference PRD §15.1):**
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  IMPACT TRACER  v0.1.0
  Project: ./demo/payments_service
  Overall Risk: CRITICAL (0.87) | Confidence: HIGH
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CHANGED (1):  payments.validator.BasePaymentValidator.validate  SIGNATURE_CHANGE
─────────────────────────────────────────────────
AFFECTED (14 symbols):
  CRITICAL  payments.api.routes.process_payment    0.92  depth:1
            └─ calls validate() directly │ 0 tests
  CRITICAL  payments.api.routes.refund_payment     0.88  depth:1
  HIGH      payments.workers.settlement_worker     0.74  depth:2
                ...
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  LLM EXPLANATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  [summary, blast radius, top risks, actions]
```

##### Sub-Phase 4b: Graph Visualization (H+13:30 → H+15:00) — P0/P1

| # | Task | Module |
|---|---|---|
| 4.7 | Implement `output/graph_visualizer.py` | Use `pyvis.network.Network` to generate `graph.html` from `DependencyGraph` |
| 4.8 | Apply risk-based color coding | Blue=unchanged, Orange=changed, Red=critical, Yellow=high, Green=low |
| 4.9 | Apply node sizing | `node_size = 10 + (fan_in * 3)` — high-fan-in nodes are visually prominent |
| 4.10 | Wire `impact-tracer graph` CLI command | Single-shot NL: `impact-tracer "show me the graph for payments/"` → `graph_visualizer.py` |
| 4.11 | Test graph output | Open `graph.html` in browser; verify interactive force-directed layout |

##### Sub-Phase 4c: MCP Server Wiring (H+15:00 → H+17:00) — P1

| # | Task | Module |
|---|---|---|
| 4.12 | Implement `mcp/tool_handlers.py` | Wire 4 MCP tools (`analyze_change`, `get_impact_report`, `query_dependency_graph`, `get_risk_score`) to orchestrator |
| 4.13 | Implement `mcp/server.py` main loop | stdio transport; `impact-tracer-mcp` script entry; verify tool registration |
| 4.14 | Test MCP with Claude Desktop | Register in `claude_desktop_config.json`; call each tool; verify responses match expected schema |
| 4.15 | End-to-end NL REPL test | Run 7 demo query patterns in REPL; verify intent parsing success rate ≥ 85% |
| 4.16 | Polish REPL UX | Input prompt styling; spinner during analysis; session context display; error message formatting |

#### Deliverables

- `cli_reporter.py` — rich, color-coded, judge-ready CLI output
- `graph_visualizer.py` — produces interactive `graph.html`
- NL CLI: `impact-tracer "what breaks if I change validate()"` runs end-to-end
- NL CLI REPL: multi-turn session context working (follow-up queries)
- `impact-tracer-mcp` starts, registers all 4 tools, callable from Claude Desktop
- `--format json` flag produces `ImpactReport` JSON on stdout

#### Validation Checklist

- [ ] CLI output matches target format; all risk colors display correctly
- [ ] `graph.html` opens in browser; nodes are interactive (hover for details)
- [ ] Risk colors are applied correctly: changed nodes are orange, critical are red
- [ ] NL query `"what breaks if I change validate() in payments/"` runs end-to-end
- [ ] Intent parser correctly parses all 7 demo query patterns
- [ ] REPL follow-up query (referring to `last_report`) works within same session
- [ ] MCP server: all 4 tools callable from Claude Desktop
- [ ] `--format json` output passes `jq .` validation

#### Fallback Plan

If MCP server is not complete by H+17:00: skip MCP wiring. The demo will use:
1. NL CLI REPL (P0 — must work)
2. Single-shot mode with `--format json` for CI/CD story
3. Static `graph.html` opened directly in the browser

This is still a highly compelling demo. Do not sacrifice NL CLI quality for MCP.

---

### Phase 5: Testing & Stabilization
**Duration:** 4 hours (H+17:00 → H+21:00)  
**Goal:** A reliable, crash-resistant system that handles edge cases gracefully and passes a defined test suite.  
**Branch:** `feature/phase-5-stabilization` (merge then work on `develop`)

**RULE: No new features in this phase. Bug fixes and stability only.**

#### Tasks

| # | Task | Priority |
|---|---|---|
| 5.1 | Run full end-to-end test with demo diff | Identify all crashes, incorrect outputs, display issues | P0 |
| 5.2 | Test edge cases: empty diff, no-change diff, docstring-only diff | Verify LOW risk, no crashes | P0 |
| 5.3 | Test edge cases: circular imports in demo project | Verify no infinite loop | P0 |
| 5.4 | Test edge cases: file with syntax error in demo project | Verify graceful skip | P0 |
| 5.5 | Test `--no-llm` flag | Verify report generates without LLM call | P0 |
| 5.6 | Test `DEMO_MODE=1` | Verify cached explanation loads | P0 |
| 5.7 | Write integration test: full pipeline | `tests/test_integration.py` — end-to-end with demo project | P0 |
| 5.8 | Write edge case tests | `tests/test_edge_cases.py` — empty diff, syntax error file, cycle | P0 |
| 5.9 | Fix all P0 bugs found in 5.1–5.8 | Bug fixes only | P0 |
| 5.10 | Generate `requirements.txt` fallback | `poetry export -f requirements.txt --output requirements.txt` | P0 |
| 5.11 | Write `README.md` | Installation, quick start, demo command | P0 |
| 5.12 | Write `DEMO.md` | Step-by-step demo script for team reference during presentation | P0 |
| 5.13 | Create Dockerfile (if time) | `docker build -t impact-tracer .` | P2 |
| 5.14 | Run `pytest --cov` | Target: ≥ 70% coverage on `core/` modules | P1 |

#### Test Matrix

| Test Category | File | Scenarios |
|---|---|---|
| Unit: AST Parser | `test_ast_parser.py` | simple func, class method, nested func, decorator, syntax error file |
| Unit: Import Resolver | `test_import_resolver.py` | absolute import, relative import, `from...import`, alias |
| Unit: Graph Builder | `test_graph_builder.py` | 3-module fixture, circular dep, orphan node |
| Unit: Diff Parser | `test_diff_parser.py` | signature change, body change, docstring change, addition, deletion |
| Unit: Propagator | `test_propagator.py` | direct dep, transitive dep (depth 2+), cycle, empty graph |
| Unit: Scorer | `test_scorer.py` | docstring → score < 0.2, signature + high fan-in → score ≥ 0.8 |
| Unit: LLM Client | `test_llm_explainer.py` | no API key → None, timeout → None, valid → LLMExplanation |
| Integration | `test_integration.py` | Full pipeline: demo project + demo diff → ImpactReport |
| Edge Cases | `test_edge_cases.py` | empty diff, no Python files, syntax error project |

#### Deliverables

- All P0 unit tests passing
- Integration test passing with demo project
- `requirements.txt` generated and verified
- `README.md` complete with installation and demo instructions
- `DEMO.md` with step-by-step judge demo script
- No unhandled exceptions on any of the test scenarios above
- `pytest --cov=impact_tracer` run and coverage report saved

#### Validation Checklist

- [ ] `pytest tests/` exits 0 (all tests green)
- [ ] `pytest --cov=impact_tracer/core` shows ≥ 70% coverage
- [ ] End-to-end demo run completes in < 15 seconds
- [ ] Docstring-only diff produces "LOW" risk (not CRITICAL or HIGH)
- [ ] Syntax-error file in project causes a warning log, not a crash
- [ ] `pip install -r requirements.txt && impact-tracer --help` works
- [ ] `DEMO.md` rehearsed at least once end-to-end
- [ ] `graph.html` opens cleanly in Chrome and Firefox

#### Fallback Plan

If test coverage is below 70%: drop the coverage requirement. Ensure the demo integration test and edge-case tests pass. Coverage is not visible to judges — reliability is. If bugs are found that take > 30 minutes each: skip and document in `KNOWN_ISSUES.md`. A documented known issue is more professional than a crash.

---

### Phase 6: Demo & Pitch
**Duration:** 3 hours (H+21:00 → H+24:00)  
**Goal:** A polished, rehearsed, confidence-inspiring demo that wins the judges.  
**Branch:** Merge all to `main`; tag `v0.1.0`.

#### Tasks

| # | Task |
|---|---|
| 6.1 | Final merge to `main`; create `git tag v0.1.0` |
| 6.2 | Full demo rehearsal #1 — timed (target: 4 minutes) |
| 6.3 | Identify rough spots; fix or note fallback for each |
| 6.4 | Full demo rehearsal #2 — simulate judge questions |
| 6.5 | Prepare "what if it crashes" response (Section 10) |
| 6.6 | Ensure backup screenshots/screen recording of demo exists |
| 6.7 | Prepare 3-slide context: Problem → Solution → Live Demo |
| 6.8 | Test on the presentation computer (not dev machine) |
| 6.9 | Submit repository with `README.md`, `DEMO.md`, and `demo/` directory |

#### Demo Sequence (from PRD Appendix E, expanded)

| Step | Duration | What you show | Talking points |
|---|---|---|---|
| 0. Context | 30s | Show the demo FastAPI payments project in VS Code | "This is a 15-module Python payments service. Someone just changed a core validator." |
| 1. Graph first | 30s | Open `graph.html` in browser; zoom in on `validator.py` node | "Here's the full dependency graph. Every arrow is a real import or call relationship." |
| 2. Trivial NL query | 45s | REPL: `does changing the validate() docstring break anything?` | "Docstring change. Result: LOW risk. Confidence: HIGH. Zero false alarms." |
| 3. Risky NL query | 90s | REPL: `what breaks if I change the validate() signature in payments/validator.py?` | Walk through CRITICAL output, propagation paths, LLM explanation |
| 4. Follow-up query | 30s | REPL: `which of those are deployed to production?` | "Multi-turn session context. It remembers the last report." |
| 5. MCP demo | 30s | Switch to Claude Desktop; call `analyze_change` tool with the same change | "Any AI agent can call this as a native tool. Zero glue code." |
| 6. The "so what" | 25s | Show `DEMO.md` GitHub Actions YAML | "This runs in CI. Every PR. No configuration beyond an API key." |

**Total: ~4 minutes**

---

## 7. Hour-by-Hour Timeline

| Hour | UTC Range | Phase | Key Deliverable by End |
|---|---|---|---|
| H01 | 00:00–01:00 | Phase 0 | Repo scaffolded; deps installed; demo project selected |
| H02 | 01:00–02:00 | Phase 1 | `ast_parser.py` reading functions, classes, imports |
| H03 | 02:00–03:00 | Phase 1 | `import_resolver.py` resolving intra-project imports |
| H04 | 03:00–04:00 | Phase 1 | `call_graph_builder.py` emitting caller→callee edges |
| H05 | 04:00–05:00 | Phase 1 | `graph_builder.py` producing NetworkX graph from demo project |
| H06 | 05:00–06:00 | Phase 1 | `graph_query.py` + unit tests passing; Phase 1 branch merged |
| H07 | 06:00–07:00 | Phase 2 | `diff_parser.py` + change type classification working |
| H08 | 07:00–08:00 | Phase 2 | Diff → symbol mapper; `ChangedSymbol[]` extraction |
| H09 | 08:00–09:00 | Phase 2 | `propagator.py` BFS working; `AffectedSymbol[]` with depth + path |
| H10 | 09:00–10:00 | Phase 2 | `scorer.py` + `orchestrator.analyze()` end-to-end; Phase 2 merged |
| H11 | 10:00–11:00 | Phase 3 | `prompt_builder.py` + `client.py` working |
| H12 | 11:00–12:00 | Phase 3 | `explainer.py` + demo cache + graceful degradation; Phase 3 merged |
| H13 | 12:00–13:00 | Phase 4a | `cli_reporter.py` with Rich formatting |
| H14 | 13:00–14:00 | Phase 4a | Full CLI output polished; `--format json` working |
| H15 | 14:00–15:00 | Phase 4b | `graph_visualizer.py` + NL CLI graph query working |
| H16 | 15:00–16:00 | Phase 4c | `mcp/tool_handlers.py` + `mcp/server.py` wired; all 4 tools callable |
| H17 | 16:00–17:00 | Phase 4c | NL CLI REPL session context + intent_parser polished; Phase 4 merged |
| H18 | 17:00–18:00 | Phase 5 | Full end-to-end run; bug fixes; edge case identification |
| H19 | 18:00–19:00 | Phase 5 | Test suite written and passing; README.md drafted |
| H20 | 19:00–20:00 | Phase 5 | DEMO.md drafted; `requirements.txt` generated; all P0 bugs fixed |
| H21 | 20:00–21:00 | Phase 5 | Final regression run; `pytest` green; Phase 5 merged |
| H22 | 21:00–22:00 | Phase 6 | `v0.1.0` tagged; Demo rehearsal #1 |
| H23 | 22:00–23:00 | Phase 6 | Demo rehearsal #2; fix rough spots; backup recording |
| H24 | 23:00–24:00 | Phase 6 | Final submission; repository public; submission form completed |

---

## 8. Git Branching Strategy

### 8.1 Branch Model

```
main          ← Production-ready; only receives merges from develop
develop       ← Integration branch; all feature branches merge here first
  │
  ├── feature/phase-0-setup
  ├── feature/phase-1-core-parsing
  ├── feature/phase-2-impact-engine
  ├── feature/phase-3-llm
  ├── feature/phase-4-ui
  ├── feature/phase-5-stabilization
  └── hotfix/[description]    ← Emergency bug fix; merges to develop + main
```

### 8.2 Commit Convention

Every commit follows: `<type>(<scope>): <message>`

| Type | Scope | Example |
|---|---|---|
| `feat` | Core module name | `feat(parser): add import resolver for relative imports` |
| `fix` | Bug scope | `fix(propagator): prevent infinite loop on circular deps` |
| `test` | Module | `test(scorer): add boundary tests for CRITICAL threshold` |
| `refactor` | Module | `refactor(graph_builder): extract edge weight computation` |
| `docs` | File | `docs(README): add quick-start demo instructions` |
| `chore` | Infra | `chore(deps): add pyvis to pyproject.toml` |

### 8.3 Merge Rules

| Rule | Detail |
|---|---|
| **Merge only green code** | Never merge a feature branch if `pytest` fails on it |
| **Merge to `develop` first** | Direct merges to `main` are forbidden during development |
| **Tag on milestones** | `git tag phase-N-complete` at end of each phase |
| **Squash within a phase** | Squash minor WIP commits before merging; keep commit history clean |
| **Emergency hotfix** | Branch `hotfix/` from `develop`; merge to both `develop` and `main` |

### 8.4 Tag Strategy

```
git tag phase-0-complete    # After Phase 0 validation passes
git tag phase-1-complete    # After Phase 1 validation passes
...
git tag v0.1.0-rc1          # After Phase 5
git tag v0.1.0              # Final submission tag — what judges evaluate
```

---

## 9. Demo Preparation Guide

### 9.1 Pre-Demo Setup Checklist (30 minutes before presentation)

- [ ] `git checkout main && git pull`
- [ ] `poetry install` (or `pip install -r requirements.txt`) — fresh environment  
- [ ] `cp .env.example .env` → set `OPENAI_API_KEY` and `DEMO_MODE=1`
- [ ] Pre-generate the graph: `impact-tracer graph --project demo/ --output demo_graph.html`
- [ ] Open `demo_graph.html` in browser — verify it loads
- [ ] Run trivial NL query: `impact-tracer "does changing the docstring for validate() break anything?"`
- [ ] Confirm output shows LOW risk
- [ ] Run the risky NL query: `impact-tracer "what breaks if I change the signature of validate() in payments/validator.py?"`
- [ ] Confirm CRITICAL output with propagation tree and LLM explanation (from cache)
- [ ] Start REPL: `impact-tracer` → enter multi-turn session; run follow-up query
- [ ] Start MCP server: `impact-tracer-mcp`
- [ ] Connect Claude Desktop; call `analyze_change` tool with demo diff; verify response
- [ ] Export graph: NL query `"show me the dependency graph for payments/"` → `graph.html` opens in browser
- [ ] All checks pass → ready to present

### 9.2 The Two Demo Diffs

Prepare **two specific, crafted diff files** committed to `demo/` directory:

**`demo/trivial.diff`** — A docstring-only change:
```diff
--- a/demo/payments_service/payments/utils.py
+++ b/demo/payments_service/payments/utils.py
@@ -15,6 +15,7 @@ class PaymentUtils:
     def format_amount(self, value: float) -> str:
-        """Format a payment amount."""
+        """Format a payment amount as a currency string."""
         return f"${value:.2f}"
```
*Expected result: LOW risk, < 5 affected symbols.*

**`demo/signature_change.diff`** — A signature change on a high-fan-in method:
```diff
--- a/demo/payments_service/payments/validator.py
+++ b/demo/payments_service/payments/validator.py
@@ -42,7 +42,7 @@ class BasePaymentValidator:
-    def validate(self, payment_data: dict) -> bool:
+    def validate(self, payment_data: dict, strict: bool = False) -> ValidationResult:
         """Validate payment data."""
```
*Expected result: CRITICAL risk, ≥ 10 affected symbols, LLM explanation showing API endpoints at risk.*

### 9.3 Judge Q&A Preparation

| Question | Prepared Answer |
|---|---|
| "How do you handle dynamic imports?" | "Python's dynamic dispatch is a known limitation. We apply a confidence penalty when import resolution is incomplete, and surface that to the user. The PRD documents this as Constraint C3. It's a feature, not a bug — honesty about confidence is core to the product." |
| "What's the accuracy of the call graph?" | "We achieve ≥ 95% accuracy on standard Python patterns. AST-based static analysis misses `getattr` calls and metaclass magic, which represent < 5% of typical production Python. Our confidence score accounts for this rate." |
| "How does this differ from existing tools?" | "Coverage tools are backward-looking; they tell you what was tested. We are forward-looking — we predict what will be affected before tests run. No existing open-source tool combines graph traversal, risk scoring, and LLM explanation in a single pipeline." |
| "How would this scale to a 500K LOC monorepo?" | "Graph build is O(N·E) and completes in < 60 seconds for 50K LOC per our benchmarks. For larger codebases, incremental analysis (cache the graph, re-analyze only changed files) reduces latency to < 3 seconds. The PRD roadmap adds Neo4j as the graph backend for production scale." |
| "Can it give false negatives?" | "Yes, for dynamic dispatch patterns. We are honest about this and quantify it via the confidence score. A LOW confidence CRITICAL is treated differently than a HIGH confidence CRITICAL — both are surfaced to the user." |

---

## 10. Backup & Contingency Plans

### 10.1 "It Won't Start" Contingency

If the demo code fails to start on the presentation machine:

1. **Backup #1:** Video recording of a successful demo run (record during Phase 6 rehearsal; save as `backup_demo.mp4`)
2. **Backup #2:** Screenshots of each demo step in a slide deck (`backup_demo_slides.pptx`)
3. **Backup #3:** Run from the developer's machine, screen-shared remotely

### 10.2 Component Failure Fallbacks

| Component Down | Fallback |
|---|---|
| OpenAI API | `DEMO_MODE=1` → load from cache; never show error to judges |
| MCP server not connecting | Demo with NL CLI only; graph via static `graph.html` in browser |
| Browser won't open graph.html | Screenshot of the graph in `demo_screenshots/graph.png` |
| Pyvis graph is unreadable | Show NetworkX graph as text adjacency list: `impact-tracer graph --format adjacency` |
| Poetry install fails | `pip install -r requirements.txt` fallback |
| Python version mismatch | Include a `python3.11` check in `check_env.sh`; ship with Dockerized fallback |

### 10.3 "We Ran Out of Time" Phase Fallbacks

| Phase Incomplete | Demo-Safe Fallback |
|---|---|
| Phase 3 (LLM) incomplete | Demo with `--no-llm`; explain LLM integration in slides; show the prompt design |
| Phase 4c (MCP server) incomplete | Demo with NL CLI only; explain MCP integration design verbally or from `plan-mcpIntegration.prompt.md` |
| Phase 4b (Graph viz) incomplete | Print adjacency list; sketch the graph on whiteboard |
| Phase 2 scorer not calibrated | Demo with known-correct risk outputs from cached `ImpactReport` JSON |
| Phase 1 call graph incomplete | Use import-only graph; mark "call graph in demo video" as stretch goal |

### 10.4 Fallback Demo Narrative

If only the NL CLI works:
> *"What you're seeing is the core intelligence engine — AST parsing, graph traversal, risk scoring, and GPT-4o intent parsing, all in one conversational terminal. You just ask it in plain English. The MCP server surfaces the same engine as an agent tool; the `--format json` flag makes it scriptable for CI/CD. The intelligence is the same regardless of which surface you use."*

This reframes a limitation as a design decision.

---

## 11. Final Submission Checklist

### 11.1 Code Quality Gate

- [ ] `git tag v0.1.0` exists on the submission commit
- [ ] `pytest tests/` exits 0 on a clean `poetry install`
- [ ] `impact-tracer --help` works after install
- [ ] `impact-tracer analyze --diff demo/signature_change.diff --project demo/` produces CRITICAL output
- [ ] No hardcoded secrets anywhere in the codebase (`git grep "sk-"` returns empty)
- [ ] `OPENAI_API_KEY` is loaded from `.env` / environment, never committed

### 11.2 Repository Structure Gate

- [ ] `README.md` — project description, installation, demo command
- [ ] `DEMO.md` — judge-facing demo script
- [ ] `demo/` — demo project + both diff files + cached LLM response
- [ ] `demo_screenshots/` — at least 3 screenshots of working demo
- [ ] `.env.example` — all environment variables documented
- [ ] `pyproject.toml` — complete, pinned dependencies
- [ ] `requirements.txt` — generated from `poetry export`
- [ ] `risk_weights.yaml` — present with default values
- [ ] `tests/` — unit + integration tests

### 11.3 Demo Readiness Gate

- [ ] `backup_demo.mp4` or `backup_demo_slides.pptx` prepared
- [ ] Both demo diffs (`trivial.diff`, `signature_change.diff`) committed
- [ ] Demo pre-run checklist (Section 9.1) completed on presentation machine
- [ ] Team has rehearsed the 4-minute demo at least twice
- [ ] Q&A answers from Section 9.3 reviewed by all presenters

### 11.4 Submission Form Items

- [ ] Repository URL (public GitHub)
- [ ] Demo video link (YouTube unlisted or direct file upload)
- [ ] Project description (use Executive Summary from PRD §1)
- [ ] Tech stack listed (Section 3 of this plan)
- [ ] Team member names and roles

---

## Appendix A: Directory Structure Reference

```
impact_tracer/
├── cli/
│   ├── __init__.py
│   ├── main.py                  # Entry point: REPL loop + single-shot mode
│   ├── repl.py                  # Interactive REPL (prompt_toolkit)
│   ├── intent_parser.py         # GPT-4o function calling → operation mapper
│   └── session.py               # Session context (current_project, last_report)
├── core/
│   ├── orchestrator.py          # Coordinates all engines
│   ├── analyzer/
│   │   └── python/
│   │       ├── ast_parser.py
│   │       ├── import_resolver.py
│   │       └── call_graph_builder.py
│   ├── infra/                   # Infrastructure config parsers (P1)
│   │   ├── __init__.py
│   │   ├── base.py              # InfraParser ABC
│   │   ├── docker_compose.py    # pyyaml-based parser
│   │   ├── kubernetes.py        # pyyaml-based parser
│   │   └── terraform.py         # python-hcl2-based parser
│   ├── runtime/                 # Runtime trace/log miners (P1)
│   │   ├── __init__.py
│   │   ├── base.py              # RuntimeMiner ABC
│   │   ├── otel_parser.py       # OTEL JSON trace aggregation (pandas)
│   │   ├── nginx_parser.py      # Nginx/Envoy access log parser
│   │   └── postgres_parser.py   # Postgres slow query log parser
│   ├── graph/
│   │   ├── graph_builder.py     # Merges AST + infra + runtime → UnifiedGraph
│   │   ├── graph_store.py
│   │   └── graph_query.py
│   ├── diff/
│   │   └── diff_parser.py
│   ├── propagation/
│   │   └── propagator.py
│   ├── risk/
│   │   ├── scorer.py
│   │   └── config.py
│   └── llm/
│       ├── client.py
│       ├── prompt_builder.py
│       └── explainer.py
├── output/
│   ├── cli_reporter.py
│   ├── json_reporter.py
│   ├── markdown_reporter.py
│   └── graph_visualizer.py
├── models/
│   ├── symbol.py          # CodeNode, Symbol, AffectedSymbol
│   ├── infra.py           # ServiceNode, InfraNode, NetworkNode, TableNode
│   ├── runtime.py         # RuntimeEdge, DataAccessEdge
│   ├── graph.py           # UnifiedDependencyGraph
│   ├── diff.py
│   ├── impact.py
│   └── report.py
├── config/
│   ├── settings.py
│   └── risk_weights.yaml
└── tests/
    ├── conftest.py
    ├── test_ast_parser.py
    ├── test_import_resolver.py
    ├── test_graph_builder.py
    ├── test_diff_parser.py
    ├── test_propagator.py
    ├── test_scorer.py
    ├── test_llm_explainer.py
    ├── test_docker_compose_parser.py
    ├── test_kubernetes_parser.py
    ├── test_terraform_parser.py
    ├── test_otel_parser.py
    ├── test_unified_graph.py
    ├── test_integration.py
    └── test_edge_cases.py

demo/
├── payments_service/            # Demo FastAPI project (15 modules)
├── trivial.diff                 # Docstring-only change → LOW risk
├── signature_change.diff        # Signature change → CRITICAL risk
└── demo_cache/
    └── explanation_demo.json    # Pre-cached LLM response

README.md
DEMO.md
KNOWN_ISSUES.md
.env.example
pyproject.toml
requirements.txt
```

---

## Appendix B: Critical Code Patterns — Quick Reference

These patterns are the most failure-prone. Every implementer must commit them to memory.

**BFS with cycle protection (the most critical pattern):**
```python
# ALWAYS use a visited set. NEVER skip this.
visited: Set[str] = set()
queue: deque = deque()
while queue:
    node = queue.popleft()
    if node in visited:
        continue          # ← This one line prevents infinite loops
    visited.add(node)
    # ... process node
```

**Graceful AST parse (never crash on user files):**
```python
try:
    tree = ast.parse(source_code)
except SyntaxError as e:
    logger.warning(f"Skipping {file_path}: SyntaxError at line {e.lineno}")
    self._stats.failed_files += 1
    return SymbolTable(file_path=file_path, symbols=[])  # ← Return empty, never raise
```

**LLM graceful degradation (never block the pipeline):**
```python
async def explain(self, report) -> Optional[LLMExplanation]:
    try:
        # ... call LLM
    except Exception:              # ← Catch ALL exceptions from LLM layer
        return None                # ← Never propagate; caller checks for None
```

---

*End of Impact Tracer Master Execution Plan v1.0.0*  
*This document governs all implementation decisions for the 24-hour hackathon window.*  
*Companion document: `PRD.prompt.md` — governs feature correctness and requirements.*
