"""MCP (Model Context Protocol) client support.

Connects to external MCP servers via stdio with proper Content-Length framing.
Config lives in ~/.krim/mcp.json or .krim/mcp.json
"""

from __future__ import annotations

import json
import os
import select
import subprocess
from dataclasses import dataclass
from pathlib import Path

from rich.console import Console

from krim import __version__
from krim.tools.base import Tool
from krim.truncate import truncate

MCP_READ_TIMEOUT = 60  # seconds

console = Console()


@dataclass
class McpServerConfig:
    name: str
    command: list[str]
    env: dict[str, str] | None = None


class McpTool(Tool):
    """A tool proxied from an MCP server."""

    def __init__(self, name: str, description: str, parameters: dict, server: McpServer):
        self.name = name
        self.description = description
        self.parameters = parameters
        self._server = server
        self._required: list[str] = []

    def schema(self) -> dict:
        """Generate schema with proper required field from MCP server."""
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": {
                "type": "object",
                "properties": self.parameters,
                "required": self._required,
            },
        }

    def run(self, **kwargs) -> str:
        return self._server.call_tool(self.name, kwargs)


class McpServer:
    """Manages a single MCP server process via stdio with Content-Length framing."""

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
        )
        self._initialize()
        self._discover_tools()

    def stop(self):
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=5)
            except Exception:
                self.process.kill()
            self.process = None

    def _send_raw(self, data: bytes):
        """Send a message with Content-Length header framing."""
        header = f"Content-Length: {len(data)}\r\n\r\n".encode()
        self.process.stdin.write(header + data)
        self.process.stdin.flush()

    def _recv_raw(self, timeout: float = MCP_READ_TIMEOUT) -> bytes:
        """Read a Content-Length framed message with timeout."""
        # wait for data with timeout
        fd = self.process.stdout.fileno()
        ready, _, _ = select.select([fd], [], [], timeout)
        if not ready:
            raise TimeoutError(f"MCP server did not respond within {timeout}s")

        # read headers
        content_length = 0
        while True:
            line = self.process.stdout.readline()
            if not line:
                raise ConnectionError("MCP server closed connection")
            line_str = line.decode("utf-8", errors="replace").strip()
            if not line_str:
                break  # empty line = end of headers
            if line_str.lower().startswith("content-length:"):
                content_length = int(line_str.split(":", 1)[1].strip())

        if content_length == 0:
            raise ConnectionError("MCP server sent no Content-Length")

        data = self.process.stdout.read(content_length)
        return data

    def _send(self, method: str, params: dict | None = None) -> dict:
        self._request_id += 1
        msg = {
            "jsonrpc": "2.0",
            "id": self._request_id,
            "method": method,
        }
        if params is not None:
            msg["params"] = params

        self._send_raw(json.dumps(msg).encode("utf-8"))

        # read responses, skipping notifications (no "id" field)
        while True:
            raw = self._recv_raw()
            resp = json.loads(raw)
            if "id" in resp:
                return resp
            # else it's a notification, skip it

    def _initialize(self):
        resp = self._send("initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "krim", "version": __version__},
        })
        # send initialized notification
        notify = {
            "jsonrpc": "2.0",
            "method": "notifications/initialized",
        }
        self._send_raw(json.dumps(notify).encode("utf-8"))
        return resp

    def _discover_tools(self):
        resp = self._send("tools/list")
        if "result" not in resp:
            return
        for t in resp["result"].get("tools", []):
            schema = t.get("inputSchema", {})
            props = schema.get("properties", {})
            required = schema.get("required", [])
            # store full schema info so McpTool.schema() works correctly
            tool = McpTool(
                name=t["name"],
                description=t.get("description", ""),
                parameters=props,
                server=self,
            )
            tool._required = required
            self.tools.append(tool)

    def call_tool(self, name: str, args: dict) -> str:
        try:
            resp = self._send("tools/call", {"name": name, "arguments": args})
        except Exception as e:
            return f"error: MCP call failed: {e}"

        if "error" in resp:
            err = resp["error"]
            msg = err.get("message", str(err)) if isinstance(err, dict) else str(err)
            return f"error: {msg}"

        result = resp.get("result", {})
        contents = result.get("content", [])
        parts = []
        for c in contents:
            if c.get("type") == "text":
                parts.append(c["text"])
            else:
                parts.append(json.dumps(c))
        out = "\n".join(parts) or "(no output)"
        return truncate(out, 30_000)


def load_mcp_config(global_dir: Path | None = None, project_dir: Path | None = None) -> list[McpServerConfig]:
    """Load MCP server configs from ~/.krim/mcp.json and .krim/mcp.json"""
    configs = []
    search_paths = []
    if global_dir:
        search_paths.append(global_dir / "mcp.json")
    else:
        search_paths.append(Path.home() / ".krim" / "mcp.json")
    if project_dir:
        search_paths.append(project_dir / "mcp.json")

    for path in search_paths:
        if path.is_file():
            try:
                with open(path) as f:
                    data = json.load(f)
                for name, cfg in data.get("mcpServers", {}).items():
                    configs.append(McpServerConfig(
                        name=name,
                        command=cfg["command"],
                        env=cfg.get("env"),
                    ))
            except Exception as e:
                console.print(f"[yellow]mcp: failed to load {path}: {e}[/]")

    return configs


def start_mcp_servers(configs: list[McpServerConfig]) -> tuple[list[McpTool], list[McpServer]]:
    """Start all MCP servers and collect their tools. Returns (tools, servers) for cleanup."""
    all_tools = []
    servers = []
    for cfg in configs:
        try:
            server = McpServer(cfg)
            server.start()
            servers.append(server)
            all_tools.extend(server.tools)
            console.print(f"[dim]mcp: {cfg.name} started ({len(server.tools)} tools)[/]")
        except Exception as e:
            console.print(f"[yellow]mcp: failed to start {cfg.name}: {e}[/]")
    return all_tools, servers
