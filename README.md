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

Impact Tracer exposes 4 tools via the [Model Context Protocol](https://modelcontextprotocol.io/) (MCP),
letting code agents (Copilot, OpenCode, Claude, etc.) call them directly.

### Tools provided to agents

| # | Tool | Description |
|---|------|-------------|
| 1 | `analyze_change` | Analyze a unified diff against a project → overall risk, changed/affected symbol counts, `report_id` |
| 2 | `get_impact_report` | Retrieve the full report (symbols, propagation paths, LLM explanation) by `report_id` |
| 3 | `query_dependency_graph` | Graph summary (node/edge counts) or incoming/outgoing neighbors for a symbol |
| 4 | `get_risk_score` | Risk score (0-1), level (LOW/MEDIUM/HIGH/CRITICAL), propagation depth for one symbol |

### Run the MCP server

```powershell
impact-tracer-mcp
```

This runs the server over **stdio** (foreground process), which is what MCP clients expect.

### Connect in VS Code

A workspace config is already provided in `.vscode/mcp.json`.

1. Open Command Palette → **MCP: List Servers** → start **impactTracer**.
2. In Chat, enable tools from the **impactTracer** server in the tool picker.
3. Prompt example:

```text
Analyze the blast radius of renaming validate() to validate_payment() in validator.py. Use impactTracer.
```

If you need to set it up manually, add to `.vscode/mcp.json`:

```json
{
  "servers": {
    "impactTracer": {
      "type": "stdio",
      "command": "${workspaceFolder}/.venv/Scripts/impact-tracer-mcp",
      "envFile": "${workspaceFolder}/.env",
      "env": {
        "OPENAI_API_KEY": "${env:OPENAI_API_KEY}",
        "LOG_LEVEL": "INFO"
      }
    }
  }
}
```

> **Tip:** If tools don't appear, run **MCP: Reset Cached Tools**.

### Connect in OpenCode

A config is already provided in `opencode.json` (project root).

Verify and debug:

```bash
opencode mcp list
opencode mcp debug impact_tracer_mcp
```

Prompt example:

```text
What is the blast radius of changing the payment validation logic? Use impact_tracer_mcp.
```

Manual `opencode.json` if needed:

```json
{
  "$schema": "https://opencode.ai/config.json",
  "mcp": {
    "impact_tracer": {
      "type": "local",
      "command": ["./.venv/Scripts/python.exe", "-m", "impact_tracer.mcp.server"],
      "enabled": true,
      "timeout": 30000,
      "environment": {
        "OPENAI_API_KEY": "{env:OPENAI_API_KEY}",
        "LOG_LEVEL": "INFO"
      }
    },
    "impact_tracer_mcp": {
      "type": "local",
      "command": ["./.venv/Scripts/impact-tracer-mcp"],
      "enabled": true,
      "timeout": 30000,
      "environment": {
        "OPENAI_API_KEY": "{env:OPENAI_API_KEY}",
        "LOG_LEVEL": "INFO"
      }
    }
  }
}
```

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
