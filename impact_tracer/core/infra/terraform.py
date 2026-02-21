"""Terraform HCL parser.

Parses Terraform .tf files (hcl2 JSON plan output or simplified JSON)
to extract cloud resources and their dependencies.
"""

from __future__ import annotations

import json
from pathlib import Path

from impact_tracer.models.infra import InfraEdge, InfraNode, InfraNodeType, InfraTopology

_TYPE_MAP = {
    "aws_instance": InfraNodeType.SERVICE,
    "aws_ecs_service": InfraNodeType.SERVICE,
    "aws_lambda_function": InfraNodeType.SERVICE,
    "aws_rds_instance": InfraNodeType.DATABASE,
    "aws_db_instance": InfraNodeType.DATABASE,
    "aws_elasticache_cluster": InfraNodeType.DATABASE,
    "aws_sqs_queue": InfraNodeType.QUEUE,
    "aws_sns_topic": InfraNodeType.TOPIC,
    "aws_alb": InfraNodeType.GATEWAY,
    "aws_lb": InfraNodeType.GATEWAY,
    "aws_api_gateway_rest_api": InfraNodeType.GATEWAY,
    "aws_vpc": InfraNodeType.NETWORK,
    "aws_subnet": InfraNodeType.NETWORK,
    "aws_security_group": InfraNodeType.NETWORK,
    "google_compute_instance": InfraNodeType.SERVICE,
    "google_sql_database_instance": InfraNodeType.DATABASE,
    "google_pubsub_topic": InfraNodeType.TOPIC,
    "azurerm_virtual_machine": InfraNodeType.SERVICE,
    "azurerm_sql_server": InfraNodeType.DATABASE,
}


class TerraformParser:
    """Parse Terraform plan JSON output into InfraTopology."""

    def parse(self, path: str) -> InfraTopology:
        """Parse terraform plan JSON (``terraform show -json tfplan``).

        Expected simplified format::

            {
              "resources": [
                {
                  "type": "aws_ecs_service",
                  "name": "payments-api",
                  "provider": "aws",
                  "depends_on": ["aws_rds_instance.payments_db"]
                }
              ]
            }

        Args:
            path: Path to Terraform JSON plan or simplified resource list.

        Returns:
            InfraTopology with cloud resource nodes and dependency edges.
        """
        file_path = Path(path)
        if not file_path.exists():
            return InfraTopology()

        try:
            data = json.loads(file_path.read_text(encoding="utf-8"))
        except Exception:
            return InfraTopology()

        nodes: list[InfraNode] = []
        edges: list[InfraEdge] = []

        resources = data.get("resources", [])
        for res in resources:
            res_type = res.get("type", "unknown")
            res_name = res.get("name", "unknown")
            provider = res.get("provider", self._infer_provider(res_type))
            node_id = f"tf:{res_type}.{res_name}"

            node_type = _TYPE_MAP.get(res_type, InfraNodeType.OTHER)
            nodes.append(InfraNode(
                id=node_id,
                label=res_name,
                node_type=node_type,
                provider=provider,
                metadata={"resource_type": res_type},
            ))

            for dep in res.get("depends_on", []):
                dep_node_id = f"tf:{dep}"
                edges.append(InfraEdge(
                    source=node_id,
                    target=dep_node_id,
                    edge_type="DEPENDS_ON",
                    confidence=1.0,
                ))

        return InfraTopology(nodes=nodes, edges=edges)

    def _infer_provider(self, resource_type: str) -> str:
        """Infer cloud provider from resource type prefix."""
        if resource_type.startswith("aws_"):
            return "aws"
        if resource_type.startswith("google_"):
            return "gcp"
        if resource_type.startswith("azurerm_"):
            return "azure"
        return "unknown"
