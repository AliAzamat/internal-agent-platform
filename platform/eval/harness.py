"""The eval harness. Run a suite of task cases against an agent and score each on
task-completion (did the answer satisfy the check?) and grounding (did it cite
sources when required?). Emits an aggregate report — the gate you ship behind."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from platform.agent.agent import Agent
from platform.agent.orchestrator import run
from platform.agent.grounding import is_grounded


@dataclass
class TaskCase:
    goal: str
    check: Callable[[str], bool]   # does the final answer satisfy the task?
    must_ground: bool = False      # must this case produce a citation?


@dataclass
class CaseResult:
    goal: str
    completed: bool
    grounded: bool
    grounding_ok: bool
    steps: int


def evaluate(agent: Agent, suite: list[TaskCase]) -> dict[str, Any]:
    results: list[CaseResult] = []
    for case in suite:
        rr = run(agent, case.goal)
        completed = case.check(rr.answer)
        grounded = is_grounded(rr.transcript)
        # A grounding-required case passes grounding only if it actually grounded.
        grounding_ok = (not case.must_ground) or grounded
        results.append(CaseResult(case.goal, completed, grounded, grounding_ok, rr.steps))

    n = len(results) or 1
    completion_rate = sum(r.completed for r in results) / n
    grounding_rate = sum(r.grounding_ok for r in results) / n
    return {
        "cases": len(results),
        "completion_rate": round(completion_rate, 3),
        "grounding_rate": round(grounding_rate, 3),
        "passed": completion_rate >= 0.8 and grounding_rate >= 0.95,
        "details": results,
    }
