# DEMO.md

This guide is for a stable, repeatable hackathon demo run.

## Demo Scenarios

## 1) Offline-safe run (`--no-llm`)

```powershell
impact-tracer --project demo/payments_service --diff-file demo/signature_change.diff --format text --no-llm
```

Expected:
- risk summary shown in terminal
- no LLM explanation section

## 2) Cached explanation run (`DEMO_MODE=1`)

```powershell
$env:DEMO_MODE="1"
impact-tracer --project demo/payments_service --diff-file demo/signature_change.diff --format text
```

Expected:
- explanation is loaded from `demo/demo_cache/explanation_demo.json`
- no dependency on live OpenAI response for demo reliability

## 3) Markdown + interactive graph export

```powershell
impact-tracer --project demo/payments_service --diff-file demo/signature_change.diff --format markdown --output impact_report.md --graph-output graph.html
```

Expected artifacts:
- `impact_report.md` (detailed simple-language report)
- `graph.html` (interactive graph)
- markdown contains Mermaid summary + graph link

## REPL demo

```powershell
impact-tracer --project demo/payments_service
```

Inside REPL:
- `show me the graph`
- `demo/signature_change.diff`
- `exit`

## Suggested 4-minute flow

1. Show command with `--no-llm` (safety baseline)
2. Show markdown export and open `impact_report.md`
3. Open `graph.html` and navigate nodes
4. Show cached mode (`DEMO_MODE=1`) for LLM-ready narrative

## Demo reset checklist

- Confirm `.venv` active
- Confirm tests pass (`pytest tests/ -q`)
- Remove stale outputs if needed:
  - `impact_report.md`
  - `graph.html`
- Set `DEMO_MODE=1` for reliability if internet/API uncertain
