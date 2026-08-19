"""Two concrete skills, registered at import time. They are deliberately mundane
(math, a mocked lookup) — the point is the CONTRACT, not the cleverness. Real
teams register their own: 'query_positions', 'fetch_filing', 'run_backtest'."""
from __future__ import annotations

from typing import Any

from platform.skills.base import Skill
from platform.skills.registry import registry


def _calculate(args: dict[str, Any]) -> float:
    a, b, op = args["a"], args["b"], args["op"]
    if op == "add":
        return a + b
    if op == "mul":
        return a * b
    if op == "div":
        if b == 0:
            raise ValueError("division by zero")
        return a / b
    raise ValueError(f"unsupported op: {op}")


registry.register(Skill(
    name="calculate",
    description="Do exact arithmetic on two numbers. Use for any math the model "
                "must not eyeball. op is one of add, mul, div.",
    input_schema={
        "type": "object",
        "properties": {
            "a": {"type": "number"},
            "b": {"type": "number"},
            "op": {"type": "string", "enum": ["add", "mul", "div"]},
        },
        "required": ["a", "b", "op"],
        "additionalProperties": False,
    },
    handler=_calculate,
    side_effecting=False,
))


def _lookup_ticker(args: dict[str, Any]) -> dict[str, Any]:
    # Stand-in for a real internal data service. Deterministic for the MVP.
    table = {"ACME": {"name": "Acme Corp", "sector": "Industrials"},
             "GLOB": {"name": "Globex", "sector": "Technology"}}
    sym = args["symbol"].upper()
    if sym not in table:
        raise KeyError(f"unknown symbol {sym}")
    return {"symbol": sym, **table[sym]}


registry.register(Skill(
    name="lookup_ticker",
    description="Resolve a stock ticker symbol to its company name and sector "
                "from the internal reference service.",
    input_schema={
        "type": "object",
        "properties": {"symbol": {"type": "string", "minLength": 1}},
        "required": ["symbol"],
        "additionalProperties": False,
    },
    handler=_lookup_ticker,
    side_effecting=False,
))
