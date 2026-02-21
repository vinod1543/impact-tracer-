"""Docker Compose infrastructure parser.

Parses docker-compose.yml files to extract service nodes and dependency edges.
Adds INFRA layer nodes to the unified dependency graph.
"""

from __future__ import annotations

from pathlib import Path

import yaml

from impact_tracer.models.infra import InfraEdge, InfraNode, InfraNodeType, InfraTopology


class DockerComposeParser:
    """Parse docker-compose.yml into InfraTopology."""

    def parse(self, path: str) -> InfraTopology:
        """Parse a docker-compose file.

        Args:
            path: Path to docker-compose.yml.

        Returns:
            InfraTopology: Parsed infrastructure topology.
        """
        file_path = Path(path)
        if not file_path.exists():
            return InfraTopology()

        try:
            content = yaml.safe_load(file_path.read_text(encoding="utf-8"))
        except Exception:
            return InfraTopology()

        if not content or "services" not in content:
            return InfraTopology()

        nodes: list[InfraNode] = []
        edges: list[InfraEdge] = []

        services = content.get("services", {})
        for service_name, service_config in services.items():
            node_type = self._detect_node_type(service_name, service_config)
            node = InfraNode(
                id=f"service:{service_name}",
                label=service_name,
                node_type=node_type,
                provider="docker",
                metadata={
                    "image": service_config.get("image", ""),
                    "ports": str(service_config.get("ports", [])),
                },
            )
            nodes.append(node)

            # Parse depends_on
            depends_on = service_config.get("depends_on", [])
            if isinstance(depends_on, dict):
                depends_on = list(depends_on.keys())
            for dep in depends_on:
                edges.append(InfraEdge(
                    source=f"service:{service_name}",
                    target=f"service:{dep}",
                    edge_type="DEPENDS_ON",
                    confidence=1.0,
                ))

            # Parse links
            for link in service_config.get("links", []):
                link_target = link.split(":")[0]
                edges.append(InfraEdge(
                    source=f"service:{service_name}",
                    target=f"service:{link_target}",
                    edge_type="LINKS_TO",
                    confidence=1.0,
                ))

            # Parse environment for connection strings
            env_vars = service_config.get("environment", {})
            if isinstance(env_vars, list):
                env_vars = dict(item.split("=", 1) for item in env_vars if "=" in item)
            for key, value in env_vars.items():
                for other_service in services:
                    if other_service != service_name and other_service in str(value):
                        edges.append(InfraEdge(
                            source=f"service:{service_name}",
                            target=f"service:{other_service}",
                            edge_type="ENV_REFERENCE",
                            confidence=0.8,
                            metadata={"env_var": key},
                        ))

        return InfraTopology(nodes=nodes, edges=edges)

    def _detect_node_type(self, name: str, config: dict) -> InfraNodeType:
        """Detect infrastructure node type from service name/image."""
        image = str(config.get("image", "")).lower()
        name_lower = name.lower()

        db_keywords = ["postgres", "mysql", "mongo", "redis", "database", "db", "mariadb"]
        queue_keywords = ["rabbitmq", "kafka", "celery", "sqs", "queue", "worker"]
        gateway_keywords = ["nginx", "traefik", "gateway", "proxy", "haproxy"]

        for kw in db_keywords:
            if kw in image or kw in name_lower:
                return InfraNodeType.DATABASE
        for kw in queue_keywords:
            if kw in image or kw in name_lower:
                return InfraNodeType.QUEUE
        for kw in gateway_keywords:
            if kw in image or kw in name_lower:
                return InfraNodeType.GATEWAY

        return InfraNodeType.SERVICE
