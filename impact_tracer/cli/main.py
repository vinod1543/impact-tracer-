"""CLI entry point for Impact Tracer.

Layer: Interfaces (Layer 5)
Responsibility: Single-shot command and basic startup.
Implements: PRD terminal interface baseline for MVP scaffolding.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

from impact_tracer.cli.intent_parser import parse_intent
from impact_tracer.cli.repl import run_repl
from impact_tracer.core.git_diff import discover_git_changes, get_branch_diff, get_staged_diff, get_unstaged_diff
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
    parser = argparse.ArgumentParser(
        prog="impact-tracer",
        description="Impact Tracer — analyze code change blast radius",
        epilog=(
            "Examples:\n"
            "  impact-tracer -p .                                  (REPL — auto-detects git changes)\n"
            "  impact-tracer -p . --git                            (analyze unstaged changes)\n"
            "  impact-tracer -p . --staged                         (analyze staged changes)\n"
            "  impact-tracer -p . --branch main                    (diff current branch vs main)\n"
            "  impact-tracer -p . --git --all                      (analyze + export everything)\n"
            "  impact-tracer -p demo/payments_service -d demo/signature_change.diff   (manual diff)\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("query", nargs="?", help="Natural language query")
    parser.add_argument("--project", "-p", default=".", help="Project path")
    parser.add_argument("--diff-file", "-d", default=None, help="Path to unified diff file (manual)")
    parser.add_argument("--git", "-g", action="store_true", help="Analyze unstaged git changes (auto)")
    parser.add_argument("--staged", "-s", action="store_true", help="Analyze staged git changes")
    parser.add_argument("--branch", "-b", default=None, metavar="BASE", help="Analyze diff vs a base branch (e.g. main)")
    parser.add_argument("--format", "-f", choices=["text", "json", "markdown"], default="text", help="Output format")
    parser.add_argument("--output", "-o", default=None, help="Output file path")
    parser.add_argument("--graph-output", default="graph.html", help="Graph HTML output path")
    parser.add_argument("--no-llm", action="store_true", help="Skip LLM explanation")
    parser.add_argument("--all", action="store_true", help="Export ALL outputs (terminal + JSON + Markdown + Graph)")
    return parser


def main() -> int:
    """Run the CLI entry point.

    Returns:
        int: Exit code.
    """
    parser = build_parser()
    args = parser.parse_args()

    # ── Resolve diff text from git flags or manual file ──────────
    diff_text = ""

    if args.git:
        gc = get_unstaged_diff(args.project)
        if gc:
            diff_text = gc.diff_text
            print(f"Git: {gc}")
        else:
            print("No unstaged Python changes detected.")
            return 2

    elif args.staged:
        gc = get_staged_diff(args.project)
        if gc:
            diff_text = gc.diff_text
            print(f"Git: {gc}")
        else:
            print("No staged Python changes detected.")
            return 2

    elif args.branch:
        gc = get_branch_diff(args.project, base=args.branch)
        if gc:
            diff_text = gc.diff_text
            print(f"Git: {gc}")
        else:
            print(f"No Python changes found between {args.branch} and HEAD.")
            return 2

    elif args.diff_file:
        diff_text = Path(args.diff_file).read_text(encoding="utf-8")

    elif args.query and args.query.startswith("--- "):
        diff_text = args.query

    # ── No diff source and no query → launch REPL ────────────────
    if not diff_text and args.query is None:
        run_repl(project_path=args.project)
        return 0

    intent = parse_intent(args.query or "")
    operation = intent.get("operation", "analyze_diff")

    # If user described a change in natural language, generate a diff via LLM
    if operation == "describe_change" and not diff_text:
        from impact_tracer.core.llm.diff_generator import DiffGenerator
        generator = DiffGenerator()
        diff_text = generator.generate(args.query, args.project) or ""
        if not diff_text:
            print("Could not generate diff from description. Check your OpenAI API key or try rephrasing.")
            return 2

    if operation == "analyze_diff" and not diff_text:
        # Last resort: try auto-detect from git
        changes = discover_git_changes(args.project)
        if changes:
            diff_text = changes[0].diff_text
            print(f"Auto-detected: {changes[0]}")
        else:
            print("No changes detected. Use --git, --staged, --branch, or --diff-file.")
            return 2

    report = analyze(diff_text, args.project, enable_llm=not args.no_llm)

    # --all: export everything at once
    if args.all:
        render_cli_report(report)
        json_path = args.output or "impact_report.json"
        Path(json_path).write_text(render_json_report(report), encoding="utf-8")
        graph_path = generate_interactive_graph(report, output_path=args.graph_output)
        md_path = write_markdown_report(report, output_path="impact_report.md", interactive_graph_path=graph_path)
        print(f"\nJSON   → {json_path}")
        print(f"Report → {md_path}")
        print(f"Graph  → {graph_path}")
        _open_file(graph_path)
        return 0

    if operation == "show_graph" and args.format != "markdown":
        graph_path = generate_interactive_graph(report, output_path=args.graph_output)
        print(f"Interactive graph written to: {graph_path}")
        _open_file(graph_path)
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


def _open_file(file_path: str) -> None:
    """Open a file with the system default application."""
    try:
        if sys.platform == "win32":
            os.startfile(file_path)
        elif sys.platform == "darwin":
            subprocess.run(["open", file_path], check=False)
        else:
            subprocess.run(["xdg-open", file_path], check=False)
    except Exception:
        pass


if __name__ == "__main__":
    raise SystemExit(main())
