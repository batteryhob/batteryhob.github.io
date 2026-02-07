"""Read file tool with line number support."""

from __future__ import annotations

import os

from krim.tools.base import Tool


class ReadTool(Tool):
    name = "read"
    description = "Read a file. Returns contents with line numbers. Supports offset and limit for large files."
    parameters = {
        "path": {"type": "string", "description": "File path to read"},
        "offset": {"type": "integer", "description": "Start from this line (1-indexed)", "optional": True},
        "limit": {"type": "integer", "description": "Max lines to return", "optional": True},
    }

    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

    def run(self, path: str, offset: int = 1, limit: int = 2000) -> str:
        path = os.path.expanduser(path)
        if not os.path.isfile(path):
            return f"error: {path} not found"
        try:
            size = os.path.getsize(path)
            if size > self.MAX_FILE_SIZE:
                return f"error: {path} is too large ({size // 1024 // 1024}MB). use offset/limit or bash to read portions."
            with open(path, "r") as f:
                lines = f.readlines()

            total = len(lines)
            start = max(0, offset - 1)
            end = min(total, start + limit)
            selected = lines[start:end]

            numbered = []
            for i, line in enumerate(selected, start=start + 1):
                numbered.append(f"{i:>4}\t{line.rstrip()}")

            result = "\n".join(numbered)
            if end < total:
                result += f"\n... ({total - end} more lines, {total} total)"

            return result
        except UnicodeDecodeError:
            return f"error: {path} is a binary file"
        except Exception as e:
            return f"error: {e}"
