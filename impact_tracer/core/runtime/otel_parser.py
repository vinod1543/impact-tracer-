"""OpenTelemetry / JSON trace parser.

Parses exported OpenTelemetry traces (simplified JSON format) into
RuntimeTraceGraph nodes and edges with call counts and latency.
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


class OtelTraceParser:
    """Parse OpenTelemetry / JSON runtime trace files."""

    def parse(self, path: str) -> RuntimeTraceGraph:
        """Parse a JSON traces file.

        Expected format::

            {
              "services": [
                {"name": "payments-api", "type": "SERVICE"},
                {"name": "postgres", "type": "TABLE"}
              ],
              "traces": [
                {
                  "source": "payments-api",
                  "target": "postgres",
                  "operation": "INSERT payments",
                  "call_count": 1520,
                  "avg_latency_ms": 4.2
                }
              ]
            }

        Args:
            path: Path to JSON traces file.

        Returns:
            RuntimeTraceGraph with nodes and edges.
        """
        file_path = Path(path)
        if not file_path.exists():
            return RuntimeTraceGraph()

        try:
            data = json.loads(file_path.read_text(encoding="utf-8"))
        except Exception:
            return RuntimeTraceGraph()

        nodes: list[RuntimeNode] = []
        edges: list[RuntimeEdge] = []

        # Parse service nodes
        for svc in data.get("services", []):
            node_type = self._map_type(svc.get("type", "SERVICE"))
            nodes.append(RuntimeNode(
                id=svc["name"],
                label=svc["name"],
                node_type=node_type,
                metadata=svc.get("metadata", {}),
            ))

        # Parse trace edges
        for trace in data.get("traces", []):
            edges.append(RuntimeEdge(
                source=trace["source"],
                target=trace["target"],
                edge_type=trace.get("operation", "RUNTIME_CALL"),
                confidence=trace.get("confidence", 0.9),
                call_count=trace.get("call_count"),
                latency_ms=trace.get("avg_latency_ms"),
                metadata={k: v for k, v in trace.items()
                          if k not in ("source", "target", "operation",
                                       "confidence", "call_count", "avg_latency_ms")},
            ))

        # Auto-create nodes for any referenced in edges but not declared
        known_ids = {n.id for n in nodes}
        for edge in edges:
            for node_id in (edge.source, edge.target):
                if node_id not in known_ids:
                    nodes.append(RuntimeNode(
                        id=node_id,
                        label=node_id,
                        node_type=RuntimeNodeType.SERVICE,
                    ))
                    known_ids.add(node_id)

        return RuntimeTraceGraph(nodes=nodes, edges=edges)

    def _map_type(self, type_str: str) -> RuntimeNodeType:
        """Map string type to RuntimeNodeType."""
        mapping = {
            "SERVICE": RuntimeNodeType.SERVICE,
            "ENDPOINT": RuntimeNodeType.ENDPOINT,
            "TABLE": RuntimeNodeType.TABLE,
            "DATABASE": RuntimeNodeType.TABLE,
            "QUEUE": RuntimeNodeType.QUEUE,
            "EXTERNAL": RuntimeNodeType.EXTERNAL,
        }
        return mapping.get(type_str.upper(), RuntimeNodeType.SERVICE)
