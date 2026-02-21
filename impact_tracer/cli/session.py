"""CLI session model stub."""

from pydantic import BaseModel


class CliSession(BaseModel):
    """State container for an interactive CLI session."""

    current_project: str | None = None
    last_diff: str | None = None
    last_report_id: str | None = None
