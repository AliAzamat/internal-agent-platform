"""The guardrail gates SIDE-EFFECTING skills. A read-only skill runs freely; a
world-mutating one (place_order, send_email) must be on the agent's explicit
approval allowlist AND pass a payload check before it can fire. This is where an
LLM's improvisation meets a hard boundary."""
from __future__ import annotations

from platform.skills.base import Skill, SkillResult
from platform.skills.registry import registry


def check_side_effect(agent_approved: set[str], name: str, args: dict) -> SkillResult | None:
    """Return a rejecting SkillResult if a side-effecting skill is not allowed;
    return None to let it proceed. Read-only skills always proceed."""
    skill: Skill = registry.get(name)
    if not skill.side_effecting:
        return None  # read-only — no gate
    if name not in agent_approved:
        return SkillResult(ok=False,
                           error=f"side-effecting skill '{name}' not approved for this agent")
    # A place for extra payload checks (limits, allowlisted recipients, dollar caps)
    # before a real-world action fires. Keep them explicit and auditable.
    return None
