"""Tests for Phase 4 markdown output and interactive graph export."""

from __future__ import annotations

from pathlib import Path

from impact_tracer.core.orchestrator import analyze
from impact_tracer.output.graph_visualizer import generate_interactive_graph
from impact_tracer.output.markdown_reporter import render_markdown_report, write_markdown_report


def test_markdown_report_contains_simple_detailed_sections(tmp_path) -> None:
    """Markdown report includes key sections and visual graph references."""
    diff_text = Path("demo/signature_change.diff").read_text(encoding="utf-8")
    report = analyze(diff_text, "demo/payments_service", enable_llm=False)

    markdown = render_markdown_report(report, interactive_graph_path="graph.html")

    assert "# Impact Tracer Report" in markdown
    assert "## 1) Quick Result" in markdown
    assert "## 4) Visual Graph" in markdown
    assert "```mermaid" in markdown
    assert "Interactive graph: [graph.html](graph.html)" in markdown

    output_path = tmp_path / "impact_report.md"
    write_markdown_report(report, str(output_path), interactive_graph_path="graph.html")
    assert output_path.exists()


def test_interactive_graph_html_generated(tmp_path) -> None:
    """Graph visualizer generates an interactive HTML file."""
    diff_text = Path("demo/signature_change.diff").read_text(encoding="utf-8")
    report = analyze(diff_text, "demo/payments_service", enable_llm=False)

    graph_path = tmp_path / "impact_graph.html"
    output = generate_interactive_graph(report, output_path=str(graph_path))

    assert output.endswith("impact_graph.html")
    assert graph_path.exists()
    content = graph_path.read_text(encoding="utf-8")
    assert "<html" in content.lower()
    assert "vis-network" in content.lower() or "network" in content.lower()
