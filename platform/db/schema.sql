-- Sessions group turns for one user working with one agent over time.
CREATE TABLE IF NOT EXISTS sessions (
    id            UUID PRIMARY KEY,
    tenant_id     TEXT        NOT NULL DEFAULT 'default',
    agent_id      TEXT        NOT NULL,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Turns: the durable conversation history for a session. Each turn is one
-- user goal and the agent's final answer, with the run id that produced it.
CREATE TABLE IF NOT EXISTS turns (
    id            UUID PRIMARY KEY,
    session_id    UUID        NOT NULL REFERENCES sessions (id) ON DELETE CASCADE,
    run_id        UUID        NOT NULL,
    goal          TEXT        NOT NULL,
    answer        TEXT        NOT NULL,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Durable facts: things the agent learned that should survive the session.
-- Scoped to (tenant, session) with a key so writes upsert instead of piling up.
CREATE TABLE IF NOT EXISTS memory_facts (
    id            UUID PRIMARY KEY,
    tenant_id     TEXT        NOT NULL DEFAULT 'default',
    session_id    UUID        NOT NULL REFERENCES sessions (id) ON DELETE CASCADE,
    key           TEXT        NOT NULL,
    value         TEXT        NOT NULL,
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (session_id, key)
);
