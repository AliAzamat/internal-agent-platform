"""Memory persistence. Three scopes behind one repo: durable FACTS (survive the
session, upserted by key), session HISTORY (past turns), and the ephemeral run
SCRATCH which lives only in the run's transcript (not persisted here)."""
from __future__ import annotations

import uuid
from typing import Any, Optional

from platform.db.postgres import cursor


class MemoryRepo:
    def ensure_session(self, tenant_id: str, agent_id: str,
                       session_id: Optional[str] = None) -> str:
        """Get-or-create a session so a returning user threads onto the same one."""
        if session_id:
            with cursor() as cur:
                cur.execute("SELECT id FROM sessions WHERE id=%s AND tenant_id=%s",
                            (session_id, tenant_id))
                if cur.fetchone():
                    return session_id
        sid = session_id or str(uuid.uuid4())
        with cursor() as cur:
            cur.execute("INSERT INTO sessions (id, tenant_id, agent_id) VALUES (%s, %s, %s)",
                        (sid, tenant_id, agent_id))
        return sid

    def record_turn(self, session_id: str, run_id: str, goal: str, answer: str) -> None:
        with cursor() as cur:
            cur.execute(
                "INSERT INTO turns (id, session_id, run_id, goal, answer) VALUES (%s,%s,%s,%s,%s)",
                (str(uuid.uuid4()), session_id, run_id, goal, answer),
            )

    def recent_turns(self, session_id: str, limit: int = 6) -> list[dict[str, Any]]:
        """The last few (goal, answer) pairs — the conversational context we feed
        the planner so it knows what already happened in this session."""
        with cursor() as cur:
            cur.execute(
                "SELECT goal, answer FROM turns WHERE session_id=%s "
                "ORDER BY created_at DESC LIMIT %s",
                (session_id, limit),
            )
            return list(reversed(cur.fetchall()))  # oldest-first for the planner

    def put_fact(self, tenant_id: str, session_id: str, key: str, value: str) -> None:
        """Durable, upserted by (session, key): re-learning a fact overwrites it."""
        with cursor() as cur:
            cur.execute(
                """
                INSERT INTO memory_facts (id, tenant_id, session_id, key, value)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (session_id, key)
                DO UPDATE SET value = EXCLUDED.value, updated_at = now()
                """,
                (str(uuid.uuid4()), tenant_id, session_id, key, value),
            )

    def get_facts(self, session_id: str) -> dict[str, str]:
        with cursor() as cur:
            cur.execute("SELECT key, value FROM memory_facts WHERE session_id=%s", (session_id,))
            return {r["key"]: r["value"] for r in cur.fetchall()}
