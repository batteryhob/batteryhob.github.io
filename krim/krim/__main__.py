"""krim - thin CLI agent. trust the model, keep the harness light.

Usage:
  krim "fix the bug in main.py"
  krim --provider claude --model claude-sonnet-4-5-20250929 "refactor this"
  krim --provider openai --model gpt-4o "add tests"
  krim --max-turns 20 "big refactor task"
  krim --skill deploy "ship it"
  krim                         # interactive mode
"""

import argparse
import sys

from rich.console import Console
from rich.markdown import Markdown

from krim import __version__
from krim.models import create_model
from krim.agent import Agent
from krim.mcp import load_mcp_config, start_mcp_servers
from krim.skills import discover_skills, inject_skill
from krim.prompt import SYSTEM

console = Console()


def parse_args():
    p = argparse.ArgumentParser(
        prog="krim",
        description="Thin CLI agent. Trust the model, keep the harness light.",
    )
    p.add_argument("prompt", nargs="?", help="task to perform (omit for interactive mode)")
    p.add_argument("--provider", "-p", default="claude", choices=["claude", "openai"],
                    help="model provider (default: claude)")
    p.add_argument("--model", "-m", default=None,
                    help="model name (default: provider's default)")
    p.add_argument("--max-turns", "-t", type=int, default=10,
                    help="max agent turns (default: 10)")
    p.add_argument("--skill", "-s", default=None,
                    help="activate a skill by name")
    p.add_argument("--list-skills", action="store_true",
                    help="list available skills")
    p.add_argument("--no-mcp", action="store_true",
                    help="disable MCP servers")
    p.add_argument("--version", "-v", action="version", version=f"krim {__version__}")
    return p.parse_args()


def default_model(provider: str) -> str:
    if provider == "claude":
        return "claude-sonnet-4-5-20250929"
    return "gpt-4o"


def main():
    args = parse_args()

    # list skills
    if args.list_skills:
        skills = discover_skills()
        if not skills:
            console.print("[dim]no skills found. add them to ~/.krim/skills/ or ./skills/[/]")
        for name, skill in skills.items():
            first_line = skill.prompt.strip().splitlines()[0] if skill.prompt.strip() else ""
            console.print(f"  [bold]{name}[/]  {first_line}")
        return

    model_name = args.model or default_model(args.provider)

    console.print(f"[bold]krim[/] v{__version__}  [dim]{args.provider}/{model_name}  max_turns={args.max_turns}[/]")

    # load model
    model = create_model(args.provider, model_name)

    # load MCP tools
    mcp_tools = []
    if not args.no_mcp:
        configs = load_mcp_config()
        if configs:
            console.print(f"[dim]mcp: connecting to {len(configs)} server(s)...[/]")
            mcp_tools = start_mcp_servers(configs)
            if mcp_tools:
                console.print(f"[dim]mcp: {len(mcp_tools)} tool(s) loaded[/]")

    # load skill
    skills_extra = []
    if args.skill:
        all_skills = discover_skills()
        if args.skill not in all_skills:
            console.print(f"[red]skill '{args.skill}' not found[/]")
            sys.exit(1)
        skills_extra.append(all_skills[args.skill])
        console.print(f"[dim]skill: {args.skill} active[/]")

    # create agent
    agent = Agent(
        model=model,
        provider=args.provider,
        max_turns=args.max_turns,
        mcp_tools=mcp_tools,
    )

    # inject skills into system prompt
    for skill in skills_extra:
        agent.messages[0]["content"] = inject_skill(agent.messages[0]["content"], skill)

    # single prompt mode
    if args.prompt:
        agent.run(args.prompt)
        return

    # interactive mode
    console.print("[dim]interactive mode. type 'exit' to quit.[/]\n")
    while True:
        try:
            user_input = console.input("[bold green]> [/]")
        except (EOFError, KeyboardInterrupt):
            console.print("\n[dim]bye[/]")
            break

        if user_input.strip().lower() in ("exit", "quit", "q"):
            console.print("[dim]bye[/]")
            break

        if not user_input.strip():
            continue

        agent.run(user_input)


if __name__ == "__main__":
    main()
