"""Configuration loader.

Layered config with precedence: CLI flags > .krim/ (project) > ~/.krim/ (global) > defaults.

Directory convention:
    ~/.krim/                  # global
    ├── config.json
    ├── KRIM.md
    ├── mcp.json
    ├── skills/
    │   └── <name>/SKILL.md
    └── rules/
        └── *.md

    .krim/                    # project (git root or cwd)
    ├── config.json
    ├── KRIM.md
    ├── mcp.json
    ├── skills/
    │   └── <name>/SKILL.md
    └── rules/
        └── *.md
"""

from __future__ import annotations

import json
import os
import subprocess
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class KrimConfig:
    provider: str = "claude"
    model: str | None = None
    max_turns: int = 10
    max_output_chars: int = 30_000
    auto_commit: bool = False

    # safety
    allow_commands: list[str] = field(default_factory=lambda: [
        "ls", "cat", "head", "tail", "find", "grep", "rg", "wc",
        "git status", "git diff", "git log", "git branch",
        "python -m py_compile", "python -c",
        "npm run lint", "npm test", "pytest", "make",
    ])
    deny_patterns: list[str] = field(default_factory=lambda: [
        "rm -rf /", "rm -rf ~", "rm -rf /*",
        "> /dev/sda", "mkfs.", "dd if=",
        ":(){:|:&};:", "chmod -R 777 /",
        "curl|sh", "curl|bash", "wget|sh", "wget|bash",
    ])
    ask_by_default: bool = True

    # paths resolved at load time
    global_dir: Path = field(default_factory=lambda: Path.home() / ".krim")
    project_dir: Path | None = None

    # loaded content
    krim_md: str = ""
    rules: list[str] = field(default_factory=list)


def _find_git_root() -> Path | None:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, timeout=5,
        )
        if result.returncode == 0:
            return Path(result.stdout.strip())
    except Exception:
        pass
    return None


def _find_project_dir() -> Path | None:
    cwd = Path.cwd()
    if (cwd / ".krim").is_dir():
        return cwd / ".krim"
    git_root = _find_git_root()
    if git_root and (git_root / ".krim").is_dir():
        return git_root / ".krim"
    return None


def _load_json(path: Path) -> dict:
    if path.is_file():
        with open(path) as f:
            return json.load(f)
    return {}


def _load_text(path: Path) -> str:
    if path.is_file():
        return path.read_text()
    return ""


def _load_rules(directory: Path) -> list[str]:
    rules = []
    rules_dir = directory / "rules"
    if rules_dir.is_dir():
        for p in sorted(rules_dir.glob("*.md")):
            rules.append(p.read_text())
    return rules


def _merge_config(base: dict, override: dict) -> dict:
    merged = base.copy()
    for k, v in override.items():
        if isinstance(v, dict) and isinstance(merged.get(k), dict):
            merged[k] = _merge_config(merged[k], v)
        else:
            merged[k] = v
    return merged


def load_config() -> KrimConfig:
    """Load config with layered precedence: project overrides global."""
    cfg = KrimConfig()
    cfg.project_dir = _find_project_dir()

    # load JSON configs: global first, project overrides
    global_json = _load_json(cfg.global_dir / "config.json")
    project_json = _load_json(cfg.project_dir / "config.json") if cfg.project_dir else {}
    merged = _merge_config(global_json, project_json)

    # apply merged config
    if "provider" in merged:
        cfg.provider = merged["provider"]
    if "model" in merged:
        cfg.model = merged["model"]
    if "max_turns" in merged:
        cfg.max_turns = merged["max_turns"]
    if "max_output_chars" in merged:
        cfg.max_output_chars = merged["max_output_chars"]
    if "auto_commit" in merged:
        cfg.auto_commit = merged["auto_commit"]
    if "allow_commands" in merged:
        cfg.allow_commands = merged["allow_commands"]
    if "deny_patterns" in merged:
        cfg.deny_patterns = merged["deny_patterns"]
    if "ask_by_default" in merged:
        cfg.ask_by_default = merged["ask_by_default"]

    # load KRIM.md: project overrides global
    global_md = _load_text(cfg.global_dir / "KRIM.md")
    project_md = _load_text(cfg.project_dir / "KRIM.md") if cfg.project_dir else ""
    parts = [p for p in [global_md, project_md] if p.strip()]
    cfg.krim_md = "\n\n".join(parts)

    # load rules: accumulate from both
    cfg.rules = _load_rules(cfg.global_dir)
    if cfg.project_dir:
        cfg.rules.extend(_load_rules(cfg.project_dir))

    return cfg
