"""Write file tool."""

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
            os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
            with open(path, "w") as f:
                f.write(content)
            return f"wrote {path}"
        except Exception as e:
            return f"error: {e}"
