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

    if any(token in normalized for token in ["show graph", "show me the graph", "dependency graph", "visualize", "graph"]):
        return {"operation": "show_graph", "query": query}

    risk_match = re.search(r"risk(?:\s+score)?\s+(?:for|of)\s+([\w\.:_\-/]+)", normalized)
    if risk_match:
        return {"operation": "get_risk_score", "symbol": risk_match.group(1), "query": query}

    if any(token in normalized for token in [
        "who depends on", "dependencies of", "query dependencies",
        "dependents", "what uses", "who calls", "callers of",
        "propagation", "blast radius",
    ]):
        return {"operation": "query_dependencies", "query": query}

    if any(token in normalized for token in [
        "show all", "expand", "expand report", "show full report",
        "show report", "full report", "last report", "show results",
    ]):
        return {"operation": "expand_last_report", "query": query}

    # Detect natural language change descriptions → generate diff via LLM
    # These are specific patterns where the user is DESCRIBING a change they want to make,
    # not asking about the impact of a diff file.
    nl_change_patterns = [
        r"^(?:i\s+)?want\s+to\s+(?:change|modify|update|rename|add|remove|delete|refactor)\b",
        r"^(?:can\s+i\s+safely)\s+(?:change|modify|update|rename|add|remove|delete|refactor)\b",
        r"^(?:is\s+it\s+safe\s+to)\s+(?:change|modify|update|rename|add|remove|delete|refactor)\b",
        r"^(?:impact\s+of\s+(?:changing|modifying|updating|renaming|adding|removing|deleting|refactoring))\b",
        r"^(?:if\s+i\s+)(?:change|modify|update|rename|add|remove|delete|refactor)\b",
    ]
    for pattern in nl_change_patterns:
        if re.search(pattern, normalized):
            return {"operation": "describe_change", "query": query}

    if any(token in normalized for token in ["what breaks", "impact", "change", "analyze"]):
        return {"operation": "analyze_diff", "query": query}

    return {"operation": "analyze_diff", "query": query}
