"""MCP server entry point stub."""

from __future__ import annotations

from impact_tracer.mcp.tool_handlers import analyze_change, get_impact_report, get_risk_score, query_dependency_graph

try:
    from mcp.server.fastmcp import FastMCP
except Exception:  # pragma: no cover - fallback path when SDK layout differs
    FastMCP = None


def _create_server() -> object | None:
    if FastMCP is None:
        return None

    server = FastMCP("impact-tracer")

    @server.tool()
    def analyze_change_tool(diff_text: str, project_path: str) -> dict[str, object]:
        return analyze_change(diff_text, project_path)

    @server.tool()
    def get_impact_report_tool(report_id: str) -> dict[str, object]:
        return get_impact_report(report_id)

    @server.tool()
    def query_dependency_graph_tool(project_path: str, symbol_id: str = "") -> dict[str, object]:
        return query_dependency_graph(project_path, symbol_id or None)

    @server.tool()
    def get_risk_score_tool(diff_text: str, project_path: str, symbol_id: str) -> dict[str, object]:
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
