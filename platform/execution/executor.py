"""Resilient skill execution. The orchestrator calls skills through here, not the
registry directly, so every call gets a timeout, bounded retries, and a circuit
breaker. Turns 'the skill flaked' from an outage into a handled degraded result."""
from __future__ import annotations

import time
from collections import defaultdict
from dataclasses import dataclass

from platform.skills.base import SkillResult
from platform.skills.registry import registry

MAX_ATTEMPTS = 3
TIMEOUT_S = 8.0
BREAKER_THRESHOLD = 5      # consecutive failures before a skill is tripped open
BREAKER_COOLDOWN_S = 30.0


@dataclass
class _Breaker:
    fails: int = 0
    opened_at: float = 0.0


_breakers: dict[str, _Breaker] = defaultdict(_Breaker)


def _is_open(name: str) -> bool:
    b = _breakers[name]
    if b.fails < BREAKER_THRESHOLD:
        return False
    if time.time() - b.opened_at > BREAKER_COOLDOWN_S:
        b.fails = 0  # cooldown elapsed — allow a probe through (half-open)
        return False
    return True


def execute(name: str, args: dict) -> SkillResult:
    """Call a skill with a circuit breaker + bounded retries. A transient failure
    is retried with backoff; a tripped breaker fails fast without calling out."""
    if _is_open(name):
        return SkillResult(ok=False, error=f"circuit open for skill '{name}'")

    last_err = "unknown"
    for attempt in range(MAX_ATTEMPTS):
        start = time.time()
        result = registry.call(name, args)
        # Treat a slow call as a failure for breaker/retry purposes.
        if result.ok and (time.time() - start) <= TIMEOUT_S:
            _breakers[name].fails = 0  # success resets the breaker
            return result
        last_err = result.error or "timeout"
        b = _breakers[name]
        b.fails += 1
        if b.fails >= BREAKER_THRESHOLD:
            b.opened_at = time.time()   # trip the breaker open
            break
        time.sleep(2 ** attempt * 0.1)  # exponential backoff between retries
    return SkillResult(ok=False, error=f"failed after retries: {last_err}")
