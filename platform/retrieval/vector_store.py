"""Vector store abstraction. A tiny upsert/query interface so the concrete store
(pgvector, Pinecone, an in-memory index for tests) is swappable. Retrieval code
never imports a vendor client — only this."""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any


@dataclass
class Match:
    id: str
    score: float
    metadata: dict[str, Any]


class InMemoryVectorStore:
    """A cosine-similarity store good enough for the MVP and for deterministic
    tests. The interface is the contract; a prod store implements the same two
    methods against pgvector or Pinecone."""
    def __init__(self) -> None:
        self._items: list[tuple[str, list[float], dict[str, Any]]] = []

    def upsert(self, vectors: list[tuple[str, list[float], dict[str, Any]]]) -> None:
        ids = {v[0] for v in vectors}
        self._items = [it for it in self._items if it[0] not in ids]  # overwrite by id
        self._items.extend(vectors)

    def query(self, embedding: list[float], top_k: int) -> list[Match]:
        def cosine(a: list[float], b: list[float]) -> float:
            dot = sum(x * y for x, y in zip(a, b))
            na = math.sqrt(sum(x * x for x in a)) or 1.0
            nb = math.sqrt(sum(y * y for y in b)) or 1.0
            return dot / (na * nb)

        scored = [Match(i, cosine(embedding, vec), md) for i, vec, md in self._items]
        scored.sort(key=lambda m: m.score, reverse=True)
        return scored[:top_k]


vector_store = InMemoryVectorStore()
