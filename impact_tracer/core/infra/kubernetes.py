"""Kubernetes manifest parser.

Parses Kubernetes YAML manifests (Deployments, Services, ConfigMaps)
to extract infrastructure-level service dependencies.
"""

from __future__ import annotations

from pathlib import Path

import yaml

from impact_tracer.models.infra import InfraEdge, InfraNode, InfraNodeType, InfraTopology


class KubernetesParser:
    """Parse Kubernetes manifests into InfraTopology."""

    def parse(self, path: str) -> InfraTopology:
        """Parse a single Kubernetes YAML manifest (multi-doc supported).

        Args:
            path: Path to a .yaml/.yml Kubernetes manifest.

        Returns:
            InfraTopology with parsed nodes and edges.
        """
        file_path = Path(path)
        if not file_path.exists():
            return InfraTopology()

        try:
            raw = file_path.read_text(encoding="utf-8")
            documents = list(yaml.safe_load_all(raw))
        except Exception:
            return InfraTopology()

        nodes: list[InfraNode] = []
        edges: list[InfraEdge] = []

        service_selectors: dict[str, dict] = {}
        deployment_labels: dict[str, dict] = {}

        for doc in documents:
            if not doc or "kind" not in doc:
                continue
            kind = doc.get("kind", "")
            metadata = doc.get("metadata", {})
            name = metadata.get("name", "unknown")
            namespace = metadata.get("namespace", "default")
            node_id = f"k8s:{namespace}/{name}"

            if kind == "Deployment":
                nodes.append(InfraNode(
                    id=node_id,
                    label=name,
                    node_type=InfraNodeType.SERVICE,
                    provider="kubernetes",
                    metadata={"kind": kind, "namespace": namespace},
                ))
                spec = doc.get("spec", {})
                template = spec.get("template", {})
                pod_labels = template.get("metadata", {}).get("labels", {})
                deployment_labels[name] = pod_labels

                containers = template.get("spec", {}).get("containers", [])
                for container in containers:
                    for env in container.get("env", []):
                        val = str(env.get("value", ""))
                        if ".svc" in val or "SERVICE_HOST" in env.get("name", ""):
                            ref = val.split(".")[0] if ".svc" in val else val
                            edges.append(InfraEdge(
                                source=node_id,
                                target=f"k8s:{namespace}/{ref}",
                                edge_type="ENV_REFERENCE",
                                confidence=0.8,
                                metadata={"env_var": env.get("name", "")},
                            ))

            elif kind == "Service":
                nodes.append(InfraNode(
                    id=node_id,
                    label=name,
                    node_type=InfraNodeType.GATEWAY,
                    provider="kubernetes",
                    metadata={"kind": kind, "namespace": namespace},
                ))
                selector = doc.get("spec", {}).get("selector", {})
                service_selectors[name] = selector

            elif kind == "ConfigMap":
                nodes.append(InfraNode(
                    id=node_id,
                    label=name,
                    node_type=InfraNodeType.OTHER,
                    provider="kubernetes",
                    metadata={"kind": kind, "namespace": namespace},
                ))

        # Link Services to Deployments via selector matching
        for svc_name, selector in service_selectors.items():
            if not selector:
                continue
            for deploy_name, labels in deployment_labels.items():
                if all(labels.get(k) == v for k, v in selector.items()):
                    namespace = "default"
                    edges.append(InfraEdge(
                        source=f"k8s:{namespace}/{svc_name}",
                        target=f"k8s:{namespace}/{deploy_name}",
                        edge_type="ROUTES_TO",
                        confidence=1.0,
                    ))

        return InfraTopology(nodes=nodes, edges=edges)
