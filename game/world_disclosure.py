"""Deliberate notebook disclosure and a pre-existing, observable environmental condition."""

from .balance import uniform
from .catalog import PEOPLE
from .world_common import action, know, readable, start_job


def setup(d, seed):
    d["office_window"] = {
        "wet": uniform(str(seed), "genesis/window-condition") < 0.22,
        "checked": False,
    }
    d["disclosures"] = []


def init(d, ctx):
    w = d["office_window"]
    if w["wet"]:
        w["source"] = ctx.emit(
            "办公室窗边立着地面积水提示牌，值班人员已经登记。室内靠门处有空椅。",
            title="到任时的值班记录",
        )


def options(d):
    from .world import present

    choices = []
    if d["location"] == "L01":
        w = d.get("office_window", {})
        detail = (
            "窗边有积水提示牌。也可在室内一般座位休息。"
            if w.get("wet")
            else "窗边的地面干燥，有一把空椅。"
        )
        choices.append(
            action("window_rest", "在窗边休息", detail, "本人 45 分钟", "日常安排")
        )
        if w.get("wet") and not w["checked"] and "N10" not in d["busy"]:
            choices.append(
                action(
                    "window_service",
                    "请办公室处理积水",
                    "值班人员需到场确认并清理。",
                    "值班人员 30 分钟",
                    "日常安排",
                )
            )
    if not readable(d):
        return choices
    shown = {(item["entry_ref"], item["to"]) for item in d.get("disclosures", [])}
    for mentor in ("N12", "N13"):
        if not present(d, mentor, d["location"]):
            continue
        choices_list = [
            {"label": f"第{i + 1}条 · " + e["text"][:35], "value": e["ref"]}
            for i, e in enumerate(d["notebook"]["entries"])
            if (e["ref"], mentor) not in shown
        ]
        if choices_list:
            choices.append(
                action(
                    "show_entry",
                    "向" + PEOPLE[mentor]["name"] + "出示一条笔记",
                    "只展示所选条目。对方知道你写过这段话，仍可保留不同判断。",
                    "本人和对方均在场",
                    "记事本",
                    {"mentor": mentor},
                    fields=[
                        {
                            "type": "select",
                            "name": "entry_ref",
                            "label": "出示哪一条",
                            "options": choices_list,
                            "default": choices_list[0]["value"],
                            "required": True,
                        }
                    ],
                )
            )
    return choices


def act(d, kind, args, ctx):
    if kind == "window_rest":
        wet = d.get("office_window", {}).get("wet", False)
        start_job(d, ctx, kind, "窗边休息", 45, {"observed_wet": wet})
        return True
    if kind == "window_service":
        d["office_window"]["checked"] = True
        start_job(d, ctx, kind, "值班清理", 30, actor="N10")
        return True
    if kind != "show_entry":
        return False
    entry = next(e for e in d["notebook"]["entries"] if e["ref"] == args["entry_ref"])
    who = args["mentor"]
    ref = ctx.emit(
        "你向" + PEOPLE[who]["name"] + "展示了手记中的一条" + entry["kind"] + "。",
        title="出示手记",
        refs=(entry["ref"],),
    )
    words = (
        "当事人在手记里写道：「" + entry["text"] + "」。条目标为" + entry["kind"] + "。"
    )
    receipt = ctx.emit(
        words, title="当面读到手记", actor=who, visible=False, refs=(ref, entry["ref"])
    )
    know(d, who, receipt, words, "shown_notebook")
    d.setdefault("disclosures", []).append(
        {"entry_ref": entry["ref"], "to": who, "ref": ref, "received": receipt}
    )
    return True


def complete(d, kind, args, ctx):
    if kind == "window_service":
        w = d["office_window"]
        w["wet"] = False
        ctx.emit(
            "值班人员确认地面已清理，取走了提示牌。",
            title="办公室维护完成",
            refs=(w["source"],),
        )
        return True
    if kind != "window_rest":
        return False
    w = d.get("office_window", {})
    if args["observed_wet"] and w.get("wet"):
        outcome = ctx.choice(
            ctx.scope + "/environment", {"interrupted": 0.18, "finished": 0.82}
        )
        if outcome == "interrupted":
            ctx.emit(
                "值班人员提醒你挪到干燥处，休息提前中断。",
                title="环境影响了休息",
                refs=(w["source"],),
            )
            return True
    # All seats share the same daily recovery allowance.
    from . import world_social

    world_social.complete(d, "rest", {}, ctx)
    return True
