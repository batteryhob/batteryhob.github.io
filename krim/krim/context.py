"""Context injection - gather environment info for the system prompt.

Injects: cwd, git status, project file tree.
Keeps it compact. The model doesn't need a full repo dump.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path


def get_cwd() -> str:
    return os.getcwd()


def get_git_info() -> str | None:
    """Get compact git context: branch, status summary, recent commits."""
    try:
        branch = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True, text=True, timeout=5,
        )
        if branch.returncode != 0:
            return None

        status = subprocess.run(
            ["git", "status", "--short"],
            capture_output=True, text=True, timeout=5,
        )

        log = subprocess.run(
            ["git", "log", "--oneline", "-5"],
            capture_output=True, text=True, timeout=5,
        )

        parts = [f"branch: {branch.stdout.strip()}"]
        if status.stdout.strip():
            lines = status.stdout.strip().splitlines()
            if len(lines) > 10:
                parts.append(f"changes: {len(lines)} files modified (showing first 10)")
                parts.append("\n".join(lines[:10]))
            else:
                parts.append(f"changes:\n{status.stdout.strip()}")
        else:
            parts.append("changes: clean")

        if log.stdout.strip():
            parts.append(f"recent commits:\n{log.stdout.strip()}")

        return "\n".join(parts)
    except Exception:
        return None


def get_project_tree(max_files: int = 50, max_depth: int = 3) -> str:
    """Get a compact project file tree. Respects .gitignore via git ls-files."""
    try:
        # try git ls-files first (respects .gitignore)
        result = subprocess.run(
            ["git", "ls-files"],
            capture_output=True, text=True, timeout=5,
        )
        if result.returncode == 0 and result.stdout.strip():
            files = result.stdout.strip().splitlines()
            # filter by depth
            filtered = [f for f in files if f.count("/") < max_depth]
            if len(filtered) > max_files:
                return "\n".join(filtered[:max_files]) + f"\n... ({len(filtered) - max_files} more files)"
            return "\n".join(filtered)
    except Exception:
        pass

    # fallback: basic os.walk
    cwd = Path.cwd()
    files = []
    skip = {".git", "node_modules", "__pycache__", ".venv", "venv", ".tox", "dist", "build"}
    for root, dirs, filenames in os.walk(cwd):
        dirs[:] = [d for d in dirs if d not in skip]
        depth = Path(root).relative_to(cwd).parts
        if len(depth) >= max_depth:
            dirs.clear()
            continue
        for f in filenames:
            rel = os.path.relpath(os.path.join(root, f), cwd)
            files.append(rel)
            if len(files) >= max_files:
                break
        if len(files) >= max_files:
            break

    if not files:
        return "(empty directory)"
    return "\n".join(files)


def build_context() -> str:
    """Build the full context string for prompt injection."""
    parts = [f"cwd: {get_cwd()}"]

    git = get_git_info()
    if git:
        parts.append(f"git:\n{git}")

    tree = get_project_tree()
    parts.append(f"project files:\n{tree}")

    return "\n\n".join(parts)
