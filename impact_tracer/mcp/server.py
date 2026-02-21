"""MCP server entry point – exposes Impact Tracer tools via Model Context Protocol."""

from __future__ import annotations

from impact_tracer.mcp.tool_handlers import (
    analyze_change,
    analyze_git_change,
    get_impact_report,
    get_risk_score,
    query_dependency_graph,
)

try:
    from mcp.server.fastmcp import FastMCP
except Exception:  # pragma: no cover - fallback path when SDK layout differs
    FastMCP = None


def _create_server() -> object | None:
    if FastMCP is None:
        return None

    server = FastMCP("impact-tracer")

    @server.tool(
        name="analyze_change",
        description=(
            "Analyze a code change (unified diff) and return its blast radius. "
            "Returns overall risk score, risk level, count of changed and affected symbols, "
            "and a report_id that can be passed to get_impact_report for the full breakdown."
        ),
    )
    def analyze_change_tool(
        diff_text: str,
        project_path: str,
    ) -> dict[str, object]:
        """Analyze a unified diff against a Python project.

        Args:
            diff_text: The full unified diff text (output of `git diff`).
            project_path: Path to the project root (e.g. 'src/myapp').

        Returns:
            report_id, overall_risk, risk_score, changed_symbols count, affected_symbols count.
        """
        return analyze_change(diff_text, project_path)

    @server.tool(
        name="analyze_git_change",
        description=(
            "Analyze changes directly from git — no diff text needed. "
            "Automatically detects unstaged, staged, or branch changes. "
            "Set source to 'unstaged' (default), 'staged', or 'branch'. "
            "For branch mode, set base_branch (default 'main')."
        ),
    )
    def analyze_git_change_tool(
        project_path: str,
        source: str = "unstaged",
        base_branch: str = "main",
    ) -> dict[str, object]:
        """Analyze git changes without providing a diff.

        Args:
            project_path: Path to the git repository root.
            source: Change source — 'unstaged', 'staged', or 'branch'.
            base_branch: Base branch for comparison (only used when source='branch').

        Returns:
            report_id, overall_risk, risk_score, changed_symbols, affected_symbols, git_source.
        """
        return analyze_git_change(project_path, source, base_branch)

    @server.tool(
        name="get_impact_report",
        description=(
            "Retrieve the full impact report for a previously analyzed change. "
            "Includes every changed symbol, affected symbol with risk scores, "
            "propagation paths, and an optional LLM-generated explanation."
        ),
    )
    def get_impact_report_tool(report_id: str) -> dict[str, object]:
        """Fetch a stored impact report by its id.

        Args:
            report_id: The report identifier returned by analyze_change.

        Returns:
            Full serialized ImpactReport (changed_symbols, affected_symbols,
            propagation_paths, overall_risk, explanation).
        """
        return get_impact_report(report_id)

    @server.tool(
        name="query_dependency_graph",
        description=(
            "Query the static + infrastructure + runtime dependency graph for a project. "
            "Without a symbol_id returns node/edge counts. "
            "With a symbol_id returns its incoming and outgoing dependencies."
        ),
    )
    def query_dependency_graph_tool(
        project_path: str,
        symbol_id: str = "",
    ) -> dict[str, object]:
        """Query the unified dependency graph.

        Args:
            project_path: Project root path.
            symbol_id: Optional fully-qualified symbol id (e.g. 'module.Class.method').
                        Leave empty for a graph summary.

        Returns:
            Graph summary (node_count, edge_count) or symbol neighbors (incoming, outgoing).
        """
        return query_dependency_graph(project_path, symbol_id or None)

    @server.tool(
        name="get_risk_score",
        description=(
            "Compute the risk score for a single symbol given a code change. "
            "Returns the numeric risk score (0-1), risk level (LOW/MEDIUM/HIGH/CRITICAL), "
            "and propagation depth."
        ),
    )
    def get_risk_score_tool(
        diff_text: str,
        project_path: str,
        symbol_id: str,
    ) -> dict[str, object]:
        """Get risk score for one symbol from a fresh analysis.

        Args:
            diff_text: Unified diff text.
            project_path: Project root path.
            symbol_id: Fully-qualified symbol id to check (e.g. 'validator.PaymentRequestValidator.validate').

        Returns:
            symbol_id, risk_score, risk_level, depth.
        """
        return get_risk_score(diff_text, project_path, symbol_id)

    return server


def main() -> int:
    """Run MCP server entrypoint.

    Returns:
        int: Exit code.
    """
    server = _create_server()
    if server is None:
        print("MCP SDK not available; cannot start server in this environment.")
        return 1
    server.run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
