"""MCP (Model Context Protocol) client support.

Connect to external MCP servers via stdio or SSE and use their tools.
Config lives in ~/.krim/mcp.json or ./krim.json
"""

import json
import os
import subprocess
from dataclasses import dataclass
from krim.tools.base import Tool


@dataclass
class McpServerConfig:
    name: str
    command: list[str]  # e.g. ["npx", "-y", "@modelcontextprotocol/server-filesystem", "/tmp"]
    env: dict[str, str] | None = None


class McpTool(Tool):
    """A tool proxied from an MCP server."""

    def __init__(self, name: str, description: str, parameters: dict, server: "McpServer"):
        self.name = name
        self.description = description
        self.parameters = parameters
        self._server = server

    def run(self, **kwargs) -> str:
        return self._server.call_tool(self.name, kwargs)


class McpServer:
    """Manages a single MCP server process via stdio JSON-RPC."""

    def __init__(self, config: McpServerConfig):
        self.config = config
        self.process: subprocess.Popen | None = None
        self._request_id = 0
        self.tools: list[McpTool] = []

    def start(self):
        env = os.environ.copy()
        if self.config.env:
            env.update(self.config.env)

        self.process = subprocess.Popen(
            self.config.command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
            text=True,
        )
        self._initialize()
        self._discover_tools()

    def stop(self):
        if self.process:
            self.process.terminate()
            self.process = None

    def _send(self, method: str, params: dict = None) -> dict:
        self._request_id += 1
        msg = {
            "jsonrpc": "2.0",
            "id": self._request_id,
            "method": method,
        }
        if params:
            msg["params"] = params

        raw = json.dumps(msg) + "\n"
        self.process.stdin.write(raw)
        self.process.stdin.flush()

        line = self.process.stdout.readline()
        if not line:
            return {"error": "no response from MCP server"}
        return json.loads(line)

    def _initialize(self):
        self._send("initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "krim", "version": "0.1.0"},
        })

    def _discover_tools(self):
        resp = self._send("tools/list")
        if "result" not in resp:
            return
        for t in resp["result"].get("tools", []):
            props = {}
            schema = t.get("inputSchema", {})
            if "properties" in schema:
                props = schema["properties"]
            self.tools.append(McpTool(
                name=t["name"],
                description=t.get("description", ""),
                parameters=props,
                server=self,
            ))

    def call_tool(self, name: str, args: dict) -> str:
        resp = self._send("tools/call", {"name": name, "arguments": args})
        if "error" in resp:
            return f"error: {resp['error']}"
        result = resp.get("result", {})
        # MCP tool results have content array
        contents = result.get("content", [])
        parts = []
        for c in contents:
            if c.get("type") == "text":
                parts.append(c["text"])
            else:
                parts.append(json.dumps(c))
        return "\n".join(parts) or "(no output)"


def load_mcp_config() -> list[McpServerConfig]:
    """Load MCP server configs from ~/.krim/mcp.json or ./krim.json"""
    configs = []
    for path in [os.path.expanduser("~/.krim/mcp.json"), "krim.json"]:
        if os.path.isfile(path):
            with open(path) as f:
                data = json.load(f)
            for name, cfg in data.get("mcpServers", {}).items():
                configs.append(McpServerConfig(
                    name=name,
                    command=cfg["command"],
                    env=cfg.get("env"),
                ))
    return configs


def start_mcp_servers(configs: list[McpServerConfig]) -> list[McpTool]:
    """Start all MCP servers and collect their tools."""
    all_tools = []
    servers = []
    for cfg in configs:
        try:
            server = McpServer(cfg)
            server.start()
            servers.append(server)
            all_tools.extend(server.tools)
        except Exception as e:
            from rich.console import Console
            Console().print(f"[yellow]mcp: failed to start {cfg.name}: {e}[/]")
    return all_tools
