from krim.tools.read import ReadTool
from krim.tools.write import WriteTool
from krim.tools.edit import EditTool
from krim.tools.bash import BashTool

ALL_TOOLS = [ReadTool(), WriteTool(), EditTool(), BashTool()]

def get_tool(name: str):
    for t in ALL_TOOLS:
        if t.name == name:
            return t
    return None

def tool_schemas() -> list[dict]:
    return [t.schema() for t in ALL_TOOLS]
