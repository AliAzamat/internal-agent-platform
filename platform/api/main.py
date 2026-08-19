from __future__ import annotations

from fastapi import FastAPI

from platform.db.postgres import init_schema
from platform.api.auth import tenant_auth
from platform.api.routes import router
import platform.skills.builtin       # noqa: F401 — registers builtin skills
import platform.retrieval.skill      # noqa: F401 — registers search_docs
import platform.retrieval.synthesize # noqa: F401 — registers synthesize_answer

app = FastAPI(title="Internal Agent Platform")
app.middleware("http")(tenant_auth)


@app.on_event("startup")
def _startup() -> None:
    init_schema()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(router)
