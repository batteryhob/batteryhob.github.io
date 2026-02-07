"""Abstract model interface."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class ToolCall:
    id: str
    name: str
    args: dict


@dataclass
class ModelResponse:
    text: str | None
    tool_calls: list[ToolCall]
    stop: bool  # model wants to stop (no more tool calls, final answer)


class Model(ABC):
    @abstractmethod
    def chat(
        self,
        messages: list[dict],
        tools: list[dict],
        stream_callback=None,
    ) -> ModelResponse:
        ...
