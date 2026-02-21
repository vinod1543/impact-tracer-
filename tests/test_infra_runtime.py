"""Tests for infrastructure and runtime parsers + auto-discovery."""

import json
import textwrap
from pathlib import Path

import pytest

from impact_tracer.core.infra.docker_compose import DockerComposeParser
from impact_tracer.core.infra.kubernetes import KubernetesParser
from impact_tracer.core.infra.terraform import TerraformParser
from impact_tracer.core.runtime.otel_parser import OtelTraceParser
from impact_tracer.core.runtime.postgres_parser import PostgresLogParser
from impact_tracer.core.discovery import discover_infra, discover_runtime
from impact_tracer.models.infra import InfraNodeType


# ---------- Docker Compose ----------

class TestDockerComposeParser:
    def test_parse_demo_compose(self):
        parser = DockerComposeParser()
        topo = parser.parse("demo/payments_service/docker-compose.yml")
        assert len(topo.nodes) == 8
        node_ids = {n.id for n in topo.nodes}
        assert "service:postgres" in node_ids
        assert "service:payments-api" in node_ids
        assert "service:nginx" in node_ids

    def test_depends_on_edges(self):
        parser = DockerComposeParser()
        topo = parser.parse("demo/payments_service/docker-compose.yml")
        depends_edges = [e for e in topo.edges if e.edge_type == "DEPENDS_ON"]
        assert len(depends_edges) >= 7  # payments-api(3) + notification(2) + worker(3) + nginx(2)

    def test_env_reference_edges(self):
        parser = DockerComposeParser()
        topo = parser.parse("demo/payments_service/docker-compose.yml")
        env_edges = [e for e in topo.edges if e.edge_type == "ENV_REFERENCE"]
        assert len(env_edges) >= 5

    def test_node_type_detection(self):
        parser = DockerComposeParser()
        topo = parser.parse("demo/payments_service/docker-compose.yml")
        type_map = {n.id: n.node_type for n in topo.nodes}
        assert type_map["service:postgres"] == InfraNodeType.DATABASE
        assert type_map["service:rabbitmq"] == InfraNodeType.QUEUE
        assert type_map["service:nginx"] == InfraNodeType.GATEWAY

    def test_missing_file(self):
        parser = DockerComposeParser()
        topo = parser.parse("nonexistent.yml")
        assert len(topo.nodes) == 0

    def test_empty_compose(self, tmp_path):
        f = tmp_path / "docker-compose.yml"
        f.write_text("version: '3'\n")
        parser = DockerComposeParser()
        topo = parser.parse(str(f))
        assert len(topo.nodes) == 0


# ---------- Kubernetes ----------

class TestKubernetesParser:
    def test_parse_deployment_and_service(self, tmp_path):
        manifest = textwrap.dedent("""\
            apiVersion: apps/v1
            kind: Deployment
            metadata:
              name: payments-api
              namespace: prod
            spec:
              template:
                metadata:
                  labels:
                    app: payments
                spec:
                  containers:
                    - name: api
                      image: payments:latest
            ---
            apiVersion: v1
            kind: Service
            metadata:
              name: payments-svc
              namespace: prod
            spec:
              selector:
                app: payments
              ports:
                - port: 80
        """)
        f = tmp_path / "k8s.yaml"
        f.write_text(manifest)
        parser = KubernetesParser()
        topo = parser.parse(str(f))
        assert len(topo.nodes) == 2
        # Service should route to deployment
        routes = [e for e in topo.edges if e.edge_type == "ROUTES_TO"]
        assert len(routes) == 1


# ---------- Terraform ----------

class TestTerraformParser:
    def test_parse_resources(self, tmp_path):
        plan = {
            "resources": [
                {"type": "aws_ecs_service", "name": "api", "depends_on": ["aws_rds_instance.db"]},
                {"type": "aws_rds_instance", "name": "db"},
                {"type": "aws_sqs_queue", "name": "tasks"},
            ]
        }
        f = tmp_path / "tfplan.json"
        f.write_text(json.dumps(plan))
        parser = TerraformParser()
        topo = parser.parse(str(f))
        assert len(topo.nodes) == 3
        assert len(topo.edges) == 1
        assert topo.edges[0].source == "tf:aws_ecs_service.api"
        assert topo.edges[0].target == "tf:aws_rds_instance.db"

    def test_provider_detection(self, tmp_path):
        plan = {"resources": [
            {"type": "aws_lambda_function", "name": "fn"},
            {"type": "google_compute_instance", "name": "vm"},
            {"type": "azurerm_virtual_machine", "name": "win"},
        ]}
        f = tmp_path / "tfplan.json"
        f.write_text(json.dumps(plan))
        parser = TerraformParser()
        topo = parser.parse(str(f))
        providers = {n.label: n.provider for n in topo.nodes}
        assert providers["fn"] == "aws"
        assert providers["vm"] == "gcp"
        assert providers["win"] == "azure"


# ---------- OpenTelemetry / Runtime ----------

class TestOtelTraceParser:
    def test_parse_demo_traces(self):
        parser = OtelTraceParser()
        graph = parser.parse("demo/payments_service/runtime_traces.json")
        assert len(graph.nodes) == 7
        assert len(graph.edges) == 13

    def test_call_count_and_latency(self):
        parser = OtelTraceParser()
        graph = parser.parse("demo/payments_service/runtime_traces.json")
        gateway_edges = [e for e in graph.edges if e.source == "gateway"]
        assert len(gateway_edges) == 2
        total_calls = sum(e.call_count for e in gateway_edges if e.call_count)
        assert total_calls == 52400 + 12100

    def test_missing_file(self):
        parser = OtelTraceParser()
        graph = parser.parse("nonexistent.json")
        assert len(graph.nodes) == 0


# ---------- PostgreSQL ----------

class TestPostgresLogParser:
    def test_parse_queries(self, tmp_path):
        data = {
            "database": "payments_db",
            "queries": [
                {"query": "SELECT * FROM payments WHERE id = $1", "calls": 1000,
                 "mean_time_ms": 1.5, "caller_service": "api"},
                {"query": "INSERT INTO audit_log (event) VALUES ($1)", "calls": 500,
                 "mean_time_ms": 2.0, "caller_service": "api"},
            ]
        }
        f = tmp_path / "pg_stat.json"
        f.write_text(json.dumps(data))
        parser = PostgresLogParser()
        graph = parser.parse(str(f))
        assert len(graph.nodes) >= 3  # api + 2 tables
        table_nodes = [n for n in graph.nodes if n.node_type.value == "TABLE"]
        assert len(table_nodes) == 2


# ---------- Auto-Discovery ----------

class TestDiscovery:
    def test_discover_infra_demo(self):
        topo = discover_infra("demo/payments_service")
        assert topo is not None
        assert len(topo.nodes) >= 8

    def test_discover_runtime_demo(self):
        graph = discover_runtime("demo/payments_service")
        assert graph is not None
        assert len(graph.nodes) >= 7
        assert len(graph.edges) >= 13

    def test_discover_empty(self, tmp_path):
        assert discover_infra(str(tmp_path)) is None
        assert discover_runtime(str(tmp_path)) is None
