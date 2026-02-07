"""Bash execution tool with safety checks, persistent cwd, and output truncation."""

from __future__ import annotations

import os
import subprocess

from krim.tools.base import Tool
from krim.safety import Action, check_command, prompt_user
from krim.truncate import truncate

_CWD_MARKER = "__KRIM_CWD__"


class BashTool(Tool):
    name = "bash"
    description = "Run a shell command. Returns stdout and stderr. Working directory persists between calls."
    parameters = {
        "command": {"type": "string", "description": "Shell command to execute"},
        "timeout": {"type": "integer", "description": "Timeout in seconds (default 120)", "optional": True},
    }

    def __init__(self):
        self._deny_patterns: list[str] = []
        self._allow_commands: list[str] = []
        self._ask_by_default: bool = True
        self._max_output_chars: int = 30_000
        self._cwd: str = os.getcwd()

    def configure(
        self,
        deny_patterns: list[str],
        allow_commands: list[str],
        ask_by_default: bool = True,
        max_output_chars: int = 30_000,
        cwd: str | None = None,
    ):
        self._deny_patterns = deny_patterns
        self._allow_commands = allow_commands
        self._ask_by_default = ask_by_default
        self._max_output_chars = max_output_chars
        if cwd:
            self._cwd = cwd

    @property
    def cwd(self) -> str:
        return self._cwd

    def run(self, command: str, timeout: int = 120) -> str:
        # safety check
        action = check_command(
            command, self._deny_patterns, self._allow_commands, self._ask_by_default,
        )

        if action == Action.DENY:
            return f"error: command denied by safety rules: {command}"

        if action == Action.ASK:
            if not prompt_user(command):
                return "error: command rejected by user"

        # wrap command to: 1) capture its exit code, 2) track cwd changes, 3) exit with original code
        wrapped = f'{command}\n__krim_ec=$?\necho "{_CWD_MARKER}"\npwd\nexit $__krim_ec'

        try:
            result = subprocess.run(
                wrapped,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=self._cwd,
            )

            stdout = result.stdout or ""

            # extract and update cwd from the marker
            if _CWD_MARKER in stdout:
                parts = stdout.rsplit(_CWD_MARKER, 1)
                stdout = parts[0]
                new_cwd = parts[1].strip()
                if new_cwd and os.path.isdir(new_cwd):
                    self._cwd = new_cwd

            out = ""
            if stdout.strip():
                out += stdout.strip()
            if result.stderr:
                if out:
                    out += "\n"
                out += result.stderr.strip()
            if result.returncode != 0:
                out += f"\n[exit code: {result.returncode}]"

            out = out.strip() or "(no output)"
            return truncate(out, self._max_output_chars)

        except subprocess.TimeoutExpired:
            return f"error: command timed out after {timeout}s"
        except Exception as e:
            return f"error: {e}"
