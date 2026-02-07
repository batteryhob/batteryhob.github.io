"""Read file tool."""

import os
from krim.tools.base import Tool


class ReadTool(Tool):
    name = "read"
    description = "Read a file. Returns its contents."
    parameters = {
        "path": {"type": "string", "description": "File path to read"},
    }

    def run(self, path: str) -> str:
        path = os.path.expanduser(path)
        if not os.path.isfile(path):
            return f"error: {path} not found"
        try:
            with open(path, "r") as f:
                content = f.read()
            lines = content.splitlines()
            if len(lines) > 2000:
                return "\n".join(lines[:2000]) + f"\n... ({len(lines) - 2000} more lines)"
            return content
        except Exception as e:
            return f"error: {e}"
