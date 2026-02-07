"""Core agent loop. Single loop, no sub-agents. Trust the model.

Features:
- Retry on API errors with exponential backoff
- Tool execution with error boundaries
- Doom loop detection (same tool call repeated)
- Context compaction when approaching token limits
- Max turns enforcement with graceful degradation
- Per-run stats tracking (turns, tool calls, token estimates)
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field

from rich.console import Console
from rich.panel import Panel

from krim.models.base import Model, ModelResponse, ToolCall
from krim.tools import get_tool, tool_schemas
from krim.tools.base import Tool
from krim.compaction import needs_compaction, compact, estimate_message_tokens
from krim.retry import with_retry

console = Console()


@dataclass
class RunStats:
    """Stats for a single agent.run() invocation."""
    turns: int = 0
    tool_calls: int = 0
    compactions: int = 0
    tool_call_names: dict[str, int] = field(default_factory=dict)

    def record_tool_call(self, name: str):
        self.tool_calls += 1
        self.tool_call_names[name] = self.tool_call_names.get(name, 0) + 1

MAX_STEPS_PROMPT = (
    "You have reached the maximum number of tool calls for this turn. "
    "Stop calling tools. Summarize what you accomplished and what remains to be done."
)


# -- message builders (provider-specific formatting) --

def _build_assistant_msg_claude(response: ModelResponse) -> dict:
    content = []
    if response.text:
        content.append({"type": "text", "text": response.text})
    for tc in response.tool_calls:
        content.append({
            "type": "tool_use",
            "id": tc.id,
            "name": tc.name,
            "input": tc.args,
        })
    return {"role": "assistant", "content": content}


def _build_assistant_msg_openai(response: ModelResponse) -> dict:
    msg: dict = {"role": "assistant"}
    if response.text:
        msg["content"] = response.text
    if response.tool_calls:
        msg["tool_calls"] = [
            {
                "id": tc.id,
                "type": "function",
                "function": {
                    "name": tc.name,
                    "arguments": json.dumps(tc.args),
                },
            }
            for tc in response.tool_calls
        ]
    return msg


def _build_tool_result_openai(tool_call_id: str, name: str, result: str) -> dict:
    return {
        "role": "tool",
        "tool_call_id": tool_call_id,
        "name": name,
        "content": result,
    }


class Agent:
    def __init__(
        self,
        model: Model,
        provider: str,
        system_prompt: str,
        tools: list[Tool],
        mcp_tools: list[Tool] | None = None,
        max_turns: int = 10,
        verbose: bool = False,
    ):
        self.model = model
        self.provider = provider
        self.max_turns = max_turns
        self.tools = tools
        self.mcp_tools = mcp_tools or []
        self.verbose = verbose
        self.messages: list[dict] = [{"role": "system", "content": system_prompt}]

        # doom loop detection: track recent tool calls
        self._recent_calls: list[str] = []

        # cumulative stats
        self.last_stats: RunStats | None = None
        self.total_turns: int = 0
        self.total_tool_calls: int = 0

    # -- tool management --

    def _all_tool_schemas(self) -> list[dict]:
        schemas = tool_schemas(self.tools)
        for mt in self.mcp_tools:
            schemas.append(mt.schema())
        return schemas

    def _execute_tool(self, name: str, args: dict) -> str:
        """Execute a tool with error boundary."""
        # check mcp tools first
        for mt in self.mcp_tools:
            if mt.name == name:
                try:
                    return mt.run(**args)
                except Exception as e:
                    return f"error: tool '{name}' raised: {e}"

        tool = get_tool(self.tools, name)
        if not tool:
            return f"error: unknown tool '{name}'"
        try:
            return tool.run(**args)
        except Exception as e:
            return f"error: tool '{name}' raised: {e}"

    # -- doom loop detection --

    def _check_doom_loop(self, tool_calls: list[ToolCall]) -> bool:
        """Detect if the agent is stuck calling the same tools repeatedly."""
        sig = json.dumps([(tc.name, tc.args) for tc in tool_calls], sort_keys=True)
        self._recent_calls.append(sig)
        if len(self._recent_calls) > 10:
            self._recent_calls = self._recent_calls[-10:]

        # same call 3 times in a row
        if len(self._recent_calls) >= 3:
            last3 = self._recent_calls[-3:]
            if last3[0] == last3[1] == last3[2]:
                return True
        return False

    # -- display --

    def _print_tool_call(self, name: str, args: dict):
        icon = {"bash": ">>", "read": "<<", "write": "=>", "edit": "<>"}.get(name, "::")
        summary = f"[bold cyan]{icon} {name}[/]"
        if name == "bash":
            cmd = args.get("command", "")
            # show first line of multi-line commands
            first_line = cmd.split("\n")[0]
            if len(first_line) > 100:
                first_line = first_line[:97] + "..."
            summary += f"  `{first_line}`"
        elif name in ("read", "write", "edit"):
            path = args.get("path", "")
            summary += f"  {path}"
        else:
            summary += f"  {json.dumps(args, ensure_ascii=False)[:80]}"
        console.print(summary)

    def _print_tool_result(self, result: str):
        lines = result.splitlines()
        preview = "\n".join(lines[:20])
        if len(lines) > 20:
            preview += f"\n[dim]... ({len(lines) - 20} more lines)[/]"
        console.print(Panel(preview, border_style="dim", expand=False, padding=(0, 1)))

    # -- core loop --

    def run(self, user_input: str) -> RunStats:
        """Execute a single user request through the agent loop."""
        self.messages.append({"role": "user", "content": user_input})
        self._recent_calls.clear()
        stats = RunStats()

        # cache tool schemas (deterministic order for prompt cache)
        cached_schemas = self._all_tool_schemas()

        # wrap model.chat with retry
        chat_with_retry = with_retry(self.model.chat)

        turn = 0
        while turn < self.max_turns:
            turn += 1
            stats.turns = turn

            if self.verbose:
                tokens = estimate_message_tokens(self.messages)
                console.print(f"\n[dim]--- turn {turn}/{self.max_turns}  ~{tokens:,} tokens ---[/]")
            else:
                console.print(f"\n[dim]--- turn {turn}/{self.max_turns} ---[/]")

            # check for compaction
            if needs_compaction(self.messages):
                console.print("[dim]compacting conversation...[/]")
                self.messages = compact(self.messages)
                stats.compactions += 1

            # stream callback
            def stream_cb(text: str):
                console.print(text, end="", highlight=False)

            # call model with retry
            try:
                response = chat_with_retry(
                    messages=self.messages,
                    tools=cached_schemas,
                    stream_callback=stream_cb,
                )
            except Exception as e:
                console.print(f"\n[red]model error: {e}[/]")
                break

            if response.text:
                console.print()

            # no tool calls -> model is done
            if not response.tool_calls:
                if response.text:
                    self.messages.append({"role": "assistant", "content": response.text})
                break

            # doom loop detection
            if self._check_doom_loop(response.tool_calls):
                console.print("[yellow]doom loop detected, forcing stop[/]")
                self.messages.append({"role": "user", "content": MAX_STEPS_PROMPT})
                try:
                    final = chat_with_retry(
                        messages=self.messages,
                        tools=[],  # no tools, force text response
                        stream_callback=stream_cb,
                    )
                    if final.text:
                        console.print()
                        self.messages.append({"role": "assistant", "content": final.text})
                except Exception:
                    pass
                break

            # add assistant message with tool calls
            if self.provider == "claude":
                self.messages.append(_build_assistant_msg_claude(response))
            else:
                self.messages.append(_build_assistant_msg_openai(response))

            # execute each tool call
            tool_results = []
            for tc in response.tool_calls:
                self._print_tool_call(tc.name, tc.args)
                result = self._execute_tool(tc.name, tc.args)
                self._print_tool_result(result)
                tool_results.append((tc, result))
                stats.record_tool_call(tc.name)

            # add tool results to messages
            if self.provider == "claude":
                content = []
                for tc, result in tool_results:
                    content.append({
                        "type": "tool_result",
                        "tool_use_id": tc.id,
                        "content": result,
                    })
                self.messages.append({"role": "user", "content": content})
            else:
                for tc, result in tool_results:
                    self.messages.append(_build_tool_result_openai(tc.id, tc.name, result))

        else:
            # while-else: loop condition became false (not break) = all turns used with tool calls still pending
            console.print(f"\n[yellow]reached max turns ({self.max_turns})[/]")
            # inject max_steps prompt for graceful summary
            self.messages.append({"role": "user", "content": MAX_STEPS_PROMPT})
            try:
                final = chat_with_retry(
                    messages=self.messages,
                    tools=[],
                    stream_callback=lambda t: console.print(t, end="", highlight=False),
                )
                if final.text:
                    console.print()
                    self.messages.append({"role": "assistant", "content": final.text})
            except Exception:
                pass

        # print run stats
        self._print_stats(stats)
        self.last_stats = stats
        self.total_turns += stats.turns
        self.total_tool_calls += stats.tool_calls
        return stats

    def _print_stats(self, stats: RunStats):
        parts = [f"turns: {stats.turns}"]
        if stats.tool_calls:
            tools_summary = ", ".join(f"{n}:{c}" for n, c in sorted(stats.tool_call_names.items()))
            parts.append(f"tool calls: {stats.tool_calls} ({tools_summary})")
        if stats.compactions:
            parts.append(f"compactions: {stats.compactions}")
        tokens = estimate_message_tokens(self.messages)
        parts.append(f"~{tokens:,} tokens")
        console.print(f"\n[dim]{' | '.join(parts)}[/]")

    def token_count(self) -> int:
        return estimate_message_tokens(self.messages)

    def force_compact(self):
        """Manually trigger compaction."""
        before = estimate_message_tokens(self.messages)
        self.messages = compact(self.messages)
        after = estimate_message_tokens(self.messages)
        console.print(f"[dim]compacted: ~{before:,} → ~{after:,} tokens[/]")
