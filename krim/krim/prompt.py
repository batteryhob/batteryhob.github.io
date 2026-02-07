"""System prompt builder.

Assembles the final prompt from:
1. Core identity (minimal, ~50 words)
2. Context (cwd, git info, project tree)
3. KRIM.md instructions
4. Rules
5. Active skills

Philosophy: keep the core tiny. Let context and instructions do the work.
"""

from __future__ import annotations

from krim.config import KrimConfig
from krim.context import build_context

CORE = """You are krim, a coding agent running in the user's terminal.
You have tools: read, write, edit, bash.
Be direct. Fix root causes, not symptoms. After editing code, verify your changes with bash (run tests, lint, compile). When done, say so.
Tool notes: bash working directory persists across calls (cd works). edit uses fuzzy matching if exact match fails."""


def build_system_prompt(config: KrimConfig, extra_tools: list[str] | None = None) -> str:
    """Build the complete system prompt."""
    parts = [CORE]

    # inject extra tool names if MCP tools are loaded
    if extra_tools:
        parts.append(f"Additional tools available: {', '.join(extra_tools)}")

    # context: cwd, git, project tree
    ctx = build_context()
    parts.append(f"# Environment\n{ctx}")

    # KRIM.md project/global instructions
    if config.krim_md:
        parts.append(f"# Project Instructions\n{config.krim_md}")

    # rules
    for i, rule in enumerate(config.rules):
        parts.append(f"# Rule {i + 1}\n{rule}")

    return "\n\n".join(parts)
