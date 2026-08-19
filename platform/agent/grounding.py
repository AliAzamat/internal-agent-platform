"""Grounding enforcement. For an agent with require_grounding=True, a run's final
answer must trace to at least one citation from a retrieval/synthesis skill, or
the run is flagged ungrounded — the platform's honesty guarantee."""
from __future__ import annotations

from typing import Any


def extract_citations(transcript: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Pull citations out of any synthesize_answer skill outputs in the run."""
    citations: list[dict[str, Any]] = []
    for entry in transcript:
        if entry.get("skill") == "synthesize_answer" and entry.get("ok"):
            out = entry.get("output") or {}
            citations.extend(out.get("citations", []))
    return citations


def is_grounded(transcript: list[dict[str, Any]]) -> bool:
    """A run is grounded if it produced at least one citation. An honest
    'I don't know' produces none — which is a legitimate grounded outcome only
    when the answer itself admits it, so we check citations OR an explicit
    unknown answer at the call site."""
    return len(extract_citations(transcript)) > 0
