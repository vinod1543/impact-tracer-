"""Rich CLI report renderer.

Layer: Interfaces/Output (Layer 5)
Responsibility: Render readable risk-ranked terminal report.
"""

from __future__ import annotations

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from impact_tracer.models.impact import RiskLevel
from impact_tracer.models.report import ImpactReport


def render_cli_report(report: ImpactReport, console: Console | None = None) -> None:
	"""Render impact report to terminal using rich tables and panels.

	Args:
		report: Structured impact report.
		console: Optional rich console.
	"""
	console = console or Console()

	header = (
		f"Project: {report.project_path}\n"
		f"Overall Risk: {report.overall_risk.level.value} ({report.overall_risk.value:.2f})\n"
		f"Confidence: {report.confidence.value}"
	)
	console.print(Panel(header, title="Impact Tracer", border_style="cyan"))

	changed_table = Table(title="Changed Symbols", show_header=True, header_style="bold magenta")
	changed_table.add_column("Symbol")
	changed_table.add_column("Change Type")
	for item in report.changed_symbols:
		changed_table.add_row(item.symbol_id, item.change_type.value)
	if not report.changed_symbols:
		changed_table.add_row("(none)", "-")
	console.print(changed_table)

	affected_table = Table(title="Affected Symbols (Ranked)", show_header=True, header_style="bold green")
	affected_table.add_column("Risk")
	affected_table.add_column("Symbol")
	affected_table.add_column("Score")
	affected_table.add_column("Depth")

	sorted_affected = sorted(report.affected_symbols, key=lambda node: node.risk_score, reverse=True)
	for item in sorted_affected:
		affected_table.add_row(
			_risk_badge(item.risk_level),
			item.symbol.id,
			f"{item.risk_score:.2f}",
			str(item.propagation_depth),
		)
	if not report.affected_symbols:
		affected_table.add_row("LOW", "(none)", "0.00", "0")
	console.print(affected_table)

	if report.explanation is not None:
		def _lines(items: list[str]) -> str:
			return "\n".join([f"- {item}" for item in items]) if items else "- (none)"

		explanation = (
			f"Summary: {report.explanation.summary}\n\n"
			f"Blast Radius: {report.explanation.blast_radius}\n\n"
			"Impacted APIs:\n"
			f"{_lines(report.explanation.impacted_apis)}\n\n"
			"Impacted Modules/Functions:\n"
			f"{_lines(report.explanation.impacted_modules_or_functions)}\n\n"
			"Downstream Dependencies:\n"
			f"{_lines(report.explanation.downstream_dependencies)}\n\n"
			"Known Impact Zones:\n"
			f"{_lines(report.explanation.known_impact_zones)}\n\n"
			"Unknown Impact Zones:\n"
			f"{_lines(report.explanation.unknown_impact_zones)}\n\n"
			"High-Risk/Uncertain Areas:\n"
			f"{_lines(report.explanation.high_risk_or_uncertain_areas)}\n\n"
			"Recommended Actions:\n"
			+ "\n".join([f"- {action}" for action in report.explanation.recommended_actions])
		)
		console.print(Panel(explanation, title="LLM Explanation", border_style="yellow"))


def _risk_badge(level: RiskLevel) -> str:
	if level == RiskLevel.CRITICAL:
		return "[red]CRITICAL[/red]"
	if level == RiskLevel.HIGH:
		return "[yellow]HIGH[/yellow]"
	if level == RiskLevel.MEDIUM:
		return "[blue]MEDIUM[/blue]"
	return "[green]LOW[/green]"
