"""Skill system - reusable prompt + script packages.

Skills are directories containing:
  SKILL.md  - description and instructions (appended to system prompt when active)
  *.sh      - optional helper scripts the model can reference

Search paths: ~/.krim/skills/ and .krim/skills/ (project overrides global)
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass
class Skill:
    name: str
    prompt: str   # contents of SKILL.md
    path: str     # directory path


def discover_skills(
    global_dir: Path | None = None,
    project_dir: Path | None = None,
) -> dict[str, Skill]:
    """Find all available skills. Project skills override global ones."""
    skills = {}
    search_dirs = []

    if global_dir:
        search_dirs.append(global_dir / "skills")
    else:
        search_dirs.append(Path.home() / ".krim" / "skills")

    if project_dir:
        search_dirs.append(project_dir / "skills")

    for base in search_dirs:
        if not base.is_dir():
            continue
        for entry in sorted(base.iterdir()):
            if not entry.is_dir():
                continue
            skill_md = entry / "SKILL.md"
            if skill_md.is_file():
                skills[entry.name] = Skill(
                    name=entry.name,
                    prompt=skill_md.read_text(),
                    path=str(entry),
                )
    return skills


def inject_skill(system_prompt: str, skill: Skill) -> str:
    """Append skill instructions to the system prompt."""
    return system_prompt + f"\n\n# Skill: {skill.name}\n{skill.prompt}"
