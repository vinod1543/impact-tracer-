"""Auto-discovery for infrastructure configs and runtime trace files.

Layer: Engines (Layer 3)
Responsibility: Scan a project directory for known infra/runtime file patterns,
parse them, and return merged InfraTopology / RuntimeTraceGraph.
"""

from __future__ import annotations

from pathlib import Path

from impact_tracer.core.infra.docker_compose import DockerComposeParser
from impact_tracer.core.infra.kubernetes import KubernetesParser
from impact_tracer.core.infra.terraform import TerraformParser
from impact_tracer.core.runtime.otel_parser import OtelTraceParser
from impact_tracer.models.infra import InfraTopology
from impact_tracer.models.runtime import RuntimeTraceGraph

# Infra file patterns → parser class
_INFRA_PATTERNS: list[tuple[str, type]] = [
    ("docker-compose.yml", DockerComposeParser),
    ("docker-compose.yaml", DockerComposeParser),
    ("compose.yml", DockerComposeParser),
    ("compose.yaml", DockerComposeParser),
]

# Glob patterns for Kubernetes manifests
_K8S_GLOBS = ["k8s/*.yml", "k8s/*.yaml", "kubernetes/*.yml", "kubernetes/*.yaml",
              "deploy/*.yml", "deploy/*.yaml"]

# Terraform plan JSON
_TF_PATTERNS = ["terraform.tfplan.json", "tfplan.json", "infra/*.tf.json"]

# Runtime trace file patterns
_RUNTIME_PATTERNS = [
    "runtime_traces.json",
    "traces.json",
    "otel_traces.json",
    "runtime/*.json",
]


def discover_infra(project_path: str) -> InfraTopology | None:
    """Scan project for infrastructure config files and merge into one topology.

    Args:
        project_path: Root directory to scan.

    Returns:
        Merged InfraTopology or None if nothing found.
    """
    root = Path(project_path)
    all_nodes = []
    all_edges = []

    # Docker Compose
    for pattern, parser_cls in _INFRA_PATTERNS:
        candidate = root / pattern
        if candidate.exists():
            parser = parser_cls()
            topo = parser.parse(str(candidate))
            all_nodes.extend(topo.nodes)
            all_edges.extend(topo.edges)

    # Kubernetes manifests
    k8s_parser = KubernetesParser()
    for glob_pattern in _K8S_GLOBS:
        for candidate in root.glob(glob_pattern):
            topo = k8s_parser.parse(str(candidate))
            all_nodes.extend(topo.nodes)
            all_edges.extend(topo.edges)

    # Terraform plans
    tf_parser = TerraformParser()
    for pattern in _TF_PATTERNS:
        for candidate in root.glob(pattern):
            topo = tf_parser.parse(str(candidate))
            all_nodes.extend(topo.nodes)
            all_edges.extend(topo.edges)

    if not all_nodes and not all_edges:
        return None

    return InfraTopology(nodes=all_nodes, edges=all_edges)


def discover_runtime(project_path: str) -> RuntimeTraceGraph | None:
    """Scan project for runtime trace files and merge into one graph.

    Args:
        project_path: Root directory to scan.

    Returns:
        Merged RuntimeTraceGraph or None if nothing found.
    """
    root = Path(project_path)
    all_nodes = []
    all_edges = []

    otel_parser = OtelTraceParser()
    for pattern in _RUNTIME_PATTERNS:
        for candidate in root.glob(pattern):
            graph = otel_parser.parse(str(candidate))
            all_nodes.extend(graph.nodes)
            all_edges.extend(graph.edges)

    if not all_nodes and not all_edges:
        return None

    # Deduplicate nodes by id
    seen = set()
    unique_nodes = []
    for node in all_nodes:
        if node.id not in seen:
            seen.add(node.id)
            unique_nodes.append(node)

    return RuntimeTraceGraph(nodes=unique_nodes, edges=all_edges)
