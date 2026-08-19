"""An Agent is CONFIG over the platform, not code. It names the skills it may use
(a subset of the registry — least privilege), a step budget, and a system role.
This is what other teams author to stand up a new agent."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Agent:
    id: str
    goal_role: str                         # human description of the agent's purpose
    allowed_skills: list[str]              # subset of the registry this agent may call
    max_steps: int = 8                     # hard budget so a run always terminates
    require_grounding: bool = False        # set by retrieval-backed agents (later step)
    metadata: dict = field(default_factory=dict)
