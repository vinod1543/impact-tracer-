"""Natural language intent parser stub."""

from __future__ import annotations

import re


def parse_intent(query: str) -> dict[str, str]:
    """Parse natural language query into operation payload.

    Args:
        query: User query text.

    Returns:
        dict[str, str]: Parsed operation payload.
    """
    normalized = query.strip().lower()

    if not normalized:
        return {"operation": "analyze_diff", "query": query}

    if any(token in normalized for token in ["show graph", "show me the graph", "dependency graph"]):
        return {"operation": "show_graph", "query": query}

    risk_match = re.search(r"risk score for\s+([\w\.:_\-/]+)", normalized)
    if risk_match:
        return {"operation": "get_risk_score", "symbol": risk_match.group(1), "query": query}

    if any(token in normalized for token in ["who depends on", "dependencies of", "query dependencies"]):
        return {"operation": "query_dependencies", "query": query}

    if normalized in {"show all", "expand", "expand report", "show full report"}:
        return {"operation": "expand_last_report", "query": query}

    if any(token in normalized for token in ["what breaks", "impact", "change", "analyze"]):
        return {"operation": "analyze_diff", "query": query}

    return {"operation": "analyze_diff", "query": query}
