"""Ordered, independently resolved attempts in one atomic player command."""

from copy import deepcopy
from typing import Annotated
from pydantic import Field, JsonValue
from . import balance as bal

Identifier = Annotated[str, Field(pattern=r"^[a-zA-Z0-9_-]{1,40}$")]


class Attempt(bal.Strict):
    id: Identifier
    kind: Identifier
    args: dict[str, JsonValue]
    depends_on: Annotated[list[Identifier], Field(max_length=8)]


class Batch(bal.Strict):
    attempts: Annotated[list[Attempt], Field(min_length=2, max_length=8)]


# Actions requiring extra choices or a destructive confirmation remain independent
# commands. A supplied ID does not make an absent action available in the world.
SEPARATE = {
    "present_item",
    "advance",
    "set_balance",
    "batch",
    "destroy_note",
    "confirm_note",
    "career_exit",
    "hearing",
    "stage_end",
    "confirm_risk",
    "career_end",
    "finding",
}


def resolve_attempts(context, graph):
    from . import world
    from .engine import Context, GameError

    prior = set()
    for item in graph.attempts:
        if (
            item.id in prior
            or not set(item.depends_on) <= prior
            or len(item.depends_on) != len(set(item.depends_on))
        ):
            raise GameError(
                "invalid_input",
                "每个子行动须有不同编号，依赖只能引用排在前面的子行动。",
            )
        if item.kind in SEPARATE:
            raise GameError("invalid_input", "这项操作需要单独确认。")
        prior.add(item.id)
    completed, receipts = set(), []
    state = context.state
    for item in graph.attempts:
        if not set(item.depends_on) <= completed:
            receipts.append(
                {"id": item.id, "status": "blocked", "text": "前置行动未受理。"}
            )
            continue
        options = world.actions(state["domain"])
        selected = next(
            (
                a
                for a in options
                if a["kind"] == item.kind
                and a.get("args", {}) == item.args
                and not a.get("confirm")
                and not a.get("fields")
            ),
            None,
        )
        if not selected:
            receipts.append(
                {
                    "id": item.id,
                    "status": "unavailable",
                    "text": "当前条件下无法办理这项行动。",
                }
            )
            continue
        trial = Context(deepcopy(state))
        trial.scope = context.scope + "/" + item.id
        try:
            world.act(trial.state["domain"], item.kind, item.args, trial)
        except ValueError:
            receipts.append(
                {
                    "id": item.id,
                    "status": "unavailable",
                    "text": selected["label"] + "未受理。",
                }
            )
            continue
        state = trial.state
        context.events.extend(trial.events)
        completed.add(item.id)
        receipts.append(
            {
                "id": item.id,
                "status": "accepted",
                "text": "已受理：" + selected["label"] + "。",
            }
        )
    state["last_action_results"] = receipts
    return state
