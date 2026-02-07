"""krim - thin CLI agent. trust the model, keep the harness light.

Usage:
  krim "fix the bug in main.py"
  krim --provider claude --model claude-sonnet-4-5-20250929 "refactor this"
  krim --provider openai --model gpt-4o "add tests"
  krim --max-turns 20 "big refactor task"
  krim --skill deploy "ship it"
  krim --auto-commit "fix and commit"
  krim                         # interactive mode
"""

from __future__ import annotations

import argparse
import atexit
import sys

from rich.console import Console

from krim import __version__
from krim.config import load_config, KrimConfig
from krim.models import create_model, DEFAULT_MODELS
from krim.agent import Agent
from krim.tools import create_tools, get_tool
from krim.tools.bash import BashTool
from krim.mcp import load_mcp_config, start_mcp_servers
from krim.skills import discover_skills, inject_skill
from krim.prompt import build_system_prompt
from krim.git import is_git_repo, commit_dirty, auto_commit, undo
from krim.ui import print_banner, print_banner_oneliner, create_session, prompt_input

console = Console()


def _handle_slash_command(cmd: str, agent: Agent, config: KrimConfig, verbose: bool):
    """Handle interactive slash commands."""
    parts = cmd.split(maxsplit=1)
    command = parts[0].lower()

    if command == "/help":
        console.print(
            "[bold]Commands:[/]\n"
            "  /help      - show this help\n"
            "  /tokens    - show token usage\n"
            "  /compact   - force context compaction\n"
            "  /config    - show current config\n"
            "  /undo      - undo last krim commit\n"
            "  /verbose   - toggle verbose mode\n"
            "  exit       - quit interactive mode"
        )
    elif command == "/tokens":
        from krim.compaction import estimate_message_tokens
        tokens = estimate_message_tokens(agent.messages)
        console.print(f"[dim]messages: {len(agent.messages)} | ~{tokens:,} tokens[/]")
        console.print(f"[dim]total turns: {agent.total_turns} | total tool calls: {agent.total_tool_calls}[/]")
    elif command == "/compact":
        agent.force_compact()
    elif command == "/config":
        console.print(f"[dim]provider: {config.provider}[/]")
        console.print(f"[dim]model: {config.model or 'default'}[/]")
        console.print(f"[dim]max_turns: {config.max_turns}[/]")
        console.print(f"[dim]auto_commit: {config.auto_commit}[/]")
        console.print(f"[dim]safety: {'ask' if config.ask_by_default else 'off'}[/]")
        console.print(f"[dim]global_dir: {config.global_dir}[/]")
        console.print(f"[dim]project_dir: {config.project_dir or 'none'}[/]")
        if config.krim_md:
            console.print(f"[dim]KRIM.md: {len(config.krim_md)} chars[/]")
        if config.rules:
            console.print(f"[dim]rules: {len(config.rules)} loaded[/]")
    elif command == "/undo":
        undo()
    elif command == "/verbose":
        agent.verbose = not agent.verbose
        console.print(f"[dim]verbose: {'on' if agent.verbose else 'off'}[/]")
    else:
        console.print(f"[dim]unknown command: {command}. try /help[/]")


def parse_args():
    p = argparse.ArgumentParser(
        prog="krim",
        description="Thin CLI agent. Trust the model, keep the harness light.",
    )
    p.add_argument("prompt", nargs="?", help="task to perform (omit for interactive mode)")
    p.add_argument("--provider", "-p", default=None, choices=["claude", "openai"],
                   help="model provider (default: from config or claude)")
    p.add_argument("--model", "-m", default=None,
                   help="model name (default: provider's default)")
    p.add_argument("--max-turns", "-t", type=int, default=None,
                   help="max agent turns (default: from config or 10)")
    p.add_argument("--skill", "-s", default=None,
                   help="activate a skill by name")
    p.add_argument("--list-skills", action="store_true",
                   help="list available skills")
    p.add_argument("--no-mcp", action="store_true",
                   help="disable MCP servers")
    p.add_argument("--auto-commit", action="store_true", default=None,
                   help="auto-commit after agent edits")
    p.add_argument("--no-safety", action="store_true",
                   help="disable bash safety prompts (auto-allow all)")
    p.add_argument("--verbose", action="store_true",
                   help="show debug info (token counts, config details)")
    p.add_argument("--version", "-v", action="version", version=f"krim {__version__}")
    return p.parse_args()


def main():
    args = parse_args()

    # load layered config
    config = load_config()

    # CLI flags override config
    provider = args.provider or config.provider
    model_name = args.model or config.model or DEFAULT_MODELS.get(provider, "gpt-4o")
    max_turns = args.max_turns if args.max_turns is not None else config.max_turns
    do_auto_commit = args.auto_commit if args.auto_commit is not None else config.auto_commit

    verbose = args.verbose
    if args.no_safety:
        config.ask_by_default = False

    # list skills
    if args.list_skills:
        skills = discover_skills(config.global_dir, config.project_dir)
        if not skills:
            console.print("[dim]no skills found. add them to ~/.krim/skills/ or .krim/skills/[/]")
        for name, skill in skills.items():
            first_line = skill.prompt.strip().splitlines()[0] if skill.prompt.strip() else ""
            console.print(f"  [bold]{name}[/]  {first_line}")
        return

    # header - full banner for interactive, one-liner for single prompt
    is_interactive = args.prompt is None
    if is_interactive:
        print_banner(provider, model_name, max_turns, str(config.project_dir) if config.project_dir else None)
    else:
        print_banner_oneliner(provider, model_name, max_turns)
        if config.project_dir:
            console.print(f"[dim]config: {config.project_dir}[/]")
    if verbose:
        console.print(f"[dim]verbose: on | safety: {'ask' if config.ask_by_default else 'off'}[/]")
        console.print(f"[dim]deny_patterns: {len(config.deny_patterns)} | allow_commands: {len(config.allow_commands)}[/]")

    # create model
    model = create_model(provider, model_name)

    # create tools and configure bash safety
    tools = create_tools()
    bash_tool = get_tool(tools, "bash")
    if isinstance(bash_tool, BashTool):
        bash_tool.configure(
            deny_patterns=config.deny_patterns,
            allow_commands=config.allow_commands,
            ask_by_default=config.ask_by_default,
            max_output_chars=config.max_output_chars,
        )

    # load MCP tools
    mcp_tools = []
    mcp_servers = []
    if not args.no_mcp:
        configs = load_mcp_config(config.global_dir, config.project_dir)
        if configs:
            mcp_tools, mcp_servers = start_mcp_servers(configs)
            if mcp_tools:
                console.print(f"[dim]mcp: {len(mcp_tools)} tool(s) loaded[/]")

    # cleanup MCP servers on exit
    if mcp_servers:
        atexit.register(lambda: [s.stop() for s in mcp_servers])

    # load skill
    active_skills = []
    if args.skill:
        all_skills = discover_skills(config.global_dir, config.project_dir)
        if args.skill not in all_skills:
            console.print(f"[red]skill '{args.skill}' not found[/]")
            sys.exit(1)
        active_skills.append(all_skills[args.skill])
        console.print(f"[dim]skill: {args.skill} active[/]")

    # build system prompt
    extra_tool_names = [t.name for t in mcp_tools]
    system_prompt = build_system_prompt(config, extra_tool_names)
    for skill in active_skills:
        system_prompt = inject_skill(system_prompt, skill)

    # create agent
    agent = Agent(
        model=model,
        provider=provider,
        system_prompt=system_prompt,
        tools=tools,
        mcp_tools=mcp_tools,
        max_turns=max_turns,
        verbose=verbose,
    )

    # git: protect uncommitted changes
    if do_auto_commit and is_git_repo():
        commit_dirty()

    # single prompt mode
    if args.prompt:
        agent.run(args.prompt)
        if do_auto_commit and is_git_repo():
            auto_commit(f"krim: {args.prompt[:60]}")
        return

    # interactive mode
    session = create_session()
    while True:
        user_input = prompt_input(session)
        if user_input is None:
            console.print("\n[dim]bye[/]")
            break

        stripped = user_input.strip()
        if not stripped:
            continue

        if stripped.lower() in ("exit", "quit", "q"):
            console.print("[dim]bye[/]")
            break

        # slash commands
        if stripped.startswith("/"):
            _handle_slash_command(stripped, agent, config, verbose)
            continue

        agent.run(user_input)

        if do_auto_commit and is_git_repo():
            auto_commit(f"krim: {stripped[:60]}")


if __name__ == "__main__":
    main()
