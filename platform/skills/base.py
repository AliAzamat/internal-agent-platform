"""A skill is the unit other teams reuse. It declares a name, a JSON schema for
its input, and whether it has side effects — then implements run(). Everything
the orchestrator can do, it does by calling a registered skill through here."""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Callable, Optional


@dataclass
class SkillResult:
    """The uniform envelope EVERY skill returns. The orchestrator never sees a
    raw exception from a skill — success or failure, it gets one of these."""
    ok: bool
    output: Any = None
    error: Optional[str] = None
    latency_ms: int = 0
    meta: dict[str, Any] = field(default_factory=dict)


@dataclass
class Skill:
    name: str
    description: str          # what an LLM planner reads to decide when to use it
    input_schema: dict[str, Any]   # JSON schema for the arguments
    handler: Callable[[dict[str, Any]], Any]
    side_effecting: bool = False   # does it mutate the outside world? gates guardrails later


def timed(fn: Callable[[dict[str, Any]], Any]) -> Callable[[dict[str, Any]], SkillResult]:
    """Wrap a raw handler so it always returns a SkillResult with latency and
    never leaks an exception into the orchestration loop."""
    def wrapped(args: dict[str, Any]) -> SkillResult:
        start = time.perf_counter()
        try:
            out = fn(args)
            ms = int((time.perf_counter() - start) * 1000)
            return SkillResult(ok=True, output=out, latency_ms=ms)
        except Exception as exc:  # a skill failing is data, not a crash
            ms = int((time.perf_counter() - start) * 1000)
            return SkillResult(ok=False, error=str(exc), latency_ms=ms)
    return wrapped
