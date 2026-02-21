"""Tests for CLI main argument handling and output modes."""

from __future__ import annotations

from pathlib import Path

from impact_tracer.cli.main import main


def test_cli_returns_error_when_analyze_without_diff(monkeypatch) -> None:
    """CLI should fail fast for analyze intent when no diff source is provided."""
    monkeypatch.setattr("sys.argv", ["impact-tracer", "what breaks if i change validate", "--project", "demo/payments_service"])
    exit_code = main()
    assert exit_code == 2


def test_cli_markdown_mode_writes_output_files(monkeypatch, tmp_path) -> None:
    """CLI markdown mode should generate markdown and graph outputs."""
    markdown_out = tmp_path / "report.md"
    graph_out = tmp_path / "graph.html"
    monkeypatch.setattr(
        "sys.argv",
        [
            "impact-tracer",
            "--project",
            "demo/payments_service",
            "--diff-file",
            "demo/signature_change.diff",
            "--format",
            "markdown",
            "--output",
            str(markdown_out),
            "--graph-output",
            str(graph_out),
            "--no-llm",
        ],
    )
    exit_code = main()
    assert exit_code == 0
    assert markdown_out.exists()
    assert graph_out.exists()


def test_cli_json_mode_writes_output_file(monkeypatch, tmp_path) -> None:
    """CLI json mode should generate json file output."""
    json_out = tmp_path / "report.json"
    monkeypatch.setattr(
        "sys.argv",
        [
            "impact-tracer",
            "--project",
            "demo/payments_service",
            "--diff-file",
            "demo/signature_change.diff",
            "--format",
            "json",
            "--output",
            str(json_out),
            "--no-llm",
        ],
    )
    exit_code = main()
    assert exit_code == 0
    assert json_out.exists()
    assert "overall_risk" in json_out.read_text(encoding="utf-8")
