"""CLI session model stub."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class CliSession(BaseModel):
    """State container for an interactive CLI session."""

    current_project: str | None = None
    last_diff: str | None = None
    last_diff_text: str | None = None
    last_report: Any | None = None
    last_report_id: str | None = None
    last_query: str | None = None
    last_operation: str | None = None
