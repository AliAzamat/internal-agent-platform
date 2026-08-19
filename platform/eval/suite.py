"""A small task suite. Each case is a goal plus a check on the final answer. Real
suites grow from production failures — every bad answer a user flags becomes a
regression case here so it can never silently return."""
from __future__ import annotations

from platform.eval.harness import TaskCase


def contains(substr: str):
    return lambda answer: substr.lower() in (answer or "").lower()


SUITE = [
    TaskCase(goal="What is 12 times 8?", check=contains("96")),
    TaskCase(goal="What sector is ticker GLOB in?", check=contains("technology")),
    TaskCase(
        goal="According to our onboarding doc, what is the PTO policy?",
        check=contains("pto"),
        must_ground=True,   # this must cite a document, not free-associate
    ),
]
