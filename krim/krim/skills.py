"""Skill system - reusable prompt + script packages.

Skills are directories under ~/.krim/skills/ or ./skills/ containing:
  SKILL.md  - description and instructions (appended to system prompt when active)
  *.sh      - optional helper scripts the model can reference

Usage:
  krim --skill git-commit "fix the login bug and commit"
  krim --skill deploy "deploy to production"
"""

import os
from dataclasses import dataclass


@dataclass
class Skill:
    name: str
    prompt: str  # contents of SKILL.md
    path: str    # directory path


def discover_skills() -> dict[str, Skill]:
    """Find all available skills from ~/.krim/skills/ and ./skills/"""
    skills = {}
    search_dirs = [
        os.path.expanduser("~/.krim/skills"),
        os.path.join(os.getcwd(), "skills"),
    ]
    for base in search_dirs:
        if not os.path.isdir(base):
            continue
        for name in os.listdir(base):
            skill_dir = os.path.join(base, name)
            skill_md = os.path.join(skill_dir, "SKILL.md")
            if os.path.isfile(skill_md):
                with open(skill_md) as f:
                    prompt = f.read()
                skills[name] = Skill(name=name, prompt=prompt, path=skill_dir)
    return skills


def inject_skill(system_prompt: str, skill: Skill) -> str:
    """Append skill instructions to the system prompt."""
    return system_prompt + f"\n\n# Skill: {skill.name}\n{skill.prompt}"
