"""Base tool interface."""

from __future__ import annotations

from abc import ABC, abstractmethod


class Tool(ABC):
    name: str
    description: str
    parameters: dict

    @abstractmethod
    def run(self, **kwargs) -> str:
        ...

    def schema(self) -> dict:
        """Generate tool schema in Anthropic format (also used as canonical internal format)."""
        required = [
            k for k, v in self.parameters.items()
            if not v.get("optional", False)
        ]
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": {
                "type": "object",
                "properties": {
                    k: {key: val for key, val in v.items() if key != "optional"}
                    for k, v in self.parameters.items()
                },
                "required": required,
            },
        }
