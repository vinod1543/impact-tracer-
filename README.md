# Impact Tracer

Impact Tracer is a Python-first impact analysis tool that helps answer:

> If I change this code, what else might break?

It analyzes a project + diff, builds dependency context, propagates impact, computes risk, and can generate:
- rich terminal report
- JSON report
- detailed Markdown report
- interactive graph HTML

## Current MVP Status

- Phase 0 to Phase 4 completed
- Test suite currently green
- CLI + REPL + MCP interfaces available

## Installation

### Recommended in this environment (Poetry fallback)

```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

### Optional Poetry flow

If Poetry is available:

```powershell
poetry install
```

## Quick Start (Single-shot)

### 1) JSON output

```powershell
impact-tracer --project demo/payments_service --diff-file demo/signature_change.diff --format json
```

### 2) Markdown output + interactive graph

```powershell
impact-tracer --project demo/payments_service --diff-file demo/signature_change.diff --format markdown --output impact_report.md --graph-output graph.html
```

### 3) Rich terminal output

```powershell
impact-tracer --project demo/payments_service --diff-file demo/signature_change.diff --format text
```

## REPL Mode

Launch REPL (no args):

```powershell
impact-tracer --project demo/payments_service
```

Inside REPL:
- `show me the graph` to export interactive graph
- pass a `.diff` file path (for example `demo/signature_change.diff`) to run analysis
- type `exit` to quit

## CLI Flags

- `--project`: target project path
- `--diff-file`: unified diff file path
- `--format`: `text | json | markdown`
- `--output`: output file path (json/markdown)
- `--graph-output`: graph HTML output path
- `--no-llm`: skip LLM explanation stage

## Environment Variables

From `.env.example`:

- `OPENAI_API_KEY`: optional (required only for live LLM calls)
- `LOG_LEVEL`: logging level
- `DEMO_MODE`: set `1` to use cached explanation from `demo/demo_cache/explanation_demo.json`

## MCP Server

Start MCP server:

```powershell
impact-tracer-mcp
```

Exposed tools:
- `analyze_change`
- `get_impact_report`
- `query_dependency_graph`
- `get_risk_score`

## Testing

Run full suite:

```powershell
pytest tests/ -q
```

## Branching & Milestones

Phase branches and tags are used for checkpoints:
- `feature/phase-<n>-...`
- `phase-<n>-complete`

## Notes

See `SCHEMA.md` for fixed data contracts and `EXECUTION_LOG.md` for execution history.
