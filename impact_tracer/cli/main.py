"""CLI entry point for Impact Tracer.

Layer: Interfaces (Layer 5)
Responsibility: Single-shot command and basic startup.
Implements: PRD terminal interface baseline for MVP scaffolding.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from impact_tracer.cli.intent_parser import parse_intent
from impact_tracer.cli.repl import run_repl
from impact_tracer.core.orchestrator import analyze
from impact_tracer.output.cli_reporter import render_cli_report
from impact_tracer.output.graph_visualizer import generate_interactive_graph
from impact_tracer.output.json_reporter import render_json_report
from impact_tracer.output.markdown_reporter import write_markdown_report


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI argument parser.

    Returns:
        argparse.ArgumentParser: Configured parser instance.
    """
    parser = argparse.ArgumentParser(prog="impact-tracer", description="Impact Tracer CLI")
    parser.add_argument("query", nargs="?", help="Natural language query")
    parser.add_argument("--project", default=".", help="Project path")
    parser.add_argument("--format", choices=["text", "json", "markdown"], default="text", help="Output format")
    parser.add_argument("--diff-file", default=None, help="Path to unified diff file")
    parser.add_argument("--output", default=None, help="Output file path")
    parser.add_argument("--graph-output", default="graph.html", help="Interactive graph HTML output path")
    parser.add_argument("--no-llm", action="store_true", help="Skip LLM explanation stage")
    return parser


def main() -> int:
    """Run the CLI entry point.

    Returns:
        int: Exit code.
    """
    parser = build_parser()
    args = parser.parse_args()

    if args.query is None and args.diff_file is None:
        run_repl(project_path=args.project)
        return 0

    diff_text = ""
    if args.diff_file:
        diff_text = Path(args.diff_file).read_text(encoding="utf-8")
    elif args.query and args.query.startswith("--- "):
        diff_text = args.query

    intent = parse_intent(args.query or "")
    operation = intent.get("operation", "analyze_diff")

    if operation == "analyze_diff" and not diff_text:
        print("No diff input found. Provide --diff-file <path> or pass unified diff text.")
        return 2

    report = analyze(diff_text, args.project, enable_llm=not args.no_llm)

    if operation == "show_graph" and args.format != "markdown":
        graph_path = generate_interactive_graph(report, output_path=args.graph_output)
        print(f"Interactive graph written to: {graph_path}")
        return 0

    if args.format == "json":
        payload = render_json_report(report)
        if args.output:
            Path(args.output).write_text(payload, encoding="utf-8")
        else:
            print(payload)
        return 0

    if args.format == "markdown":
        graph_path = generate_interactive_graph(report, output_path=args.graph_output)
        output_path = args.output or "impact_report.md"
        write_markdown_report(report, output_path=output_path, interactive_graph_path=graph_path)
        print(f"Markdown report written to: {output_path}")
        print(f"Interactive graph written to: {graph_path}")
        return 0

    # text fallback
    render_cli_report(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
