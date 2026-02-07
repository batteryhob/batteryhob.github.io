"""OpenAI model provider (codex / gpt models)."""

from __future__ import annotations

import json
import os
from typing import Callable

from openai import OpenAI

from krim.models.base import Model, ModelResponse, ToolCall


class OpenAIModel(Model):
    def __init__(self, model: str = "gpt-4o", max_tokens: int = 16_384):
        self.model = model
        self.max_tokens = max_tokens
        self.client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

    def chat(
        self,
        messages: list[dict],
        tools: list[dict],
        stream_callback: Callable[[str], None] | None = None,
    ) -> ModelResponse:
        oai_tools = self._convert_tools(tools) if tools else None

        kwargs: dict = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "messages": messages,
        }
        if oai_tools:
            kwargs["tools"] = oai_tools

        if stream_callback:
            return self._stream(kwargs, stream_callback)
        else:
            resp = self.client.chat.completions.create(**kwargs)
            return self._parse(resp)

    def _convert_tools(self, tools: list[dict]) -> list[dict]:
        """Convert krim tool schemas to OpenAI function calling format."""
        return [
            {
                "type": "function",
                "function": {
                    "name": t["name"],
                    "description": t["description"],
                    "parameters": t["input_schema"],
                },
            }
            for t in tools
        ]

    def _stream(self, kwargs: dict, callback: Callable[[str], None]) -> ModelResponse:
        kwargs["stream"] = True
        text_parts: list[str] = []
        tool_calls_map: dict[int, dict] = {}

        for chunk in self.client.chat.completions.create(**kwargs):
            delta = chunk.choices[0].delta if chunk.choices else None
            if not delta:
                continue

            if delta.content:
                callback(delta.content)
                text_parts.append(delta.content)

            if delta.tool_calls:
                for tc in delta.tool_calls:
                    idx = tc.index
                    if idx not in tool_calls_map:
                        tool_calls_map[idx] = {"id": tc.id or "", "name": "", "args": ""}
                    if tc.id:
                        tool_calls_map[idx]["id"] = tc.id
                    if tc.function and tc.function.name:
                        tool_calls_map[idx]["name"] = tc.function.name
                    if tc.function and tc.function.arguments:
                        tool_calls_map[idx]["args"] += tc.function.arguments

        tool_calls: list[ToolCall] = []
        for idx in sorted(tool_calls_map):
            tc = tool_calls_map[idx]
            args = json.loads(tc["args"]) if tc["args"] else {}
            tool_calls.append(ToolCall(id=tc["id"], name=tc["name"], args=args))

        text = "".join(text_parts) or None
        stop = len(tool_calls) == 0
        return ModelResponse(text=text, tool_calls=tool_calls, stop=stop)

    def _parse(self, resp) -> ModelResponse:
        msg = resp.choices[0].message
        text = msg.content
        tool_calls: list[ToolCall] = []
        if msg.tool_calls:
            for tc in msg.tool_calls:
                args = json.loads(tc.function.arguments) if tc.function.arguments else {}
                tool_calls.append(ToolCall(
                    id=tc.id,
                    name=tc.function.name,
                    args=args,
                ))
        stop = resp.choices[0].finish_reason == "stop"
        return ModelResponse(text=text, tool_calls=tool_calls, stop=stop)
