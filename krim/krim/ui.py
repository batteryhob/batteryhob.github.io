"""Terminal UI - banner, input, completions.

Uses prompt_toolkit for input (history, multiline paste, slash command completion).
Uses rich for all output (streaming, panels, colors).
"""

from __future__ import annotations

from rich.console import Console
from rich.text import Text

from krim import __version__

console = Console()

# -- banner --

_FACE = [
    "",
    "  ●     ●",
    " ▄██▄ ▄██▄",
    "  ▀▀   ▀▀",
    "",
    "",
]

_TEXT = [
    " ██╗  ██╗██████╗ ██╗███╗   ███╗",
    " ██║ ██╔╝██╔══██╗██║████╗ ████║",
    " █████╔╝ ██████╔╝██║██╔████╔██║",
    " ██╔═██╗ ██╔══██╗██║██║╚██╔╝██║",
    " ██║  ██╗██║  ██║██║██║ ╚═╝ ██║",
    " ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝╚═╝     ╚═╝",
]

_FACE_W = 13
LOGO_LINES = [f"{f:{_FACE_W}s}{t}" for f, t in zip(_FACE, _TEXT)]

TAGLINE = "trust the model, keep the harness light."

SLASH_COMMANDS = ["/help", "/tokens", "/compact", "/config", "/undo", "/verbose"]


def print_banner(provider: str, model_name: str, max_turns: int, project_dir: str | None = None):
    """Print the welcome banner with config info."""
    for line in LOGO_LINES:
        console.print(f"[bold cyan]{line}[/]", highlight=False)
    console.print(f"  [dim italic]{TAGLINE}[/]")
    console.print()

    info = Text()
    info.append("  v", style="dim")
    info.append(__version__, style="bold")
    info.append("  │  ", style="dim")
    info.append(provider, style="bold green")
    info.append("/", style="dim")
    info.append(model_name, style="green")
    info.append("  │  ", style="dim")
    info.append(f"max_turns={max_turns}", style="dim")
    console.print(info)

    if project_dir:
        console.print(f"  [dim]config: {project_dir}[/]")

    console.print(f"  [dim]type /help for commands, 'exit' to quit[/]")
    console.print()


def print_banner_oneliner(provider: str, model_name: str, max_turns: int):
    """Compact one-line header for single-prompt mode."""
    console.print(f"[bold cyan]krim[/] v{__version__}  [dim]{provider}/{model_name}  max_turns={max_turns}[/]")


# -- input with prompt_toolkit --

def create_session():
    """Create a prompt_toolkit session with history and completions."""
    try:
        from prompt_toolkit import PromptSession
        from prompt_toolkit.history import InMemoryHistory
        from prompt_toolkit.completion import WordCompleter
        from prompt_toolkit.styles import Style

        style = Style.from_dict({
            "prompt": "bold green",
        })

        completer = WordCompleter(
            SLASH_COMMANDS + ["exit", "quit"],
            sentence=True,  # complete full words
        )

        session = PromptSession(
            history=InMemoryHistory(),
            completer=completer,
            style=style,
            complete_while_typing=False,
            enable_history_search=True,
            multiline=False,
        )
        return session
    except ImportError:
        return None


def prompt_input(session=None) -> str | None:
    """Get user input. Returns None on EOF/interrupt."""
    if session:
        try:
            from prompt_toolkit.formatted_text import HTML
            text = session.prompt(HTML("<prompt>&gt; </prompt>"))
            return text
        except (EOFError, KeyboardInterrupt):
            return None
    else:
        # fallback to rich
        try:
            return console.input("[bold green]> [/]")
        except (EOFError, KeyboardInterrupt):
            return None
