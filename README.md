Internal Agent Platform — Skills, Memory & Retrieval

An advanced capstone. You build the platform an Applied AI team actually ships internally — not a demo. A registry of reusable, typed "skills" any agent can call; an orchestrator that plans, invokes skills, and reasons across multiple steps; shared memory that carries context across turns and sessions, persisted in Postgres; a retrieval layer that indexes a real document corpus and grounds answers in it with citations; an eval harness that measures task-completion and grounding so you ship on evidence, not vibes; the production concerns that separate a survivable system from a demo — tool-failure handling, retries, guardrails, and per-run observability; and a thin FastAPI surface plus a control UI so other teams trigger agents against real workflows. Throughout, the framing is a reusable platform other teams adopt.

## Stack
- Python
- agent framework
- vector store
- PostgreSQL
- FastAPI
