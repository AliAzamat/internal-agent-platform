"""The platform's public surface. Three verbs other teams need: register an agent,
run it against a goal, and read a run's trace. The endpoints are thin — they wire
the pipeline (orchestrator + trace) behind a stable contract."""
from __future__ import annotations

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field

from platform.agent.agent import Agent
from platform.agent.orchestrator import run
from platform.observability.trace import record_run
from platform.db.postgres import cursor

router = APIRouter()

# In-memory agent registry for the MVP; a table in prod. Keyed by (tenant, id).
_AGENTS: dict[tuple[str, str], Agent] = {}


class RegisterAgent(BaseModel):
    id: str
    goal_role: str
    allowed_skills: list[str]
    max_steps: int = Field(8, ge=1, le=20)
    require_grounding: bool = False


class RunAgent(BaseModel):
    agent_id: str
    goal: str
    session_id: str | None = None


@router.post("/agents")
def register_agent(body: RegisterAgent, request: Request):
    tenant = request.state.tenant_id
    _AGENTS[(tenant, body.id)] = Agent(
        id=body.id, goal_role=body.goal_role, allowed_skills=body.allowed_skills,
        max_steps=body.max_steps, require_grounding=body.require_grounding,
    )
    return {"registered": body.id}


@router.post("/runs")
def trigger_run(body: RunAgent, request: Request):
    tenant = request.state.tenant_id
    agent = _AGENTS.get((tenant, body.agent_id))
    if agent is None:
        return {"error": {"code": "not_found", "message": "unknown agent"}}
    result = run(agent, body.goal, tenant_id=tenant, session_id=body.session_id)
    trace_id = record_run(agent.id, body.goal, result)
    return {"trace_id": trace_id, "answer": result.answer,
            "steps": result.steps, "terminated": result.terminated,
            "session_id": result.session_id}


@router.get("/runs/{trace_id}")
def get_trace(trace_id: str, request: Request):
    with cursor() as cur:
        cur.execute("SELECT * FROM run_traces WHERE id=%s", (trace_id,))
        row = cur.fetchone()
    if row is None:
        return {"error": {"code": "not_found", "message": "unknown trace"}}
    return row
