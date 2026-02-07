"""Edit file tool with fuzzy matching fallback.

Match strategy (in order):
1. Exact match
2. Whitespace-normalized match
3. Fuzzy match (difflib, threshold 0.8)
"""

from __future__ import annotations

import difflib
import os
import re

from krim.tools.base import Tool


def _normalize_whitespace(text: str) -> str:
    """Collapse all whitespace to single spaces, strip lines."""
    return re.sub(r"\s+", " ", text).strip()


def _fuzzy_find(content: str, old: str, threshold: float = 0.8) -> tuple[int, int] | None:
    """Find the best fuzzy match for `old` in `content`.

    Returns (start, end) indices or None.
    """
    old_lines = old.splitlines()
    content_lines = content.splitlines()

    if not old_lines:
        return None

    best_ratio = 0.0
    best_start = -1
    window = len(old_lines)

    for i in range(len(content_lines) - window + 1):
        candidate = "\n".join(content_lines[i : i + window])
        ratio = difflib.SequenceMatcher(None, old, candidate).ratio()
        if ratio > best_ratio:
            best_ratio = ratio
            best_start = i

    if best_ratio < threshold:
        return None

    matched_text = "\n".join(content_lines[best_start : best_start + window])
    start = content.find(matched_text)
    if start == -1:
        return None
    return start, start + len(matched_text)


class EditTool(Tool):
    name = "edit"
    description = (
        "Replace a string in a file. Uses exact match first, "
        "falls back to fuzzy matching if exact match fails."
    )
    parameters = {
        "path": {"type": "string", "description": "File path to edit"},
        "old": {"type": "string", "description": "String to find (exact or fuzzy)"},
        "new": {"type": "string", "description": "Replacement string"},
    }

    def run(self, path: str, old: str, new: str) -> str:
        path = os.path.expanduser(path)
        if not os.path.isfile(path):
            return f"error: {path} not found"
        try:
            with open(path, "r") as f:
                content = f.read()

            # strategy 1: exact match
            count = content.count(old)
            if count == 1:
                content = content.replace(old, new, 1)
                with open(path, "w") as f:
                    f.write(content)
                return f"edited {path} (exact match)"

            if count > 1:
                return f"error: old string found {count} times, must be unique. provide more context."

            # strategy 2: whitespace-normalized match
            norm_old = _normalize_whitespace(old)
            lines = content.splitlines(keepends=True)
            for i in range(len(lines)):
                for length in range(1, min(len(old.splitlines()) + 3, len(lines) - i + 1)):
                    chunk = "".join(lines[i : i + length])
                    if _normalize_whitespace(chunk) == norm_old:
                        content = content.replace(chunk, new, 1)
                        with open(path, "w") as f:
                            f.write(content)
                        return f"edited {path} (whitespace-normalized match)"

            # strategy 3: fuzzy match
            match = _fuzzy_find(content, old)
            if match:
                start, end = match
                matched_text = content[start:end]
                ratio = difflib.SequenceMatcher(None, old, matched_text).ratio()
                content = content[:start] + new + content[end:]
                with open(path, "w") as f:
                    f.write(content)
                return f"edited {path} (fuzzy match, {ratio:.0%} similar)"

            return "error: old string not found in file (exact, whitespace, and fuzzy match all failed)"
        except Exception as e:
            return f"error: {e}"
