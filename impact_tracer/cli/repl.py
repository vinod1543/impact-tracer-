"""Interactive REPL with git auto-detection and post-analysis action menu."""

from __future__ import annotations

import glob
import os
import subprocess
import sys
from pathlib import Path

from prompt_toolkit import prompt
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from impact_tracer.cli.intent_parser import parse_intent
from impact_tracer.cli.session import CliSession
from impact_tracer.core.git_diff import GitChange, discover_git_changes, is_git_repo
from impact_tracer.core.llm.diff_generator import DiffGenerator
from impact_tracer.core.orchestrator import analyze
from impact_tracer.output.cli_reporter import render_cli_report
from impact_tracer.output.graph_visualizer import generate_interactive_graph
from impact_tracer.output.json_reporter import render_json_report
from impact_tracer.output.markdown_reporter import write_markdown_report

# ── Action menu shown after every analysis ──────────────────────────

_ACTION_MENU = """
[bold cyan]What would you like to do?[/bold cyan]

  [bold white]1[/bold white]  Export JSON report
  [bold white]2[/bold white]  Export Markdown report
  [bold white]3[/bold white]  Open interactive graph
  [bold white]4[/bold white]  Export ALL (JSON + Markdown + Graph)
  [bold white]5[/bold white]  Show propagation paths
  [bold white]6[/bold white]  Analyze another diff
  [bold white]0[/bold white]  Skip / continue

"""


def _discover_diff_files(project_path: str) -> list[Path]:
    """Find all .diff files near the project for easy selection.

    Searches in the project directory itself, its parent, and common
    locations like ``demo/`` and ``diffs/``.
    """
    project = Path(project_path).resolve()
    search_roots = {project, project.parent}
    # common convention folders
    for name in ("demo", "diffs", "patches"):
        candidate = project.parent / name
        if candidate.is_dir():
            search_roots.add(candidate)

    found: dict[str, Path] = {}
    for root in search_roots:
        for p in root.rglob("*.diff"):
            # deduplicate by resolved path
            key = str(p.resolve())
            if key not in found:
                found[key] = p
    # sort for consistent ordering
    return sorted(found.values(), key=lambda p: p.name)


def _show_action_menu(console: Console, report: object, project_path: str) -> None:
    """Show interactive action menu after analysis.

    Args:
        console: Rich console instance.
        report: ImpactReport object.
        project_path: Current project path.
    """
    console.print(_ACTION_MENU)

    while True:
        choice = prompt("Choose [0-6]: ").strip()

        if choice == "1":
            out = "impact_report.json"
            payload = render_json_report(report)
            Path(out).write_text(payload, encoding="utf-8")
            console.print(f"[green]JSON report saved → {out}[/green]")

        elif choice == "2":
            graph_path = generate_interactive_graph(report, output_path="graph.html")
            md_path = write_markdown_report(report, output_path="impact_report.md", interactive_graph_path=graph_path)
            console.print(f"[green]Markdown report saved → {md_path}[/green]")
            console.print(f"[green]Interactive graph saved → {graph_path}[/green]")

        elif choice == "3":
            graph_path = generate_interactive_graph(report, output_path="graph.html")
            console.print(f"[green]Graph saved → {graph_path}[/green]")
            _open_file(graph_path)

        elif choice == "4":
            # Export ALL
            json_path = "impact_report.json"
            payload = render_json_report(report)
            Path(json_path).write_text(payload, encoding="utf-8")
            graph_path = generate_interactive_graph(report, output_path="graph.html")
            md_path = write_markdown_report(report, output_path="impact_report.md", interactive_graph_path=graph_path)
            console.print(f"[green]JSON   → {json_path}[/green]")
            console.print(f"[green]Report → {md_path}[/green]")
            console.print(f"[green]Graph  → {graph_path}[/green]")
            _open_file(graph_path)

        elif choice == "5":
            console.print("[bold]Propagation Paths:[/bold]")
            for path_info in report.propagation_paths:
                console.print(f"  {' → '.join(path_info.path)}")
            if not report.propagation_paths:
                console.print("  (no propagation paths)")
            continue  # stay in menu

        elif choice in {"6", "0", ""}:
            return  # back to main REPL loop

        else:
            console.print("[yellow]Invalid choice. Enter 0-6.[/yellow]")
            continue

        # After exporting, ask again or return
        console.print()
        again = prompt("Anything else? [0-6 or Enter to continue]: ").strip()
        if again in {"", "0", "6"}:
            return
        # re-process the choice
        choice = again
        continue


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
        pass  # non-critical


# ── Main REPL loop ──────────────────────────────────────────────────

def run_repl(project_path: str = ".") -> None:
    """Run interactive REPL loop.

    Returns:
        None
    """
    console = Console()
    session = CliSession(current_project=project_path)

    # Auto-discover git changes + .diff files
    git_changes = discover_git_changes(project_path)
    diff_files = _discover_diff_files(project_path)

    # Build unified selection list: git changes first, then .diff files
    choices: list[tuple[str, str | None]] = []  # (label, diff_text_or_None)
    for gc in git_changes:
        choices.append((str(gc), gc.diff_text))
    for dp in diff_files:
        try:
            display = dp.relative_to(Path.cwd())
        except ValueError:
            display = dp
        choices.append((f"{display}", dp.read_text(encoding="utf-8")))

    _print_welcome(console, project_path, choices, has_git=is_git_repo(project_path))

    # If there's exactly one git change, auto-offer to analyze it
    if len(git_changes) == 1 and not diff_files:
        gc = git_changes[0]
        console.print(f"\n[bold cyan]Detected:[/bold cyan] {gc}")
        auto = prompt("Analyze now? [Y/n]: ").strip().lower()
        if auto in {"", "y", "yes"}:
            session.last_diff_text = gc.diff_text
            report = analyze(gc.diff_text, session.current_project or ".")
            session.last_report = report
            session.last_report_id = f"report-{len(report.changed_symbols)}-{len(report.affected_symbols)}"
            render_cli_report(report, console=console)
            _show_action_menu(console, report, session.current_project or ".")

    while True:
        user_input = prompt("impact-tracer> ").strip()
        if user_input.lower() in {"exit", "quit"}:
            console.print("Bye.")
            return None
        if not user_input:
            continue
        if user_input.lower() in {"help", "?", "menu"}:
            _print_help(console)
            continue

        # --- Numeric shortcut to pick from unified list ---
        if user_input.isdigit() and choices:
            idx = int(user_input)
            if 1 <= idx <= len(choices):
                label, diff_text = choices[idx - 1]
                console.print(f"[cyan]Analyzing:[/cyan] {label}")
                session.last_diff_text = diff_text
                report = analyze(diff_text, session.current_project or ".")
                session.last_report = report
                session.last_report_id = f"report-{len(report.changed_symbols)}-{len(report.affected_symbols)}"
                render_cli_report(report, console=console)
                _show_action_menu(console, report, session.current_project or ".")
                continue
            else:
                console.print(f"[yellow]Pick 1-{len(choices)}.[/yellow]")
                continue

        session.last_query = user_input
        intent = parse_intent(user_input)
        operation = intent.get("operation", "analyze_diff")
        session.last_operation = operation

        # --- show_graph: use last report if available ---
        if operation == "show_graph":
            if session.last_report is not None:
                graph_path = generate_interactive_graph(session.last_report, output_path="graph.html")
            else:
                report = analyze("", session.current_project or ".", enable_llm=False)
                graph_path = generate_interactive_graph(report, output_path="graph.html")
            console.print(f"[green]Graph saved → {graph_path}[/green]")
            _open_file(graph_path)
            continue

        # --- expand / show full report ---
        if operation == "expand_last_report":
            if session.last_report is None:
                console.print("[yellow]No previous report. Analyze a diff first.[/yellow]")
            else:
                render_cli_report(session.last_report, console=console)
            continue

        # --- get_risk_score ---
        if operation == "get_risk_score":
            symbol_id = intent.get("symbol", "")
            if session.last_report is None:
                console.print("[yellow]No previous report. Analyze a diff first.[/yellow]")
                continue
            found = False
            for item in session.last_report.affected_symbols:
                if item.symbol.id == symbol_id or item.symbol.name == symbol_id:
                    console.print(f"[bold]{item.symbol.id}[/bold]: risk={item.risk_score:.3f} ({item.risk_level.value}), depth={item.propagation_depth}")
                    found = True
                    break
            if not found:
                console.print(f"[yellow]Symbol '{symbol_id}' not found in affected symbols.[/yellow]")
                available = [s.symbol.id for s in session.last_report.affected_symbols]
                if available:
                    console.print(f"[dim]Available: {', '.join(available)}[/dim]")
            continue

        # --- query_dependencies ---
        if operation == "query_dependencies":
            if session.last_report is None:
                console.print("[yellow]No previous report. Analyze a diff first.[/yellow]")
                continue
            console.print("[bold]Propagation Paths:[/bold]")
            for path_info in session.last_report.propagation_paths:
                console.print(f"  {' → '.join(path_info.path)}")
            if not session.last_report.propagation_paths:
                console.print("  (no propagation paths)")
            continue

        # --- describe_change: NL → diff via LLM → analysis ---
        if operation == "describe_change":
            console.print("[dim]Generating diff from your description...[/dim]")
            generator = DiffGenerator()
            diff_text = generator.generate(user_input, session.current_project or ".")
            if not diff_text:
                console.print("[red]Could not generate diff. Check OpenAI API key or rephrase.[/red]")
                continue
            console.print("[green]Diff generated:[/green]")
            _print_diff_preview(console, diff_text)
            console.print()

            session.last_diff_text = diff_text
            report = analyze(diff_text, session.current_project or ".")
            session.last_report = report
            session.last_report_id = f"report-{len(report.changed_symbols)}-{len(report.affected_symbols)}"
            render_cli_report(report, console=console)
            _show_action_menu(console, report, session.current_project or ".")
            continue

        # --- analyze_diff ---
        diff_text = _resolve_diff_text(user_input)
        if diff_text:
            session.last_diff_text = diff_text
        elif session.last_diff_text:
            diff_text = session.last_diff_text
            console.print("[dim]Using previously loaded diff.[/dim]")
        else:
            console.print("[yellow]No diff found. Provide a .diff path, describe a change, or type 'help'.[/yellow]")
            continue

        report = analyze(diff_text, session.current_project or ".")
        session.last_report = report
        session.last_report_id = f"report-{len(report.changed_symbols)}-{len(report.affected_symbols)}"
        render_cli_report(report, console=console)
        _show_action_menu(console, report, session.current_project or ".")

    return None


# ── Helpers ──────────────────────────────────────────────────────────

def _print_welcome(console: Console, project_path: str, choices: list[tuple[str, str | None]], has_git: bool = False) -> None:
    """Print welcome banner with auto-detected changes."""
    banner = (
        "[bold cyan]Impact Tracer[/bold cyan]\n"
        f"Project: [white]{project_path}[/white]"
    )
    if has_git:
        banner += "  [dim](git repo detected)[/dim]"
    banner += "\n\n"

    if choices:
        banner += "[bold]Detected changes:[/bold]\n"
        for i, (label, _) in enumerate(choices, 1):
            banner += f"  [bold yellow]{i}[/bold yellow]  {label}\n"
        banner += "\n[dim]Type a number to analyze, describe a change in English, or type help.[/dim]\n"
    else:
        if has_git:
            banner += "[dim]No uncommitted changes detected. Describe a change or type help.[/dim]\n"
        else:
            banner += "[dim]Not a git repo. Describe a change in English or type help.[/dim]\n"

    banner += (
        "  • Type [bold]help[/bold] for all commands\n"
        "  • Type [bold]exit[/bold] to quit"
    )
    console.print(Panel(banner, border_style="cyan"))


def _print_help(console: Console) -> None:
    """Print help text."""
    help_text = (
        "[bold cyan]Commands:[/bold cyan]\n\n"
        "  [bold]<number>[/bold]                   Pick a detected change to analyze\n"
        "  [bold]I want to change ...[/bold]      Describe change in English (LLM generates diff)\n"
        "  [bold]show graph[/bold]                 Open interactive dependency graph\n"
        "  [bold]show report[/bold]                Re-display last analysis\n"
        "  [bold]risk score for <symbol>[/bold]    Get risk for a specific symbol\n"
        "  [bold]who depends on this[/bold]        Show propagation paths\n"
        "  [bold]<path>.diff[/bold]               Analyze a diff file (manual fallback)\n"
        "  [bold]help[/bold]                       Show this help\n"
        "  [bold]exit[/bold]                       Quit"
    )
    console.print(Panel(help_text, border_style="dim"))


def _print_diff_preview(console: Console, diff_text: str, max_lines: int = 20) -> None:
    """Print color-coded diff preview."""
    diff_lines = diff_text.strip().split("\n")
    for line in diff_lines[:max_lines]:
        if line.startswith("+") and not line.startswith("+++"):
            console.print(f"[green]{line}[/green]")
        elif line.startswith("-") and not line.startswith("---"):
            console.print(f"[red]{line}[/red]")
        else:
            console.print(f"[dim]{line}[/dim]")
    if len(diff_lines) > max_lines:
        console.print(f"[dim]... ({len(diff_lines) - max_lines} more lines)[/dim]")


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
