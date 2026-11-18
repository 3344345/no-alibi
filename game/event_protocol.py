"""Versioned journal contracts and causal links for the scheduler."""

from __future__ import annotations
from typing import Annotated, Literal
from pydantic import Field
from . import balance

NonNegative = Annotated[float, Field(ge=0)]
Count = Annotated[int, Field(ge=0)]
HASH = Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]


class ParameterBinding(balance.Strict):
    binding_id: str
    bound_at_minute: Count
    policy_version: Annotated[int, Field(ge=1)]
    balance_eff: Annotated[float, Field(ge=0, le=1)]
    parameter_package_hash: HASH
    calculation_version: str
    parameters: dict[str, float | tuple[float, float]]


class BoundDuration(balance.Strict):
    channel: Literal["admin", "message_queue"]
    floor: NonNegative
    extra: NonNegative
    raw: NonNegative
    rounded: Count
    elapsed: Count
    working: bool
    binding: ParameterBinding


class SealedChoice(balance.Strict):
    slot: str
    sample: Annotated[float, Field(gt=0, lt=1)]
    candidate_hash: HASH
    weights: dict[str, NonNegative]
    outcome: str
    binding: ParameterBinding


class CrossedThreshold(balance.Strict):
    process: str
    slot: str
    threshold: NonNegative
    intensity: NonNegative
    generation: Count


class ModelSelection(balance.Strict):
    context_hash: HASH
    role: Literal["npc_propose", "case_propose"]
    subject: str
    selected: str
    provider_model: str


class QuarantinedTask(balance.Strict):
    task_id: str
    root: str
    parent: str
    reason: Literal["same_minute_depth", "same_minute_fanout"]


PAYLOADS = {
    "AttemptUnfulfilled": None,
    "ModelCandidateApplied": ModelSelection,
    "world": None,
    "CareerStarted": None,
    "DurationBound": BoundDuration,
    "ChoiceSealed": SealedChoice,
    "OpportunityCrossed": CrossedThreshold,
    "SimulationPolicyChanged": balance.PolicyEvent,
    "TaskQuarantined": QuarantinedTask,
}


def check_event(kind, visible, data):
    if kind not in PAYLOADS:
        raise ValueError("事件类型未登记。")
    model = PAYLOADS[kind]
    if model is None:
        if data is not None:
            raise ValueError("此类事件不接受附加字段。")
    elif visible:
        raise ValueError("内部审计记录不能投递给玩家。")
    else:
        model.model_validate_json(balance.canonical(data))


def lineage(ctx, delay):
    parent = ctx.active_task
    if parent is None:
        return {"root": ctx.scope, "parent": ctx.scope, "depth": 1, "same_minute": 0}
    old = parent.get("lineage", {})
    return {
        "root": old.get("root", parent["id"]),
        "parent": parent["id"],
        "depth": old.get("depth", 0) + 1,
        "same_minute": 0 if delay else old.get("same_minute", 0) + 1,
    }
