# KNOWN_ISSUES.md

## KI-001: Poetry unavailable in current machine image

- Severity: Medium
- Impact: Cannot use `poetry` commands directly in this environment
- Workaround: Use `pip install -r requirements.txt`

## KI-002: MCP server startup depends on installed MCP SDK layout

- Severity: Medium
- Impact: If `mcp.server.fastmcp` import path is unavailable, server cannot start
- Workaround: Ensure `mcp[cli]` is installed and compatible with current code path

## KI-003: REPL expects diff input for analysis operations

- Severity: Low
- Impact: REPL analysis now intentionally fails fast when no diff source is provided
- Workaround: Provide `.diff` file path or unified diff text directly in REPL input

## KI-004: JSON + Markdown both supported by design

- Severity: Informational
- Impact: JSON output is retained for MVP compliance while Markdown is added for readability
- Workaround: Use `--format markdown` for narrative report or `--format json` for machine-readable output
