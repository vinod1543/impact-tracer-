"""Interactive REPL module stub."""

from __future__ import annotations

from pathlib import Path

from prompt_toolkit import prompt
from rich.console import Console

from impact_tracer.cli.intent_parser import parse_intent
from impact_tracer.cli.session import CliSession
from impact_tracer.core.orchestrator import analyze
from impact_tracer.output.cli_reporter import render_cli_report
from impact_tracer.output.graph_visualizer import generate_interactive_graph
from impact_tracer.output.markdown_reporter import write_markdown_report


def run_repl(project_path: str = ".") -> None:
    """Run interactive REPL loop.

    Returns:
        None
    """
    console = Console()
    session = CliSession(current_project=project_path)
    console.print("[bold cyan]Impact Tracer REPL[/bold cyan] - type 'exit' to quit")

    while True:
        user_input = prompt("impact-tracer> ").strip()
        if user_input.lower() in {"exit", "quit"}:
            console.print("Bye.")
            return None
        if not user_input:
            continue

        session.last_query = user_input
        intent = parse_intent(user_input)
        operation = intent.get("operation", "analyze_diff")
        session.last_operation = operation

        if operation == "show_graph":
            report = analyze("", session.current_project or ".", enable_llm=False)
            graph_path = generate_interactive_graph(report, output_path="graph.html")
            console.print(f"Interactive graph written to: {graph_path}")
            continue

        if operation == "expand_last_report":
            if session.last_report_id is None:
                console.print("No previous report available in this session.")
            else:
                console.print(f"Last report id: {session.last_report_id}")
            continue

        diff_text = _resolve_diff_text(user_input)
        if not diff_text:
            console.print("No diff input found. Include unified diff text or a .diff file path.")
            continue

        report = analyze(diff_text, session.current_project or ".")
        session.last_report_id = f"report-{len(report.changed_symbols)}-{len(report.affected_symbols)}"
        render_cli_report(report, console=console)

        if "markdown" in user_input.lower():
            graph_path = generate_interactive_graph(report, output_path="graph.html")
            output_path = write_markdown_report(report, output_path="impact_report.md", interactive_graph_path=graph_path)
            console.print(f"Markdown report written to: {output_path}")

    return None


def _resolve_diff_text(user_input: str) -> str:
    """Resolve diff text from REPL input.

    Args:
        user_input: Raw user input.

    Returns:
        str: Unified diff content if present, otherwise empty string.
    """
    stripped = user_input.strip()
    if stripped.startswith("--- "):
        return stripped

    if stripped.endswith(".diff"):
        diff_path = Path(stripped)
        if diff_path.exists():
            return diff_path.read_text(encoding="utf-8")

    tokens = stripped.split()
    for token in tokens:
        if token.endswith(".diff"):
            diff_path = Path(token)
            if diff_path.exists():
                return diff_path.read_text(encoding="utf-8")

    return ""
