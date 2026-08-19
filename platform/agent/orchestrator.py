"""The plan-act-observe loop, now MEMORY-AWARE. Before planning, it loads the
session's recent turns and durable facts and injects them into the planner's
context. After finishing, it records the turn so the next call has it."""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any, Optional

from platform.agent.agent import Agent
from platform.skills.registry import registry
from platform.llm.planner import plan_next
from platform.memory.repository import MemoryRepo

memory = MemoryRepo()


@dataclass
class RunResult:
    answer: str
    steps: int
    run_id: str
    session_id: str
    transcript: list[dict[str, Any]] = field(default_factory=list)
    terminated: str = "finished"


def _scoped_catalog(agent: Agent) -> list[dict[str, Any]]:
    allowed = set(agent.allowed_skills)
    return [s for s in registry.catalog() if s["name"] in allowed]


def run(agent: Agent, goal: str, tenant_id: str = "default",
        session_id: Optional[str] = None) -> RunResult:
    run_id = str(uuid.uuid4())
    session_id = memory.ensure_session(tenant_id, agent.id, session_id)

    # Load memory: recent turns (history) + durable facts, injected as context.
    history = memory.recent_turns(session_id)
    facts = memory.get_facts(session_id)
    catalog = _scoped_catalog(agent)
    transcript: list[dict[str, Any]] = []

    for step in range(agent.max_steps):
        context = {"history": history, "facts": facts, "scratch": transcript}
        decision = plan_next(goal, catalog, context)

        if decision["action"] == "finish":
            answer = decision.get("answer", "")
            memory.record_turn(session_id, run_id, goal, answer)  # persist the turn
            return RunResult(answer=answer, steps=step, run_id=run_id,
                             session_id=session_id, transcript=transcript)

        skill_name = decision["skill"]
        if skill_name not in agent.allowed_skills:
            transcript.append({"skill": skill_name, "ok": False,
                               "error": "skill not permitted for this agent"})
            continue

        result = registry.call(skill_name, decision.get("args", {}))
        transcript.append({
            "skill": skill_name, "args": decision.get("args", {}),
            "ok": result.ok, "output": result.output,
            "error": result.error, "latency_ms": result.latency_ms,
        })

    memory.record_turn(session_id, run_id, goal, "Step budget exhausted.")
    return RunResult(answer="Step budget exhausted before completing the task.",
                     steps=agent.max_steps, run_id=run_id, session_id=session_id,
                     transcript=transcript, terminated="budget_exhausted")
