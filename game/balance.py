"""One versioned numerical policy shared by every world, action and opportunity."""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field

REGISTRY = json.loads(
    (Path(__file__).resolve().parents[1] / "PARAMETER_REGISTRY.json").read_text()
)
RULES = {entry["key"]: entry for entry in REGISTRY["parameters"]}
TRANSITION = REGISTRY["transition_minutes"]
CALC_VERSION = REGISTRY["calculation_version"]


def canonical(value) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def digest(value) -> str:
    return hashlib.sha256(canonical(value).encode("utf-8")).hexdigest()


PACKAGE_HASH = digest(REGISTRY)
CanonicalBalance = Annotated[
    str, Field(min_length=8, max_length=8, pattern=r"^(0\.[0-9]{6}|1\.000000)$")
]
Name = Annotated[str, Field(min_length=1, max_length=96)]
Minute = Annotated[int, Field(ge=0)]


class Strict(BaseModel):
    model_config = ConfigDict(
        strict=True, extra="forbid", frozen=True, allow_inf_nan=False
    )


class PolicySetting(Strict):
    balance: CanonicalBalance
    expected_policy_version: Annotated[int, Field(ge=1)]
    parameter_package_hash: Annotated[
        str, Field(min_length=64, max_length=64, pattern=r"^[0-9a-f]{64}$")
    ]


class PolicyCommand(Strict):
    command_id: Name
    expected_revision: Minute
    kind: Literal["set_balance"]
    args: PolicySetting


class PolicyEvent(Strict):
    event_domain: Literal["simulation_control"]
    start_minute: Minute
    b_start: Annotated[float, Field(ge=0, le=1)]
    target: CanonicalBalance
    previous_version: Annotated[int, Field(ge=1)]
    version: Annotated[int, Field(ge=2)]
    transition_minutes: Annotated[int, Field(ge=240, le=240)]
    calculation_version: Name
    parameter_package_hash: Annotated[
        str, Field(pattern=r"^[a-f0-9]{64}$", min_length=64, max_length=64)
    ]
    cause: Name


def initial_policy(target):
    return {"target": target, "start": float(target), "minute": 0, "version": 1}


def effective(policy, minute):
    """Evaluate the trajectory without rounding an effective value at reanchor."""
    target = float(policy["target"])
    t = (minute - policy["minute"]) / TRANSITION
    if t <= 0:
        return policy["start"]
    if t >= 1:
        return target
    value = policy["start"] + (target - policy["start"]) * (t * t * (3 - 2 * t))
    return max(0.0, min(1.0, value))


def integral(policy, start, end):
    if end < start:
        raise ValueError("时间区间无效")
    base = policy["start"]
    delta = float(policy["target"]) - base
    # Integrate only the ramp in its local coordinate system; use exact
    # constant tails to avoid subtracting large nearby values on long careers.
    anchor = policy["minute"]
    duration = TRANSITION
    t1 = max(0.0, min(1.0, (start - anchor) / duration))
    t2 = max(0.0, min(1.0, (end - anchor) / duration))

    def area(t):
        return t**3 - t**4 / 2

    constant_tail = max(0.0, end - max(start, anchor + duration))
    return max(
        0.0,
        base * (end - start)
        + delta * (duration * (area(t2) - area(t1)) + constant_tail),
    )


def parameters(b):
    if not math.isfinite(b) or not 0 <= b <= 1:
        raise ValueError("取向须在零和一之间")
    values = {}
    for key, rule in RULES.items():
        if rule["formula"] == "linear":
            values[key] = 1 + rule["slope"] * b
        elif rule["formula"] == "power":
            values[key] = rule["base"] ** b
        else:
            values[key] = (1 - b, b)
    return values


def delta_hazard(policy, start, end, process_key, intensity):
    return intensity * (
        (end - start) + RULES[process_key]["slope"] * integral(policy, start, end)
    )


def uniform(seed, slot):
    # A 52-bit midpoint is representable and strictly inside (0,1), including
    # the top bin. No wall clock, language hash randomization or policy version.
    ix = int(digest([seed, slot])[:13], 16)
    return (ix + 0.5) / 2**52


def distribution(candidates, b):
    if "none" not in candidates or not candidates:
        raise ValueError("候选池缺少 none")
    if any(
        len(pair) != 2 or any(not math.isfinite(v) or not 0 <= v <= 1 for v in pair)
        for pair in candidates.values()
    ):
        raise ValueError("候选分值超出范围")
    scores = {k: (1 - b) * r + b * g for k, (r, g) in sorted(candidates.items())}
    top = max(scores.values())
    weights = {
        k: math.exp((s - top) / REGISTRY["temperature"]) for k, s in scores.items()
    }
    total = math.fsum(weights.values())
    return {k: w / total for k, w in weights.items()}


def pick(weights, u):
    entries = sorted(weights.items())
    if not entries or any(v < 0 or not math.isfinite(v) for _, v in entries):
        raise ValueError("候选权重无效")
    positive = [(k, w) for k, w in entries if w > 0]
    if not positive:
        raise ValueError("没有合格候选")
    target = u * math.fsum(w for _, w in positive)
    accumulated = 0.0
    for key, weight in positive:
        accumulated += weight
        if target < accumulated:
            return key
    return positive[-1][0]


def counteroffer(p, b):
    w = parameters(b)["counteroffer_weight"]
    return p * w / ((1 - p) + p * w)
