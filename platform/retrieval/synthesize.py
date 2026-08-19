"""Synthesis: answer a question from passages ONLY, with citations. This is the
lever against hallucination — the model is told to use only what it is given and
to admit ignorance. Registered as a side-effect-free skill."""
from __future__ import annotations

import json
from typing import Any

from platform.skills.base import Skill
from platform.skills.registry import registry
from platform.llm.client import chat_json

SYNTH_SYSTEM = """You answer using ONLY the numbered passages provided.
Rules:
- If the passages do not contain the answer, set "answer" to
  "I don't know based on the provided documents." and "citations" to [].
- Cite the numbers (e.g. [1,3]) of every passage you used.
- Never use outside knowledge or invent facts.
Return ONLY valid JSON: {"answer": str, "citations": [int]}"""


def _synthesize(args: dict[str, Any]) -> dict[str, Any]:
    question = args["question"]
    passages = args["passages"]
    numbered = "\n\n".join(
        f"[{i}] (source: {p['source']}) {p['text']}"
        for i, p in enumerate(passages, start=1)
    )
    raw = chat_json(SYNTH_SYSTEM, f"Passages:\n{numbered}\n\nQuestion: {question}")
    try:
        result = json.loads(raw)
    except json.JSONDecodeError:
        return {"answer": "I don't know based on the provided documents.", "citations": []}
    # Resolve cited numbers back to full source references for the UI.
    used = set(result.get("citations", []))
    resolved = [
        {"n": i, "source": p["source"], "offset": p["offset"]}
        for i, p in enumerate(passages, start=1) if i in used
    ]
    return {"answer": result.get("answer", ""), "citations": resolved}


registry.register(Skill(
    name="synthesize_answer",
    description="Answer a question using ONLY the given passages, with citations, "
                "or say 'I don't know' if unsupported. Use after search_docs to "
                "produce a grounded answer.",
    input_schema={
        "type": "object",
        "properties": {
            "question": {"type": "string", "minLength": 1},
            "passages": {"type": "array", "items": {"type": "object"}},
        },
        "required": ["question", "passages"],
        "additionalProperties": False,
    },
    handler=_synthesize,
    side_effecting=False,
))
