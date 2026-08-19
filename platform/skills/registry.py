"""The registry: register a skill once, any agent discovers and calls it by name.
This is the seam that makes a skill 'reusable by other teams' — they publish into
the registry, consumers look up by name and get a validated, uniform call."""
from __future__ import annotations

from typing import Any

from jsonschema import Draft202012Validator, ValidationError

from platform.skills.base import Skill, SkillResult, timed


class SkillRegistry:
    def __init__(self) -> None:
        self._skills: dict[str, Skill] = {}
        self._validators: dict[str, Draft202012Validator] = {}

    def register(self, skill: Skill) -> None:
        if skill.name in self._skills:
            raise ValueError(f"skill '{skill.name}' already registered")
        # Precompile the schema validator so every call is cheap.
        self._validators[skill.name] = Draft202012Validator(skill.input_schema)
        self._skills[skill.name] = skill

    def get(self, name: str) -> Skill:
        if name not in self._skills:
            raise KeyError(f"unknown skill '{name}'")
        return self._skills[name]

    def catalog(self) -> list[dict[str, Any]]:
        """What a planner sees: name + description + schema of every skill.
        This is the 'menu' the orchestrator plans against."""
        return [
            {"name": s.name, "description": s.description,
             "input_schema": s.input_schema, "side_effecting": s.side_effecting}
            for s in self._skills.values()
        ]

    def call(self, name: str, args: dict[str, Any]) -> SkillResult:
        """Validate args against the skill's schema, then run it through the
        timed wrapper. A schema violation is a failed SkillResult, not an except."""
        skill = self.get(name)
        try:
            self._validators[name].validate(args)
        except ValidationError as exc:
            return SkillResult(ok=False, error=f"input validation failed: {exc.message}")
        return timed(skill.handler)(args)


registry = SkillRegistry()  # the process-wide registry other modules import
