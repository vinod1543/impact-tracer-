"""Nginx / Envoy access-log parser.

Parses structured (JSON) access logs to discover HTTP routing
relationships between gateway and upstream services.
"""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path

from impact_tracer.models.runtime import (
    RuntimeEdge,
    RuntimeNode,
    RuntimeNodeType,
    RuntimeTraceGraph,
)


class NginxLogParser:
    """Parse JSON-formatted Nginx/Envoy access logs."""

    def parse(self, path: str) -> RuntimeTraceGraph:
        """Parse a JSON-lines access log.

        Expected format (one JSON object per line)::

            {"upstream": "payments-api", "path": "/api/pay", "status": 200,
             "response_time_ms": 12.5, "method": "POST"}

        Args:
            path: Path to JSON-lines access log.

        Returns:
            RuntimeTraceGraph with gateway → upstream edges.
        """
        file_path = Path(path)
        if not file_path.exists():
            return RuntimeTraceGraph()

        nodes: dict[str, RuntimeNode] = {}
        edge_agg: dict[tuple[str, str], list[float]] = defaultdict(list)
        edge_counts: Counter[tuple[str, str]] = Counter()

        gateway_id = "gateway"
        nodes[gateway_id] = RuntimeNode(
            id=gateway_id,
            label="gateway",
            node_type=RuntimeNodeType.SERVICE,
            metadata={"role": "edge-proxy"},
        )

        try:
            for line in file_path.read_text(encoding="utf-8").strip().splitlines():
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue

                upstream = entry.get("upstream", "unknown")
                latency = entry.get("response_time_ms", 0.0)

                if upstream not in nodes:
                    nodes[upstream] = RuntimeNode(
                        id=upstream,
                        label=upstream,
                        node_type=RuntimeNodeType.SERVICE,
                    )

                key = (gateway_id, upstream)
                edge_counts[key] += 1
                edge_agg[key].append(float(latency))
        except Exception:
            return RuntimeTraceGraph()

        edges: list[RuntimeEdge] = []
        for (src, tgt), count in edge_counts.items():
            latencies = edge_agg[(src, tgt)]
            avg_lat = sum(latencies) / len(latencies) if latencies else None
            edges.append(RuntimeEdge(
                source=src,
                target=tgt,
                edge_type="HTTP_PROXY",
                confidence=0.85,
                call_count=count,
                latency_ms=round(avg_lat, 2) if avg_lat is not None else None,
            ))

        return RuntimeTraceGraph(
            nodes=list(nodes.values()),
            edges=edges,
        )
