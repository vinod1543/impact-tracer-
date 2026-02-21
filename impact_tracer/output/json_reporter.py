"""JSON report renderer.

Layer: Interfaces/Output (Layer 5)
Responsibility: Serialize ImpactReport into JSON output.
"""

from __future__ import annotations

from pathlib import Path

from impact_tracer.models.report import ImpactReport


def render_json_report(report: ImpactReport) -> str:
	"""Render impact report as pretty JSON string.

	Args:
		report: Structured impact report.

	Returns:
		str: JSON content.
	"""
	return report.model_dump_json(indent=2)


def write_json_report(report: ImpactReport, output_path: str) -> str:
	"""Write report JSON to output file.

	Args:
		report: Structured impact report.
		output_path: Output path.

	Returns:
		str: Output path.
	"""
	payload = render_json_report(report)
	target = Path(output_path)
	target.parent.mkdir(parents=True, exist_ok=True)
	target.write_text(payload, encoding="utf-8")
	return str(target)
