"""Bash execution tool."""

import subprocess
from krim.tools.base import Tool


class BashTool(Tool):
    name = "bash"
    description = "Run a shell command. Returns stdout and stderr."
    parameters = {
        "command": {"type": "string", "description": "Shell command to execute"},
    }

    def run(self, command: str, timeout: int = 120) -> str:
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=None,
            )
            out = ""
            if result.stdout:
                out += result.stdout
            if result.stderr:
                out += result.stderr
            if result.returncode != 0:
                out += f"\n[exit code: {result.returncode}]"
            return out.strip() or "(no output)"
        except subprocess.TimeoutExpired:
            return f"error: command timed out after {timeout}s"
        except Exception as e:
            return f"error: {e}"
