"""Edit file tool - exact string replacement."""

import os
from krim.tools.base import Tool


class EditTool(Tool):
    name = "edit"
    description = "Replace an exact string in a file with new content."
    parameters = {
        "path": {"type": "string", "description": "File path to edit"},
        "old": {"type": "string", "description": "Exact string to find"},
        "new": {"type": "string", "description": "Replacement string"},
    }

    def run(self, path: str, old: str, new: str) -> str:
        path = os.path.expanduser(path)
        if not os.path.isfile(path):
            return f"error: {path} not found"
        try:
            with open(path, "r") as f:
                content = f.read()
            count = content.count(old)
            if count == 0:
                return "error: old string not found in file"
            if count > 1:
                return f"error: old string found {count} times, must be unique"
            content = content.replace(old, new, 1)
            with open(path, "w") as f:
                f.write(content)
            return f"edited {path}"
        except Exception as e:
            return f"error: {e}"
