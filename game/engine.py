"""Pure game-time resolution. I/O, world identity and commits live in store.py."""

from __future__ import annotations

import math
from copy import deepcopy
from typing import Annotated

from pydantic import Field, JsonValue, ValidationError

from . import balance as bal
from . import event_protocol

QUARTER_MINUTES = 90 * 1440
MAX_ADVANCE = QUARTER_MINUTES * 120
MAX_STEPS = 8192
# Rate per eligible game minute. Domain eligibility and attention load gate each
# channel independently. The sample rates in the design appendix are fixtures.
PROCESSES = {
    "verification": ("verification_rate", 1 / (2 * 1440)),
    "repair": ("repair_rate", 1 / (3 * 1440)),
    "case": ("optional_case_rate", 1 / (7 * 1440)),
    "rework": ("optional_rework", 1 / (8 * 1440)),
}


class GameError(ValueError):
    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message
        super().__init__(message)


class NewCareer(bal.Strict):
    start: Annotated[str, Field(pattern=r"^S0[1-8]$")]
    name: Annotated[str, Field(min_length=1, max_length=32)]
    balance: bal.CanonicalBalance
    seed: Annotated[str, Field(min_length=1, max_length=128)]


class Command(bal.Strict):
    command_id: bal.Name
    expected_revision: bal.Minute
    kind: bal.Name
    args: dict[str, JsonValue]


class Advance(bal.Strict):
    minutes: Annotated[int, Field(ge=1, le=MAX_ADVANCE)] | None = None


def checked(cls, data):
    try:
        return cls.model_validate(data)
    except ValidationError as exc:
        message = "、".join(".".join(map(str, e["loc"])) for e in exc.errors()[:4])
        raise GameError("invalid_input", f"请检查输入字段（{message}）。") from exc


def work_elapsed(start, duration):
    """Calendar time for business minutes, day 1 Monday, epoch at 09:00."""
    cursor = start
    remaining = duration
    while remaining:
        day, local = divmod(cursor + 9 * 60, 1440)
        if day % 7 >= 5:
            cursor += (7 - day % 7) * 1440 - local + 9 * 60
            continue
        if local < 9 * 60:
            cursor += 9 * 60 - local
            continue
        if local >= 17 * 60:
            cursor += 1440 - local + 9 * 60
            continue
        chunk = min(remaining, 17 * 60 - local)
        cursor += chunk
        remaining -= chunk
    return cursor - start


class Context:
    """Domain callbacks may only plan effects within this isolated resolution."""

    def __init__(self, state, proposals=None, collect=None):
        self.proposals = proposals or {}
        self.collect = collect
        self.state = state
        self.events = []
        self.scope = "world"
        self.active_task = None
        self.immediate_counts = {}
        self.binding = None

    @property
    def minute(self):
        return self.state["minute"]

    @property
    def seed(self):
        return self.state["rng_seed"]

    @property
    def params(self):
        return bal.parameters(bal.effective(self.state["policy"], self.minute))

    def bind(self, label):
        p = self.state["policy"]
        return {
            "binding_id": f"{self.scope}/{label}",
            "bound_at_minute": self.minute,
            "policy_version": p["version"],
            "balance_eff": bal.effective(p, self.minute),
            "parameter_package_hash": bal.PACKAGE_HASH,
            "calculation_version": bal.CALC_VERSION,
            "parameters": self.params,
        }

    def emit(
        self,
        text,
        *,
        title="",
        kind="world",
        visible=True,
        actor="player",
        refs=(),
        data=None,
    ):
        event_protocol.check_event(kind, visible, data)
        state = self.state
        state["sequence"] += 1
        event = {
            "id": f"{state['stream']}/e{state['sequence']}",
            "minute": self.minute,
            "kind": kind,
            "title": title,
            "text": text,
            "actor": actor,
            "refs": list(refs),
            "visible": visible,
            "cause": self.scope,
            "schema_version": "game-event/1",
        }
        if data is not None:
            event["data"] = deepcopy(data)
        self.events.append(event)
        if visible:
            state["visible_sequence"] = state.get("visible_sequence", 0) + 1
            state["timeline"].append(
                {
                    k: event[k]
                    for k in ("id", "minute", "kind", "title", "text", "actor", "refs")
                }
            )
            if len(state["timeline"]) > 200:
                del state["timeline"][:-200]
        return event["id"]

    def suggest(self, menu, fallback):
        keys = {row.key for row in menu.choices}
        if fallback not in keys or len(keys) < 2:
            return fallback
        if not self.proposals and self.collect is None:
            return fallback
        menu_hash = bal.digest(menu.model_dump(mode="json"))
        if self.collect is not None and len(self.collect) < 4:
            self.collect[menu_hash] = menu
        proposed = self.proposals.get(menu_hash)
        if not proposed or proposed["key"] not in keys:
            return fallback
        self.emit(
            "",
            kind="ModelCandidateApplied",
            visible=False,
            data={
                "context_hash": menu_hash,
                "role": menu.role,
                "subject": menu.subject,
                "selected": proposed["key"],
                "provider_model": proposed["model"],
            },
        )
        return proposed["key"]

    def duration(self, channel, floor, extra, working=False):
        key = {
            "adm": "admin",
            "ADM": "admin",
            "B40-ADM": "admin",
            "msg": "message_queue",
            "MSG": "message_queue",
            "B40-MSG": "message_queue",
        }.get(channel, channel)
        if key not in ("admin", "message_queue") or min(floor, extra) < 0:
            raise ValueError("工作时长配置无效")
        raw = floor + extra * self.params[key]
        quantized = math.ceil(raw)
        elapsed = work_elapsed(self.minute, quantized) if working else quantized
        self.emit(
            "",
            visible=False,
            kind="DurationBound",
            data={
                "channel": key,
                "floor": floor,
                "extra": extra,
                "raw": raw,
                "rounded": quantized,
                "elapsed": elapsed,
                "working": working,
                "binding": self.bind(key),
            },
        )
        return elapsed

    def schedule(
        self,
        kind,
        payload,
        delay,
        *,
        title="",
        visible=True,
        decision=False,
        priority=20,
        pool=None,
    ):
        if not isinstance(delay, int) or delay < 0 or type(priority) is not int:
            raise ValueError("任务延时或优先级无效")
        state = self.state
        state["task_sequence"] += 1
        tid = f"{state['stream']}/t{state['task_sequence']}"
        task = {
            "id": tid,
            "order": state["task_sequence"],
            "kind": kind,
            "payload": deepcopy(payload),
            "due": self.minute + delay,
            "priority": priority,
            "title": title,
            "visible": visible,
            "decision": decision,
            "pool": pool,
            "binding": self.bind(kind),
        }
        chain = event_protocol.lineage(self, delay)
        task["lineage"] = chain
        if delay == 0:
            key = (chain["root"], self.minute)
            self.immediate_counts[key] = self.immediate_counts.get(key, 0) + 1
            over_depth = chain["same_minute"] > 16
            if over_depth or self.immediate_counts[key] > 128:
                reason = "same_minute_depth" if over_depth else "same_minute_fanout"
                state.setdefault("quarantine", []).append(
                    {"reason": reason, "task": task}
                )
                self.emit(
                    "",
                    kind="TaskQuarantined",
                    visible=False,
                    data={
                        "task_id": tid,
                        "root": chain["root"],
                        "parent": chain["parent"],
                        "reason": reason,
                    },
                )
                return tid
        state["queue"].append(task)
        return tid

    def roll(self, slot):
        return bal.uniform(self.seed, slot)

    def choice(self, slot, weighted):
        sample = self.roll(slot)
        outcome = bal.pick(weighted, sample)
        self.emit(
            "",
            kind="ChoiceSealed",
            visible=False,
            data={
                "slot": slot,
                "sample": sample,
                "candidate_hash": bal.digest(weighted),
                "weights": dict(weighted),
                "outcome": outcome,
                "binding": self.bind("choice"),
            },
        )
        return outcome

    def candidate(self, slot, scores):
        return self.choice(
            slot,
            bal.distribution(scores, bal.effective(self.state["policy"], self.minute)),
        )


def _threshold(state, name, episode):
    slot = f"opportunity/{name}/{episode}/threshold"
    return slot, -math.log(bal.uniform(state["rng_seed"], slot))


def _clock(state, name):
    slot, threshold = _threshold(state, name, 0)
    return {
        "episode": 0,
        "slot": slot,
        "E": threshold,
        "H": 0.0,
        "anchor": 0,
        "at_anchor": 0.0,
        "last": 0,
        "generation": 0,
        "rate": 0.0,
        "due": None,
    }


def _measure(state, name, at):
    c = state["clocks"][name]
    return c["at_anchor"] + bal.delta_hazard(
        state["policy"], c["anchor"], at, PROCESSES[name][0], c["rate"]
    )


def _predict(state, name):
    clock = state["clocks"][name]
    here = state["minute"]
    if clock["rate"] <= 0:
        return None
    if clock["H"] >= clock["E"]:
        return here
    # The rate multiplier is positive for all allowed b. Bracket then find
    # the first integer minute reaching the threshold (ceil continuous time).
    lower_bound = min(1.0, 1.0 + bal.RULES[PROCESSES[name][0]]["slope"])
    hi = here + max(
        1, math.ceil((clock["E"] - clock["H"]) / (clock["rate"] * lower_bound)) + 1
    )
    lo = here
    while lo + 1 < hi:
        mid = (lo + hi) // 2
        if _measure(state, name, mid) >= clock["E"]:
            hi = mid
        else:
            lo = mid
    return hi


def _rates(state, force=False):
    from . import world

    for name, (_, baseline) in PROCESSES.items():
        clock = state["clocks"][name]
        active = sum(1 for t in state["queue"] if t["pool"] == name)
        relevant = getattr(world, "relevant_load", None)
        if relevant is not None:
            active += relevant(state["domain"], name)
        rate = (
            baseline / (1 + active / 3) ** 2
            if world.eligible(state["domain"], name)
            else 0.0
        )
        if force or rate != clock["rate"]:
            clock.update(
                anchor=state["minute"],
                at_anchor=clock["H"],
                rate=rate,
                generation=clock["generation"] + 1,
            )
            clock["due"] = _predict(state, name)


def _move(state, at):
    for name, c in state["clocks"].items():
        c.update(H=_measure(state, name, at), last=at)
    state["minute"] = at
    state["domain"]["now"] = at


def _fire(state, ctx, name, generation):
    from . import world

    c = state["clocks"][name]
    if generation != c["generation"] or c["due"] != state["minute"] or not c["rate"]:
        return False
    if c["H"] < c["E"]:
        raise GameError("clock_limit", "机会时钟的阈值记录不一致。")
    ctx.scope = c["slot"]
    # Preserve surplus intensity accrued before ceiling the arrival minute.
    surplus = c["H"] - c["E"]
    c["episode"] += 1
    slot, threshold = _threshold(state, name, c["episode"])
    ctx.emit(
        "",
        kind="OpportunityCrossed",
        visible=False,
        data={
            "process": name,
            "slot": c["slot"],
            "threshold": c["E"],
            "intensity": c["H"],
            "generation": generation,
        },
    )
    c.update(
        H=surplus,
        at_anchor=surplus,
        anchor=state["minute"],
        slot=slot,
        E=threshold,
        generation=generation + 1,
    )
    c["due"] = _predict(state, name)
    world.opportunity(state["domain"], name, ctx)
    return True


def _pending(domain):
    from . import world

    check = getattr(world, "decision_pending", None)
    return bool(check and check(domain))


def _advance(ctx, minutes):
    from . import world

    state = ctx.state
    if state["domain"].get("ended"):
        raise GameError("unavailable", "这段生涯已经结束。")
    if _pending(state["domain"]):
        raise GameError("unavailable", "请先处理已经到场的决定。")
    visible = [
        t["due"] for t in state["queue"] if t["visible"] and t["due"] >= ctx.minute
    ]
    target = (
        ctx.minute + minutes
        if minutes is not None
        else min(visible, default=(state["quarter"] * QUARTER_MINUTES))
    )
    for _ in range(MAX_STEPS):
        queue = [
            (t["due"], t["priority"], t["order"], "task", t) for t in state["queue"]
        ]
        # Stable sequences in separate namespaces break ties without dictionary
        # insertion-order or process hash dependence.
        for index, name in enumerate(sorted(state["clocks"])):
            c = state["clocks"][name]
            if c["due"] is not None:
                queue.append((c["due"], 50, index, "clock", (name, c["generation"])))
        queue.append((state["quarter"] * QUARTER_MINUTES, 100, 0, "quarter", None))
        due = min(queue, key=lambda e: e[:4], default=None)
        if due is None or due[0] > target:
            _move(state, target)
            return
        minute, _, _, kind, item = due
        _move(state, minute)
        if kind == "task":
            state["queue"].remove(item)
            ctx.scope, ctx.binding = item["id"], item["binding"]
            ctx.active_task = item
            world.complete(state["domain"], item["kind"], item["payload"], ctx)
            ctx.active_task = None
            ctx.binding = None
        elif kind == "clock":
            _fire(state, ctx, *item)
        else:
            state["quarter"] += 1
            ctx.scope = f"quarter/{state['quarter']}"
            world.quarter(state["domain"], state["quarter"], ctx)
        _rates(state)
        if (
            _pending(state["domain"])
            or state["domain"].get("ended")
            or (kind == "task" and item["decision"])
        ):
            return
    raise GameError("clock_limit", "此次推进触及调度上限，请缩短推进时段。")


def genesis(world_id, request):
    from . import world

    state = {
        "world_id": world_id,
        "stream": world_id,
        "name": request.name,
        "start": request.start,
        "rng_seed": request.seed,
        "minute": 0,
        "quarter": 1,
        "revision": 0,
        "sequence": 0,
        "task_sequence": 0,
        "policy": bal.initial_policy(request.balance),
        "queue": [],
        "timeline": [],
        "domain": world.genesis(request.start, request.name, request.seed),
    }
    state["policy_history"] = [dict(state["policy"])]
    state["domain"]["now"] = 0
    state["clocks"] = {name: _clock(state, name) for name in PROCESSES}
    ctx = Context(state)
    ctx.emit("你在澄川县开始了新的生涯。", title="到任", kind="CareerStarted")
    if getattr(world, "init", None):
        world.init(state["domain"], ctx)
    _rates(state)
    validate(state)
    return state, ctx.events


def resolve(before, command, proposals=None, collect=None):
    from . import world

    state = deepcopy(before)
    ctx = Context(state, proposals, collect)
    ctx.scope = f"action/{command.kind}/{state['sequence'] + 1}"
    if command.kind == "set_balance":
        cfg = checked(bal.PolicySetting, command.args)
        p = state["policy"]
        if (
            cfg.expected_policy_version != p["version"]
            or cfg.parameter_package_hash != bal.PACKAGE_HASH
        ):
            raise GameError("policy_conflict", "模拟设置已更新，请重新查看。")
        if _pending(state["domain"]):
            raise GameError("unavailable", "请先回应在场事项，再修改模拟设置。")
        if cfg.balance == p["target"]:
            return state, []
        effective = bal.effective(p, ctx.minute)
        policy_event = bal.PolicyEvent(
            event_domain="simulation_control",
            start_minute=ctx.minute,
            b_start=effective,
            target=cfg.balance,
            previous_version=p["version"],
            version=p["version"] + 1,
            transition_minutes=bal.TRANSITION,
            calculation_version=bal.CALC_VERSION,
            parameter_package_hash=bal.PACKAGE_HASH,
            cause=command.command_id,
        )
        state["policy"] = {
            "version": p["version"] + 1,
            "start": effective,
            "target": cfg.balance,
            "minute": ctx.minute,
        }
        state.setdefault("policy_history", [dict(p)]).append(dict(state["policy"]))
        ctx.emit(
            "",
            kind="SimulationPolicyChanged",
            visible=False,
            data=policy_event.model_dump(),
        )
        _rates(state, force=True)
    elif command.kind == "batch":
        from .batch import Batch, resolve_attempts

        if state["domain"].get("ended") or _pending(state["domain"]):
            raise GameError("unavailable", "请先查看本局收束或当前待回应事项。")
        state = resolve_attempts(ctx, checked(Batch, command.args))
        _rates(state)
    elif command.kind == "advance":
        options = checked(Advance, command.args)
        _advance(ctx, options.minutes)
    else:
        if state["domain"].get("ended"):
            raise GameError("unavailable", "这段生涯已经结束。")
        try:
            world.act(state["domain"], command.kind, command.args, ctx)
        except GameError:
            raise
        except ValueError as exc:
            raise GameError("unavailable", str(exc)) from exc
        _rates(state)
    state["revision"] += 1
    validate(state)
    return state, ctx.events


def validate(state):
    from . import world

    if any(t["due"] < state["minute"] for t in state["queue"]):
        raise GameError("invalid_save", "日程含有未处理的过期任务。")
    if len({t["id"] for t in state["queue"]}) != len(state["queue"]):
        raise GameError("invalid_save", "日程含有重复任务。")
    p = state["policy"]
    checked(
        bal.PolicySetting,
        {
            "balance": p["target"],
            "expected_policy_version": p["version"],
            "parameter_package_hash": bal.PACKAGE_HASH,
        },
    )
    if not 0 <= p["start"] <= 1 or not 0 <= p["minute"] <= state["minute"]:
        raise GameError("invalid_save", "配置轨迹的起始点无效。")
    history = state.get("policy_history")
    if history and history[-1] != p:
        raise GameError("invalid_save", "配置轨迹未抵达当前版本。")
    if set(state["clocks"]) != set(PROCESSES):
        raise GameError("invalid_save", "机会过程的种类不完整。")
    for name, clock in state["clocks"].items():
        quantities = (clock["H"], clock["E"], clock["at_anchor"], clock["rate"])
        if (
            any(not math.isfinite(x) or x < 0 for x in quantities)
            or clock["E"] <= 0
            or not 0 <= clock["anchor"] <= clock["last"] == state["minute"]
            or clock["slot"] != f"opportunity/{name}/{clock['episode']}/threshold"
            or clock["episode"] < 0
            or clock["generation"] < 0
            or (clock["due"] is None) != (clock["rate"] == 0)
            or (clock["due"] is not None and clock["due"] < state["minute"])
        ):
            raise GameError("invalid_save", "机会时钟与排程不一致。")
    for task in state["queue"]:
        binding = task["binding"]
        if (
            binding["parameter_package_hash"] != bal.PACKAGE_HASH
            or binding["calculation_version"] != bal.CALC_VERSION
            or not 0 <= binding["bound_at_minute"] <= state["minute"]
            or not 1 <= binding["policy_version"] <= p["version"]
            or bal.canonical(binding["parameters"])
            != bal.canonical(bal.parameters(binding["balance_eff"]))
        ):
            raise GameError("invalid_save", "任务的冻结参数与规则包不符。")
    if (
        not len(state["timeline"])
        <= state.get("visible_sequence", len(state["timeline"]))
        <= state["sequence"]
    ):
        raise GameError("invalid_save", "可见记录水位无效。")
    if state["domain"]["now"] != state["minute"] or state["minute"] < 0:
        raise GameError("invalid_save", "世界时间不一致。")
    if getattr(world, "validate", None):
        world.validate(state["domain"])


def player_view(state):
    from . import world

    domain = world.project(state["domain"])
    p = state["policy"]
    end = (
        p["minute"] + bal.TRANSITION
        if p["start"] != float(p["target"])
        else p["minute"]
    )
    observed = state.get("visible_sequence", len(state["timeline"]))
    result = {
        **domain,
        "last_action_results": state.get("last_action_results", []),
        "player_id": "player",
        "world_revision": state["revision"],
        "visible_event_sequence": observed,
        "observation_watermark": f"{state['world_id']}/v{observed}",
        "scene_id": domain.get("location", {}).get("id"),
        **{
            k: state[k]
            for k in (
                "world_id",
                "name",
                "start",
                "revision",
                "minute",
                "quarter",
                "timeline",
            )
        },
        "policy": {
            "target": p["target"],
            "effective": bal.effective(p, state["minute"]),
            "version": p["version"],
            "parameter_package_hash": bal.PACKAGE_HASH,
            "transition_end": end,
            "trajectory": deepcopy(state.get("policy_history", [p])),
        },
        "parent": state.get("parent"),
        "appointments": [
            {"id": t["id"], "due": t["due"], "title": t["title"]}
            for t in sorted(
                state["queue"], key=lambda t: (t["due"], t["priority"], t["order"])
            )
            if t["visible"] and not state["domain"].get("ended")
        ],
    }
    result["view_hash"] = bal.digest(result)
    return result
