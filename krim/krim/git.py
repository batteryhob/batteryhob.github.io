"""Git integration - auto-commit and undo.

Philosophy: every AI edit gets its own commit, so the user can always `git reset HEAD^` to undo.
Dirty files are committed separately first to keep human and AI changes distinct.
"""

from __future__ import annotations

import subprocess
from rich.console import Console

console = Console()


def _run_git(*args: str, check: bool = False) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args],
        capture_output=True, text=True, timeout=10,
        check=check,
    )


def is_git_repo() -> bool:
    result = _run_git("rev-parse", "--is-inside-work-tree")
    return result.returncode == 0


def has_uncommitted_changes() -> bool:
    result = _run_git("status", "--porcelain")
    return bool(result.stdout.strip())


def get_dirty_files() -> list[str]:
    result = _run_git("status", "--porcelain")
    files = []
    for line in result.stdout.strip().splitlines():
        if line.strip():
            # porcelain format: XY filename
            files.append(line[3:].strip())
    return files


def _stage_tracked_changes():
    """Stage only tracked file changes + new files, skipping common sensitive patterns."""
    # stage modified/deleted tracked files
    _run_git("add", "-u")
    # stage new files but exclude sensitive patterns
    dirty = get_dirty_files()
    skip = {".env", ".env.local", ".env.production", "credentials.json", "secrets.json",
            ".DS_Store", "node_modules", "__pycache__"}
    for f in dirty:
        basename = f.rsplit("/", 1)[-1] if "/" in f else f
        if basename in skip or f.startswith(".env"):
            continue
        _run_git("add", "--", f)


def commit_dirty(message: str = "krim: save uncommitted changes before agent edits") -> bool:
    """Commit any uncommitted changes to protect the user's work."""
    if not has_uncommitted_changes():
        return False
    _stage_tracked_changes()
    result = _run_git("commit", "-m", message)
    if result.returncode == 0:
        console.print(f"[dim]git: committed dirty files: {message}[/]")
        return True
    return False


def auto_commit(message: str = "krim: agent edits") -> bool:
    """Commit current changes with a descriptive message."""
    if not is_git_repo() or not has_uncommitted_changes():
        return False
    _stage_tracked_changes()
    result = _run_git("commit", "-m", message)
    if result.returncode == 0:
        short_hash = _run_git("rev-parse", "--short", "HEAD").stdout.strip()
        console.print(f"[dim]git: committed {short_hash} - {message}[/]")
        return True
    return False


def undo() -> bool:
    """Undo the last commit (git reset HEAD^). Only works on krim commits."""
    if not is_git_repo():
        console.print("[red]not a git repo[/]")
        return False

    # check that last commit is from krim
    result = _run_git("log", "-1", "--format=%s")
    last_msg = result.stdout.strip()
    if not last_msg.startswith("krim:"):
        console.print(f"[yellow]last commit is not a krim commit: {last_msg}[/]")
        return False

    result = _run_git("reset", "HEAD^")
    if result.returncode == 0:
        console.print(f"[dim]git: undid commit: {last_msg}[/]")
        return True

    console.print(f"[red]git reset failed: {result.stderr}[/]")
    return False
