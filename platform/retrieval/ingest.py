"""Ingest a document into overlapping chunks and embed them into the vector store.
Chunks keep the source and an offset so a retrieved passage is citable back to a
place a human can open."""
from __future__ import annotations

import uuid
from dataclasses import dataclass

from platform.retrieval.embeddings import embed_texts
from platform.retrieval.vector_store import vector_store

CHUNK_CHARS = 1200
OVERLAP_CHARS = 200


@dataclass
class Chunk:
    chunk_id: str
    doc_id: str
    source: str
    offset: int
    text: str


def _chunk(doc_id: str, source: str, text: str) -> list[Chunk]:
    step = CHUNK_CHARS - OVERLAP_CHARS
    chunks: list[Chunk] = []
    for offset in range(0, max(1, len(text)), step):
        window = text[offset : offset + CHUNK_CHARS]
        if not window.strip():
            continue
        chunks.append(Chunk(str(uuid.uuid4()), doc_id, source, offset, window))
    return chunks


def ingest_document(source: str, text: str) -> int:
    """Chunk, embed, and upsert into the vector store. Returns the chunk count.
    Vector ids are the chunk ids, so re-ingesting the same doc overwrites cleanly."""
    doc_id = str(uuid.uuid4())
    chunks = _chunk(doc_id, source, text)
    embeddings = embed_texts([c.text for c in chunks], input_type="search_document")
    vectors = [
        (c.chunk_id, emb, {"doc_id": c.doc_id, "source": c.source,
                           "offset": c.offset, "text": c.text})
        for c, emb in zip(chunks, embeddings)
    ]
    vector_store.upsert(vectors)
    return len(chunks)
