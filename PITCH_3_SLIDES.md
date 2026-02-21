# Phase 6 — 3-Slide Pitch Deck Script

## Slide 1 — Problem
**Title:** Small code changes cause hidden blast radius

- Engineers cannot reliably predict downstream breakage from shared utility changes.
- Manual tracing is slow, error-prone, and inconsistent across reviewers.
- AI coding tools need a safety layer before merge.

**Talk track (30s):**
"Impact Tracer answers one high-value question: if I change this code, what else might break? Instead of searching manually, we compute blast radius from a real dependency graph and give an actionable risk report before merge."

## Slide 2 — Solution
**Title:** AI-native impact analysis in terminal + MCP

- Natural-language CLI for single-shot and REPL usage.
- Unified impact pipeline: parse diff → map symbols → propagate graph impact → score risk → optional LLM explanation.
- Outputs for both humans and systems: Rich terminal, JSON, Markdown, interactive graph HTML.
- MCP tools allow agent-native integration (`analyze_change`, `get_impact_report`, `query_dependency_graph`, `get_risk_score`).

**Talk track (45s):**
"We built a layered Python system where every stage is typed and testable. The graph and propagation engine provide deterministic core intelligence; the LLM layer explains results but never blocks analysis."

## Slide 3 — Live Demo
**Title:** 4-minute reliable walkthrough

1. Show interactive `graph.html` for dependency context.
2. Run trivial change (`demo/trivial.diff`) → LOW risk.
3. Run signature change (`demo/signature_change.diff`) → higher risk with affected symbols.
4. Export Markdown + graph and JSON artifacts.
5. Mention MCP tool interoperability.

**Talk track (45s):**
"You’ll see low-noise behavior for trivial edits and high-signal risk for meaningful API changes. The same engine powers terminal use, CI JSON output, and agent tooling via MCP."

## Judge Q&A anchors

- **Accuracy:** deterministic parser + graph traversal + tested edge cases.
- **Reliability:** no-LLM mode + cached demo mode + graceful fallback.
- **Practicality:** works today as a pre-merge check in Python workflows.
