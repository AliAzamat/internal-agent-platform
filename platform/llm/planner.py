"""The planner asks the model, given a goal and the skill catalog, which single
skill to call next (or to finish). We force a strict JSON decision so the loop is
deterministic to parse. The provider is abstracted — swap the client, keep the
contract."""
from __future__ import annotations

import json
import os
from typing import Any

from platform.llm.client import chat_json

PLANNER_SYSTEM = """You are the planner for an internal agent platform.
Given a GOAL, the conversation so far, and a CATALOG of skills (name, description,
input schema), decide the single next action.

Return ONLY valid JSON, one of:
  {"action": "call_skill", "skill": "<name>", "args": {...}, "why": "<short reason>"}
  {"action": "finish", "answer": "<final answer to the goal>"}

Rules:
- Call a skill only if you need its result to make progress.
- Pass args that satisfy the skill's input schema exactly.
- When you have enough to answer the goal, finish.
- Never invent a skill that is not in the catalog."""


def plan_next(goal: str, catalog: list[dict[str, Any]], transcript: list[dict[str, Any]]) -> dict[str, Any]:
    """Return the model's next-action decision as a parsed dict. On unparseable
    output, fail soft to a finish with an honest 'I got stuck' answer."""
    user = json.dumps({"goal": goal, "catalog": catalog, "transcript": transcript})
    raw = chat_json(PLANNER_SYSTEM, user)
    try:
        decision = json.loads(raw)
    except json.JSONDecodeError:
        return {"action": "finish", "answer": "Unable to plan a next step."}
    if decision.get("action") not in ("call_skill", "finish"):
        return {"action": "finish", "answer": "Planner returned an unknown action."}
    return decision
