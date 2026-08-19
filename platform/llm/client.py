"""LLM client seam. One function the rest of the platform calls; the provider
lives behind it so the whole platform is model-agnostic. Low temperature keeps
planning reproducible for evaluation."""
from __future__ import annotations

import os
from typing import Any

# The concrete SDK is intentionally behind this seam. In tests, monkeypatch
# chat_json; in prod, point it at your provider. The platform never imports a
# vendor SDK anywhere else.
_PROVIDER = os.environ.get("LLM_PROVIDER", "mock")


def chat_json(system: str, user: str, temperature: float = 0.1) -> str:
    if _PROVIDER == "mock":
        # Deterministic stub so the platform runs end-to-end with no key.
        return '{"action": "finish", "answer": "mock planner answer"}'
    from platform.llm.providers import call_provider  # lazy import per provider
    return call_provider(_PROVIDER, system, user, temperature)
