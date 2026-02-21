# Final Rehearsal Checklist (Phase 6)

## Before starting
- Ensure presentation machine has repository clone and dependencies installed.
- Ensure .env setup is present (OPENAI_API_KEY optional; DEMO_MODE=1 recommended for reliability).
- Confirm required files are available:
  - README.md
  - DEMO.md
  - graph.html generation path writable

## Rehearsal flow (target: ~4 minutes)
1. Open graph context: run markdown flow and open graph.html.
2. Run trivial diff flow and call out LOW risk behavior.
3. Run signature-change diff flow and call out affected symbols + risk ranking.
4. Show markdown output and JSON output artifacts.
5. Mention MCP tool availability and crash fallback strategy.

## Reliability checks
- Run:
  - .venv\Scripts\python.exe -m pytest -q
- Generate demo artifacts:
  - .venv\Scripts\python.exe -m impact_tracer.cli.main --project demo/payments_service --diff-file demo/signature_change.diff --format markdown --output impact_report.md --graph-output graph.html --no-llm

## If something fails live
- Use no-LLM mode immediately.
- Use cached/demo fallback artifacts:
  - demo/backup/impact_report.md
  - demo/backup/impact_report.json
  - demo/backup/graph.html (or regenerated graph.html)
- Use CRASH_RESPONSE.md talk track.

## Final manual closeout
- Mark presentation-machine rehearsal done (Task 6.8).
- Complete final submission confirmation (Task 6.9).
