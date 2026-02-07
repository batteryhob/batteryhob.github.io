"""Core agent loop. Single loop, no sub-agents. Trust the model."""

import json
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

from krim.models.base import Model, ModelResponse
from krim.tools import get_tool, tool_schemas, ALL_TOOLS
from krim.prompt import SYSTEM

console = Console()


def _build_tool_result_claude(tool_call_id: str, result: str) -> dict:
    return {
        "role": "user",
        "content": [
            {
                "type": "tool_result",
                "tool_use_id": tool_call_id,
                "content": result,
            }
        ],
    }


def _build_tool_result_openai(tool_call_id: str, name: str, result: str) -> dict:
    return {
        "role": "tool",
        "tool_call_id": tool_call_id,
        "name": name,
        "content": result,
    }


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
    msg = {"role": "assistant"}
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


class Agent:
    def __init__(self, model: Model, provider: str, max_turns: int = 10, skills: list = None, mcp_tools: list = None):
        self.model = model
        self.provider = provider
        self.max_turns = max_turns
        self.messages: list[dict] = [{"role": "system", "content": SYSTEM}]
        self.skills = skills or []
        self.mcp_tools = mcp_tools or []

    def _get_tools(self) -> list[dict]:
        schemas = tool_schemas()
        # add mcp tool schemas
        for mt in self.mcp_tools:
            schemas.append(mt.schema())
        return schemas

    def _execute_tool(self, name: str, args: dict) -> str:
        # check mcp tools first
        for mt in self.mcp_tools:
            if mt.name == name:
                return mt.run(**args)
        # then built-in tools
        tool = get_tool(name)
        if not tool:
            return f"error: unknown tool '{name}'"
        return tool.run(**args)

    def _print_tool_call(self, name: str, args: dict):
        summary = f"[bold cyan]{name}[/]"
        if name == "bash":
            summary += f"  `{args.get('command', '')}`"
        elif name == "read":
            summary += f"  {args.get('path', '')}"
        elif name == "write":
            summary += f"  {args.get('path', '')}"
        elif name == "edit":
            summary += f"  {args.get('path', '')}"
        else:
            summary += f"  {json.dumps(args, ensure_ascii=False)[:80]}"
        console.print(summary)

    def _print_tool_result(self, result: str):
        lines = result.splitlines()
        preview = "\n".join(lines[:10])
        if len(lines) > 10:
            preview += f"\n... ({len(lines) - 10} more lines)"
        console.print(Panel(preview, style="dim", expand=False))

    def run(self, user_input: str):
        self.messages.append({"role": "user", "content": user_input})

        turn = 0
        while turn < self.max_turns:
            turn += 1
            console.print(f"\n[dim]--- turn {turn}/{self.max_turns} ---[/]")

            def stream_cb(text: str):
                console.print(text, end="", highlight=False)

            response = self.model.chat(
                messages=self.messages,
                tools=self._get_tools(),
                stream_callback=stream_cb,
            )

            # print streamed text newline
            if response.text:
                console.print()

            # no tool calls -> model is done
            if not response.tool_calls:
                if response.text:
                    self.messages.append({"role": "assistant", "content": response.text})
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

            # add tool results to messages
            if self.provider == "claude":
                # claude: all tool results in one user message
                content = []
                for tc, result in tool_results:
                    content.append({
                        "type": "tool_result",
                        "tool_use_id": tc.id,
                        "content": result,
                    })
                self.messages.append({"role": "user", "content": content})
            else:
                # openai: separate message per tool result
                for tc, result in tool_results:
                    self.messages.append(_build_tool_result_openai(tc.id, tc.name, result))

        if turn >= self.max_turns:
            console.print(f"\n[yellow]reached max turns ({self.max_turns})[/]")
