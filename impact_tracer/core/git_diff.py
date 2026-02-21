"""Git integration – pull diffs directly from the repository.

Eliminates the need for users to manually create or locate .diff files.
Supports unstaged changes, staged changes, and branch comparisons.
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass
class GitChange:
    """A detected change source from git."""

    label: str  # human-readable label
    diff_text: str  # unified diff content
    file_count: int  # number of files changed
    source: str  # "unstaged" | "staged" | "branch" | "commit"

    def __str__(self) -> str:
        return f"{self.label} ({self.file_count} file{'s' if self.file_count != 1 else ''})"


def _run_git(args: list[str], cwd: str | None = None) -> str | None:
    """Run a git command and return stdout, or None on failure."""
    try:
        result = subprocess.run(
            ["git"] + args,
            capture_output=True,
            text=True,
            cwd=cwd,
            timeout=15,
        )
        if result.returncode == 0:
            return result.stdout
        return None
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        return None


def is_git_repo(project_path: str) -> bool:
    """Check if the project is inside a git repository."""
    return _run_git(["rev-parse", "--is-inside-work-tree"], cwd=project_path) is not None


def get_repo_root(project_path: str) -> str | None:
    """Get the root of the git repository."""
    result = _run_git(["rev-parse", "--show-toplevel"], cwd=project_path)
    return result.strip() if result else None


def _count_files(diff_text: str) -> int:
    """Count the number of files in a unified diff."""
    return sum(1 for line in diff_text.splitlines() if line.startswith("+++ "))


def get_unstaged_diff(project_path: str) -> GitChange | None:
    """Get diff of unstaged (working tree) changes."""
    diff = _run_git(["diff", "--unified=3", "--", "*.py"], cwd=project_path)
    if diff and diff.strip():
        fc = _count_files(diff)
        return GitChange(
            label="Unstaged changes (working tree)",
            diff_text=diff,
            file_count=fc,
            source="unstaged",
        )
    return None


def get_staged_diff(project_path: str) -> GitChange | None:
    """Get diff of staged (index) changes."""
    diff = _run_git(["diff", "--cached", "--unified=3", "--", "*.py"], cwd=project_path)
    if diff and diff.strip():
        fc = _count_files(diff)
        return GitChange(
            label="Staged changes (git add)",
            diff_text=diff,
            file_count=fc,
            source="staged",
        )
    return None


def get_branch_diff(project_path: str, base: str = "main") -> GitChange | None:
    """Get diff between current branch and a base branch.

    Tries 'main' first, then 'master' as fallback.
    """
    for branch in (base, "master") if base == "main" else (base,):
        # Check if branch exists
        check = _run_git(["rev-parse", "--verify", branch], cwd=project_path)
        if check is None:
            continue
        diff = _run_git(["diff", f"{branch}...HEAD", "--unified=3", "--", "*.py"], cwd=project_path)
        if diff and diff.strip():
            fc = _count_files(diff)
            current = _run_git(["rev-parse", "--abbrev-ref", "HEAD"], cwd=project_path)
            branch_name = current.strip() if current else "HEAD"
            return GitChange(
                label=f"Branch diff ({branch} → {branch_name})",
                diff_text=diff,
                file_count=fc,
                source="branch",
            )
    return None


def get_last_commit_diff(project_path: str) -> GitChange | None:
    """Get diff of the most recent commit."""
    diff = _run_git(["diff", "HEAD~1..HEAD", "--unified=3", "--", "*.py"], cwd=project_path)
    if diff and diff.strip():
        fc = _count_files(diff)
        # Get commit message for label
        msg = _run_git(["log", "-1", "--format=%s"], cwd=project_path)
        short_msg = (msg.strip()[:50] + "...") if msg and len(msg.strip()) > 50 else (msg.strip() if msg else "")
        return GitChange(
            label=f"Last commit: {short_msg}",
            diff_text=diff,
            file_count=fc,
            source="commit",
        )
    return None


def discover_git_changes(project_path: str) -> list[GitChange]:
    """Auto-discover all available git change sources.

    Returns a list of available changes, ordered by usefulness:
    1. Unstaged changes (most common use case)
    2. Staged changes
    3. Branch diff vs main/master
    4. Last commit
    """
    if not is_git_repo(project_path):
        return []

    changes: list[GitChange] = []

    unstaged = get_unstaged_diff(project_path)
    if unstaged:
        changes.append(unstaged)

    staged = get_staged_diff(project_path)
    if staged:
        changes.append(staged)

    branch = get_branch_diff(project_path)
    if branch:
        changes.append(branch)

    last = get_last_commit_diff(project_path)
    if last:
        changes.append(last)

    return changes
