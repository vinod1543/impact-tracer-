# Phase 6 — "What if it crashes?" Response

## 30-second response
"If a live command fails, we switch immediately to our validated fallback path: pre-generated demo artifacts and no-LLM deterministic runs. The core analysis pipeline remains available offline, and we can still demonstrate impact propagation, risk scoring, and outputs without external dependencies."

## Fallback ladder (in order)

1. **Retry with no external dependency:** run with `--no-llm`.
2. **Use cached explanation path:** set `DEMO_MODE=1`.
3. **Use pre-generated artifacts:** open `impact_report.md`, `impact_report.json`, `graph.html`.
4. **Show deterministic validation evidence:** `pytest -q` green baseline.

## Commands

```powershell
# Deterministic run (no LLM)
impact-tracer --project demo/payments_service --diff-file demo/signature_change.diff --format text --no-llm

# Cached explanation mode
$env:DEMO_MODE="1"
impact-tracer --project demo/payments_service --diff-file demo/signature_change.diff --format text

# Open fallback artifacts
# impact_report.md, impact_report.json, graph.html
```

## What we explicitly avoid in fallback

- No live network dependency is required for core analysis.
- No architectural changes during demo.
- No hidden manual patching in front of judges.
