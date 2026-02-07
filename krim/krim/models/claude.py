"""Claude model provider."""

import os
from anthropic import Anthropic
from krim.models.base import Model, ModelResponse, ToolCall


class ClaudeModel(Model):
    def __init__(self, model: str = "claude-sonnet-4-5-20250929"):
        self.model = model
        self.client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

    def chat(self, messages: list[dict], tools: list[dict], stream_callback=None) -> ModelResponse:
        # separate system message
        system = None
        chat_msgs = []
        for m in messages:
            if m["role"] == "system":
                system = m["content"]
            else:
                chat_msgs.append(m)

        kwargs = {
            "model": self.model,
            "max_tokens": 8192,
            "messages": chat_msgs,
        }
        if system:
            kwargs["system"] = system
        if tools:
            kwargs["tools"] = tools

        if stream_callback:
            return self._stream(kwargs, stream_callback)
        else:
            resp = self.client.messages.create(**kwargs)
            return self._parse(resp)

    def _stream(self, kwargs, callback) -> ModelResponse:
        text_parts = []
        tool_calls = []
        current_tool = None

        with self.client.messages.stream(**kwargs) as stream:
            for event in stream:
                if event.type == "content_block_start":
                    if event.content_block.type == "text":
                        pass
                    elif event.content_block.type == "tool_use":
                        current_tool = {
                            "id": event.content_block.id,
                            "name": event.content_block.name,
                            "input_json": "",
                        }
                elif event.type == "content_block_delta":
                    if event.delta.type == "text_delta":
                        callback(event.delta.text)
                        text_parts.append(event.delta.text)
                    elif event.delta.type == "input_json_delta":
                        if current_tool:
                            current_tool["input_json"] += event.delta.partial_json
                elif event.type == "content_block_stop":
                    if current_tool:
                        import json
                        args = json.loads(current_tool["input_json"]) if current_tool["input_json"] else {}
                        tool_calls.append(ToolCall(
                            id=current_tool["id"],
                            name=current_tool["name"],
                            args=args,
                        ))
                        current_tool = None

            final = stream.get_final_message()

        text = "".join(text_parts) or None
        stop = final.stop_reason == "end_turn"
        return ModelResponse(text=text, tool_calls=tool_calls, stop=stop)

    def _parse(self, resp) -> ModelResponse:
        text_parts = []
        tool_calls = []
        for block in resp.content:
            if block.type == "text":
                text_parts.append(block.text)
            elif block.type == "tool_use":
                tool_calls.append(ToolCall(
                    id=block.id,
                    name=block.name,
                    args=block.input,
                ))
        text = "\n".join(text_parts) or None
        stop = resp.stop_reason == "end_turn"
        return ModelResponse(text=text, tool_calls=tool_calls, stop=stop)
