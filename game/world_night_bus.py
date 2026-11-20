"""Optional county serial, progressed by committed choices and the county clock."""

from .catalog import DAY
from .night_bus_dispatch import ARRIVALS, BOARDS, LIVE_RUNS, slips
from .night_bus_story import ECHOES, EXHIBITS, SCENES
from .world_common import action, visible_doc

TITLE = "夜班车不进站"
# Earliest reasonable interval, local clock hour and minute, visible invitation.
VISITS = {
    "curb": (0, 22, 40, "南门旧站牌碰面"),
    "tin": (180, 8, 10, "老杜开补胎铺的门"),
    "shift": (60, 21, 30, "食品厂夜班交接"),
    "morning": (90, 7, 40, "南门早市见陆经理"),
    "hearing": (90, 15, 0, "候车室开会"),
    "trial": (6 * 60, 22, 40, "七路首次试跑"),
    "fare": (6 * DAY, 15, 30, "售票间核第一周的账"),
    "turn": (0, 9, 0, "总站丈量，司机与乘客议事"),
}


def _next_visit(now, earliest, hour, minute):
    slot = (earliest + 540) // DAY * DAY + hour * 60 + minute - 540
    if slot < earliest or slot <= now:
        slot += DAY
    return slot


def _allowed(d, choice, seen):
    if not choice.needs:
        return True
    if choice.needs == "county:passage":
        return d["passage"]["opened"]
    return any(key in seen for key in choice.needs.split("|"))


def options(d):
    arc = d.get("night_bus", {})
    if arc.get("due") is not None:
        return []
    current = arc.get("node", "call")
    seen = set(arc.get("choices", ()))
    return [
        action(
            "night_bus",
            choice.label,
            SCENES[current].title,
            "计入七路行记",
            "七路夜班",
            {"scene": current, "choice": choice.key},
        )
        for choice in SCENES[current].choices
        if _allowed(d, choice, seen)
    ]


def project(d):
    arc = d.get("night_bus", {})
    current = arc.get("node", "call")
    scene = SCENES[current]
    due = arc.get("due")
    if d["ended"] and not arc:
        return None
    seen = set(arc.get("choices", ()))
    last = arc.get("last", "")
    if due is not None:
        return {
            "stage": "waiting",
            "act": TITLE,
            "place": "",
            "title": scene.title if current in ARRIVALS else VISITS[current][3],
            "body": "",
            "reply": last,
            "due": due,
            "art": _art(current),
        }
    echoes = [line for key, line in ECHOES.get(current, {}).items() if key in seen]
    paragraphs = scene.body.split("\n")
    paragraphs[-1:-1] = echoes
    return {
        "stage": "invitation"
        if not arc
        else "ending"
        if not scene.choices
        else "playing",
        "act": scene.act,
        "place": scene.place,
        "title": scene.title,
        "body": "\n".join(paragraphs),
        "reply": last,
        "due": None,
        "art": _art(current),
        "dispatch": slips(current, seen),
    }


def _art(current):
    if current in BOARDS or current in ARRIVALS or current in {
        "curb",
        "cab",
        "shoes",
        "call",
        "last_stop",
        "walk",
        "trial",
        "canal",
        "bridge_stop",
        "dark_walk",
        "end_light",
        "end_lantern",
        "end_north",
    }:
        return "nightbus"
    return "depot"


def act(d, kind, args, ctx):
    if kind != "night_bus":
        return False
    arc = d.setdefault("night_bus", {"node": "call", "choices": []})
    scene = SCENES[arc["node"]]
    chosen = next(choice for choice in scene.choices if choice.key == args["choice"])
    ref = ctx.emit(chosen.reply, title=chosen.label)
    arc["choices"].append(chosen.key)
    arc.update(node=chosen.target, last=chosen.reply)
    if chosen.exhibit:
        title, source, body = EXHIBITS[chosen.exhibit]
        visible_doc(
            d,
            "BUS-" + chosen.exhibit,
            title,
            body,
            source,
            TITLE,
            kind="七路见证",
            ref=ref,
        )
    target = SCENES[chosen.target]
    if chosen.key in LIVE_RUNS:
        travel = LIVE_RUNS[chosen.key].arrival
        arc["due"] = ctx.minute + travel
        ctx.schedule("night_bus_visit", {"scene": chosen.target}, travel, title=target.title)
    elif chosen.target in VISITS:
        delay, hour, minute, caption = VISITS[chosen.target]
        earliest = ctx.minute + delay
        if chosen.target == "turn":
            earliest = max(earliest, arc["trial_at"] + (29 * DAY))
        due = _next_visit(ctx.minute, earliest, hour, minute)
        arc["due"] = due
        ctx.schedule(
            "night_bus_visit", {"scene": chosen.target}, due - ctx.minute, title=caption
        )
    elif not target.choices:
        body = project(d)["body"]
        final_ref = ctx.emit(body, title=target.title, refs=(ref,))
        visible_doc(
            d,
            "BUS-conclusion",
            target.title,
            body,
            "七路行记",
            TITLE,
            kind="夜线结局",
            ref=final_ref,
        )
    return True


def complete(d, kind, payload, ctx):
    if kind != "night_bus_visit":
        return False
    arc = d.get("night_bus", {})
    if arc.get("node") == payload["scene"] and arc.get("due") == ctx.minute:
        del arc["due"]
        scene = SCENES[arc["node"]]
        if arc["node"] == "trial":
            arc["trial_at"] = ctx.minute
        if arc["node"] in ARRIVALS:
            run = LIVE_RUNS[arc["choices"][-1]]
            arc["last"] = run.account()
            ctx.emit(arc["last"], title=scene.title)
        else:
            ctx.emit(scene.body.split("\n")[0], title=scene.title)
    return True


def validate(d):
    if "night_bus" not in d:
        return
    arc = d["night_bus"]
    if not isinstance(arc, dict) or not isinstance(arc.get("choices"), list):
        raise ValueError("七路行记格式有误。")
    current = "call"
    seen = set()
    for key in arc["choices"]:
        choice = next((c for c in SCENES[current].choices if c.key == key), None)
        if choice is None or not _allowed(d, choice, seen):
            raise ValueError("七路行记的前后选择不一致。")
        seen.add(choice.key)
        current = choice.target
    if (
        current == "call"
        or current != arc.get("node")
        or not isinstance(arc.get("last"), str)
    ):
        raise ValueError("七路行记缺少当前场景。")
    if "due" in arc and (
        current not in VISITS and current not in ARRIVALS
        or type(arc["due"]) is not int
        or arc["due"] < d["now"]
    ):
        raise ValueError("七路行记的约定时刻无效。")
    trial_has_begun = (
        current == "trial"
        and "due" not in arc
        or bool(seen & {"hold", "on_time", "canal_link", "dial_live"})
    )
    if trial_has_begun and (
        type(arc.get("trial_at")) is not int or not 0 <= arc["trial_at"] <= d["now"]
    ):
        raise ValueError("七路试跑缺少起始记录。")
