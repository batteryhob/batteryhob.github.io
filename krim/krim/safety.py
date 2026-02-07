"""Safety module - deny/ask/allow rules for bash commands.

Rules evaluated in order: deny > allow > ask (default).
"""

from __future__ import annotations

from enum import Enum
from rich.console import Console

console = Console()


class Action(Enum):
    ALLOW = "allow"
    DENY = "deny"
    ASK = "ask"


def check_command(
    command: str,
    deny_patterns: list[str],
    allow_commands: list[str],
    ask_by_default: bool = True,
) -> Action:
    """Evaluate a bash command against safety rules.

    Order: deny > allow > ask_by_default.
    """
    cmd_lower = command.strip().lower()

    # 1. deny patterns - block dangerous commands
    for pattern in deny_patterns:
        if pattern.lower() in cmd_lower:
            return Action.DENY

    # 2. allow list - auto-approve safe commands (word boundary check)
    for allowed in allow_commands:
        al = allowed.lower()
        if cmd_lower == al or cmd_lower.startswith(al + " ") or cmd_lower.startswith(al + "\t"):
            return Action.ALLOW

    # 3. default
    return Action.ASK if ask_by_default else Action.ALLOW


def prompt_user(command: str) -> bool:
    """Ask the user for approval to run a command.

    In non-interactive mode (stdin not a tty), defaults to deny.
    """
    import sys
    if not sys.stdin.isatty():
        console.print(f"[yellow]bash: auto-denied (non-interactive):[/] {command}")
        return False
    console.print(f"\n[yellow]bash:[/] [bold]{command}[/]")
    try:
        answer = console.input("[yellow]allow? [y/N] [/]").strip().lower()
        return answer in ("y", "yes")
    except (EOFError, KeyboardInterrupt):
        console.print()
        return False
