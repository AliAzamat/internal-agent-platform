"""One structured trace per run. It flattens the orchestrator's RunResult into a
row: which agent, the goal, every skill call with latency and ok/fail, the final
answer, whether it was grounded. This is the raw material the eval harness and any
dashboard read — observe the run, don't guess about it."""
from __future__ import annotations

import json
import uuid
from typing import Any

from platform.db.postgres import cursor
from platform.agent.grounding import is_grounded


def record_run(agent_id: str, goal: str, result: Any) -> str:
    """Persist a run trace. result is the orchestrator RunResult."""
    trace_id = str(uuid.uuid4())
    calls = result.transcript
    skill_calls = len(calls)
    failed_calls = sum(1 for c in calls if not c.get("ok"))
    total_latency = sum(c.get("latency_ms", 0) for c in calls)
    grounded = is_grounded(calls)
    with cursor() as cur:
        cur.execute(
            """
            INSERT INTO run_traces
              (id, agent_id, run_id, goal, answer, steps, skill_calls,
               failed_calls, total_latency_ms, grounded, terminated, transcript)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s::jsonb)
            """,
            (trace_id, agent_id, result.run_id, goal, result.answer, result.steps,
             skill_calls, failed_calls, total_latency, grounded,
             result.terminated, json.dumps(calls)),
        )
    return trace_id
