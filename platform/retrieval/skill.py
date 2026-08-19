"""Retrieval, registered as a skill. This is the key move: grounding is not a
special path — it is one more skill any agent can be granted. search_docs embeds
the query, searches the store, and returns citation-ready passages."""
from __future__ import annotations

from typing import Any

from platform.skills.base import Skill
from platform.skills.registry import registry
from platform.retrieval.embeddings import embed_texts
from platform.retrieval.vector_store import vector_store

TOP_K = 5


def _search_docs(args: dict[str, Any]) -> dict[str, Any]:
    query = args["query"]
    k = args.get("top_k", TOP_K)
    qvec = embed_texts([query], input_type="search_query")[0]
    matches = vector_store.query(qvec, top_k=k)
    passages = [
        {"source": m.metadata["source"], "offset": m.metadata["offset"],
         "text": m.metadata["text"], "score": round(m.score, 4)}
        for m in matches
    ]
    return {"passages": passages, "count": len(passages)}


registry.register(Skill(
    name="search_docs",
    description="Search the internal document corpus for passages relevant to a "
                "query. Returns citation-ready passages with their source and "
                "offset. Use this to ground any answer in real documents.",
    input_schema={
        "type": "object",
        "properties": {
            "query": {"type": "string", "minLength": 1},
            "top_k": {"type": "integer", "minimum": 1, "maximum": 20},
        },
        "required": ["query"],
        "additionalProperties": False,
    },
    handler=_search_docs,
    side_effecting=False,
))
