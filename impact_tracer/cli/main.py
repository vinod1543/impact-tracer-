"""CLI entry point for Impact Tracer.

Layer: Interfaces (Layer 5)
Responsibility: Single-shot command and basic startup.
Implements: PRD terminal interface baseline for MVP scaffolding.
"""

from __future__ import annotations

import argparse


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI argument parser.

    Returns:
        argparse.ArgumentParser: Configured parser instance.
    """
    parser = argparse.ArgumentParser(prog="impact-tracer", description="Impact Tracer CLI")
    parser.add_argument("query", nargs="?", help="Natural language query")
    parser.add_argument("--project", default=".", help="Project path")
    parser.add_argument("--format", choices=["text", "json"], default="text", help="Output format")
    return parser


def main() -> int:
    """Run the CLI entry point.

    Returns:
        int: Exit code.
    """
    parser = build_parser()
    parser.parse_args()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
