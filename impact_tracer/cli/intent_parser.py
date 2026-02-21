"""Natural language intent parser stub."""


def parse_intent(query: str) -> dict[str, str]:
    """Parse a natural language query into an operation payload.

    Args:
        query: User query text.

    Returns:
        dict[str, str]: Parsed intent payload.
    """
    return {"operation": "analyze", "query": query}
