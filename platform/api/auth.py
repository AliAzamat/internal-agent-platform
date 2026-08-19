"""Per-key tenant scoping. A key maps to a tenant; every run and every memory
read is scoped to it so no team can trigger runs or read traces in another
tenant. The tenant comes from the credential, never from the request body."""
from __future__ import annotations

import os

from fastapi import Request
from fastapi.responses import JSONResponse

PUBLIC_PATHS = {"/health", "/docs", "/openapi.json"}


def _keys() -> dict[str, str]:
    raw = os.environ.get("PLATFORM_API_KEYS", "dev-key:default")
    out: dict[str, str] = {}
    for pair in raw.split(","):
        if ":" in pair:
            k, t = pair.split(":", 1)
            out[k.strip()] = t.strip()
    return out


_KEY_MAP = _keys()


async def tenant_auth(request: Request, call_next):
    if request.url.path in PUBLIC_PATHS:
        return await call_next(request)
    tenant = _KEY_MAP.get(request.headers.get("X-API-Key", ""))
    if tenant is None:
        return JSONResponse(status_code=401,
            content={"error": {"code": "unauthorized", "message": "invalid API key"}})
    request.state.tenant_id = tenant   # downstream reads the tenant from here
    return await call_next(request)
