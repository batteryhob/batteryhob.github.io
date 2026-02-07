"""Write file tool."""

from __future__ import annotations

import os

from krim.tools.base import Tool


class WriteTool(Tool):
    name = "write"
    description = "Write content to a file. Creates parent directories if needed."
    parameters = {
        "path": {"type": "string", "description": "File path to write"},
        "content": {"type": "string", "description": "Content to write"},
    }

    def run(self, path: str, content: str) -> str:
        path = os.path.expanduser(path)
        try:
            parent = os.path.dirname(path)
            if parent:
                os.makedirs(parent, exist_ok=True)
            with open(path, "w") as f:
                f.write(content)
            lines = content.count("\n") + (1 if content and not content.endswith("\n") else 0)
            return f"wrote {path} ({lines} lines)"
        except Exception as e:
            return f"error: {e}"
