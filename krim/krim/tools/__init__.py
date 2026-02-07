"""Tool registry."""

from __future__ import annotations

from krim.tools.read import ReadTool
from krim.tools.write import WriteTool
from krim.tools.edit import EditTool
from krim.tools.bash import BashTool
from krim.tools.base import Tool


def create_tools() -> list[Tool]:
    """Create fresh tool instances."""
    return [ReadTool(), WriteTool(), EditTool(), BashTool()]


def get_tool(tools: list[Tool], name: str) -> Tool | None:
    for t in tools:
        if t.name == name:
            return t
    return None


def tool_schemas(tools: list[Tool]) -> list[dict]:
    return [t.schema() for t in tools]
