"""PostgreSQL log parser.

Parses pg_stat_statements or slow-query-log exports to discover
table-level runtime dependencies and query patterns.
"""

from __future__ import annotations

import json
from pathlib import Path

from impact_tracer.models.runtime import (
    RuntimeEdge,
    RuntimeNode,
    RuntimeNodeType,
    RuntimeTraceGraph,
)

# Rough SQL → operation mapping
_SQL_OPS = {
    "SELECT": "READ",
    "INSERT": "WRITE",
    "UPDATE": "WRITE",
    "DELETE": "DELETE",
    "CREATE": "DDL",
    "ALTER": "DDL",
    "DROP": "DDL",
}


class PostgresLogParser:
    """Parse PostgreSQL query logs / pg_stat exports."""

    def parse(self, path: str) -> RuntimeTraceGraph:
        """Parse a JSON export of pg_stat_statements.

        Expected format::

            {
              "database": "payments_db",
              "queries": [
                {
                  "query": "SELECT * FROM payments WHERE id = $1",
                  "calls": 15000,
                  "mean_time_ms": 1.2,
                  "caller_service": "payments-api"
                }
              ]
            }

        Args:
            path: Path to pg_stat JSON export.

        Returns:
            RuntimeTraceGraph with table nodes and query edges.
        """
        file_path = Path(path)
        if not file_path.exists():
            return RuntimeTraceGraph()

        try:
            data = json.loads(file_path.read_text(encoding="utf-8"))
        except Exception:
            return RuntimeTraceGraph()

        nodes: dict[str, RuntimeNode] = {}
        edges: list[RuntimeEdge] = []

        db_name = data.get("database", "unknown_db")

        for entry in data.get("queries", []):
            query = entry.get("query", "")
            tables = self._extract_tables(query)
            caller = entry.get("caller_service", "unknown")
            calls = entry.get("calls", 1)
            latency = entry.get("mean_time_ms")
            operation = self._detect_operation(query)

            # Ensure caller node exists
            if caller not in nodes:
                nodes[caller] = RuntimeNode(
                    id=caller,
                    label=caller,
                    node_type=RuntimeNodeType.SERVICE,
                )

            for table in tables:
                table_id = f"{db_name}.{table}"
                if table_id not in nodes:
                    nodes[table_id] = RuntimeNode(
                        id=table_id,
                        label=table,
                        node_type=RuntimeNodeType.TABLE,
                        metadata={"database": db_name},
                    )

                edges.append(RuntimeEdge(
                    source=caller,
                    target=table_id,
                    edge_type=operation,
                    confidence=0.85,
                    call_count=calls,
                    latency_ms=latency,
                    metadata={"query_pattern": query[:120]},
                ))

        return RuntimeTraceGraph(
            nodes=list(nodes.values()),
            edges=edges,
        )

    def _extract_tables(self, query: str) -> list[str]:
        """Extract table names from SQL query (best-effort)."""
        import re
        tables: list[str] = []
        query_upper = query.upper()
        # FROM / JOIN
        for match in re.finditer(r'\b(?:FROM|JOIN)\s+([a-zA-Z_][a-zA-Z0-9_.]*)', query, re.IGNORECASE):
            tables.append(match.group(1).strip('"').strip("'"))
        # INSERT INTO
        for match in re.finditer(r'\bINTO\s+([a-zA-Z_][a-zA-Z0-9_.]*)', query, re.IGNORECASE):
            tables.append(match.group(1).strip('"').strip("'"))
        # UPDATE
        for match in re.finditer(r'\bUPDATE\s+([a-zA-Z_][a-zA-Z0-9_.]*)', query, re.IGNORECASE):
            tables.append(match.group(1).strip('"').strip("'"))
        return list(set(tables)) if tables else ["unknown_table"]

    def _detect_operation(self, query: str) -> str:
        """Detect SQL operation type."""
        first_word = query.strip().split()[0].upper() if query.strip() else "UNKNOWN"
        return _SQL_OPS.get(first_word, "QUERY")
