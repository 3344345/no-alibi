"""County domain projection and resolver. The store alone commits its results."""

from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
from . import world_projects as projects
from .catalog import (
    ARCS,
    CASES,
    DAY,
    LOCATIONS,
    PEOPLE,
    POSITIONS,
    PROJECTS,
    STARTS,
    WAN,
)
from .world_common import (
    accepted,
    action,
    arc,
    case,
    contact,
    know,
    promise,
    readable,
    start_job,
    visible_doc,
)


def _modules():
    from . import (
        world_social,
        world_career,
        world_office,
        world_cases,
        world_regional,
        world_intent,
        world_disclosure,
        world_interop,
        world_maintenance,
    )

    return (
        projects,
        world_social,
        world_career,
        world_office,
        world_cases,
        world_regional,
        world_intent,
        world_disclosure,
        world_interop,
        world_maintenance,
    )


def genesis(start, name, seed):
    profile = STARTS[start]
    hashed = int(sha256(str(seed).encode()).hexdigest(), 16)
    rank = 1 if start in ("S04", "S05", "S06") else 0
    d = {
        "start": start,
        "name": name,
        "opening": profile["brief"],
        "now": 0,
        "quarter": 1,
        "location": "L01",
        "ended": False,
        "ending": None,
        "contacts": list(
            dict.fromkeys(["N10", "N11", "N08", "N16", *profile["contacts"]])
        ),
        "docs": {},
        "cases": {},
        "arcs": {},
        "roles": {},
        "actors": {},
        "busy": {},
        "job_seq": 1,
        "promises": {},
        "flags": {},
        "reports": [],
        "opportunities": {},
        "family": {
            "savings": 12_000_000,
            "fatigue": 20,
            "pressure": 30,
            "resilience": 60,
            "recovered_day": -1,
            "recovered": 0,
            "training": "待回复",
            "care": "待商议",
            "arrears": 0,
            "plan_end": 0,
        },
        "notebook": {"location": "player", "entries": [], "copies": []},
        "invites": {"L04": "待回复", "L05": "未预约", "L06": "未预约"},
        "statements": [],
        "investigation": {"status": "无程序", "acquired": [], "findings": []},
        "career": {
            "rank": rank,
            "title": profile["role"],
            "since": 1,
            "deliveries": 0,
            "vacancy": None,
            "applied": False,
            "transferred": False,
            "misses": 0,
            "duties": "正常",
            "evidence": [],
            "retired": False,
            "age": profile["age"],
            "handover": None,
            "positions": {
                p[0]: ("player" if i == rank else "incumbent:" + p[0])
                for i, p in enumerate(POSITIONS)
            },
        },
        "quarterly_budget_events": [],
        "payroll": {"authorized": 12_000_000, "paid": 0},
        "delegations": {},
    }
    for key, n in PEOPLE.items():
        d["actors"][key] = {
            "beliefs": {"genesis/" + key: n["claim"]},
            "goals": [n["goal"]],
            "resources": {"channel": n["role"]},
            "relations": {
                n["contact"]: {
                    "trust": 0.55,
                    "familiarity": 0.35,
                    "dependency": 0.10,
                    "competition": 0.2,
                    "shared_exposure": 0,
                }
            },
            "plans": [n["plan"]],
            "wake": "收到职责内材料",
            "last_acted": None,
        }
    d["career"]["vacate_quarter"] = 2 + hashed % 5
    d["career"]["health_window"] = 40 + (hashed // 17) % 48
    from .balance import uniform

    d["career"]["health_profile"] = {
        "requires_followup": uniform(str(seed), "genesis/long-health-course") < 0.14,
        "irreversible": uniform(str(seed), "genesis/long-health-outcome") < 0.35,
    }
    d["family"]["training_slot"] = 3 * DAY + (hashed % 3) * DAY
    from . import world_institutions, world_regional

    from . import world_disclosure
    world_disclosure.setup(d, seed)
    world_institutions.setup(d)
    world_regional.setup(d)
    projects.setup(
        d,
        0
        if str(seed).lower() in ("classic", "tutorial", "教学", "经典")
        else hashed % 4,
    )
    visible_doc(
        d,
        "D10-window",
        "办公室 · 今日协调窗口",
        "四小时后，办公室汇总首轮意见。届时仍可提交补充件。",
        "N10",
        "今天的协调日程",
    )
    from . import world_interop

    world_interop.setup(d)
    initial_source = profile["contacts"][0]
    visible_doc(
        d,
        "START-" + start,
        profile["channel"] + "交接单",
        profile["brief"],
        initial_source,
        profile["role"],
    )
    if start == "S03":
        visible_doc(
            d,
            "START-tech",
            "技术意见摘要",
            "我仅能对自己检查的西段标桩签字。",
            "N18",
            "指定技术档案",
        )
    if start == "S02":
        visible_doc(
            d,
            "START-field",
            "前次现场巡视",
            "你上次走到西段标桩，未进入上游施工区。",
            "本人",
            "前次巡视",
            kind="本人观察",
        )
    return d


def init(d, ctx):
    from . import world_disclosure
    world_disclosure.init(d, ctx)
    prof = STARTS[d["start"]]
    ref = ctx.emit(d["opening"], title="到任 · 澄川县项目协调办")
    visible_doc(
        d,
        "FAM-training",
        "沈亦宁的培训通知",
        "培训单位已通知须由本人确认名额，家庭日程待协商。",
        "N14",
        "培训回复期",
        ref=ref,
    )
    arc(d, "V4-ARC03", "收到独立职业机会", ref)
    ctx.schedule("family_enquire", {}, DAY, title="家人核对培训时段")
    from . import world_interop

    world_interop.init(d, ctx)
    # Attach every initialized record to the committed career opening.
    for doc in d["docs"].values():
        doc["refs"] = [ref]
    case(d, "K01", "signal", ref, "南渠简报和巡查摘录已经送达。")
    case(d, prof["case"], "signal", ref, prof["brief"])
    for n in ("N08", "N18", "N10"):
        know(d, n, ref, PEOPLE[n]["claim"])
    promise(d, ctx, prof["obligation"], prof["creditor"], prof["days"] * DAY)
    ctx.schedule("window_due", {}, 240, title="办公室汇总首轮意见")
    ctx.schedule(
        "family_train", {}, d["family"]["training_slot"], title="培训名额回复期限"
    )
    ctx.schedule("technician_application", {}, 2 * DAY, title="现场技术人员来函")
    ctx.schedule(
        "mentor_channel_change", {}, 4 * DAY, title="联络渠道登记", visible=False
    )
    ctx.schedule("monthly", {}, 30 * DAY, title="岗位薪酬与家庭账单")
    ctx.schedule("npc_plan", {"npc": "N06"}, 180, title="财政预计寄出协调函")
    ctx.schedule("invite_end", {}, 7 * DAY, title="本次晚餐邀约结束")
    ctx.emit(
        "社区询问西段便道能否开放。两份来文已在桌上，周主任四小时后汇总首轮意见。",
        title="今日待办",
    )


def decision_pending(d):
    return d["investigation"].get("hearing") == "需答复" and not d["ended"]


def actions(d):
    if d["ended"]:
        return []
    if decision_pending(d):
        from . import world_career

        return world_career.hearing_options()
    if "player" in d["busy"]:
        return []
    out = [
        action(
            "scene_wait",
            "在" + LOCATIONS[d["location"]]["name"] + "稍候",
            "原有安排继续运行。",
            "本人 15 分钟",
            "个人日程",
        )
    ]
    for mod in _modules():
        if mod is projects and d["career"].get("suspended"):
            continue
        out.extend(mod.options(d))
    for key, l in LOCATIONS.items():
        if key == d["location"]:
            continue
        if l["access"] == "dinner" and d["invites"][key] not in (
            "接受",
            "婉拒后赴约",
            "自由赴约",
        ):
            continue
        if l["access"] == "appointment" and d["invites"][key] != "已预约":
            continue
        minutes = travel_time(d, key)
        out.append(
            action(
                "travel",
                "前往" + l["name"],
                l["description"],
                f"本人 {minutes} 分钟",
                "地点",
                {"location": key},
            )
        )
    return sorted(
        out,
        key=lambda a: (
            a["category"],
            a["kind"],
            a["label"],
            str(sorted(a["args"].items())),
        ),
    )


def travel_time(d, key):
    if key == "L02" or d["location"] == "L02":
        return 40 if d["passage"]["opened"] else 60
    return LOCATIONS[key]["minutes"]


def _check(d, k, args):
    if not isinstance(args, dict):
        raise ValueError("行动参数格式有误。")
    for item in actions(d):
        if item["kind"] != k or any(
            args.get(key) != v for key, v in item["args"].items()
        ):
            continue
        fields = {f["name"]: f for f in item["fields"]}
        if set(args) - set(item["args"]) - set(fields):
            continue
        if any(
            f["type"] == "select"
            and args.get(key) not in [opt["value"] for opt in f["options"]]
            for key, f in fields.items()
        ):
            continue
        if any(
            not isinstance(args.get(key), str)
            or not args[key].strip()
            or len(args[key]) > f.get("maxLength", 300)
            for key, f in fields.items()
        ):
            continue
        return
    if k == "travel" and args.get("location") in LOCATIONS:
        from .world_templates import scene_line

        raise ValueError(scene_line(args["location"], "denied"))
    raise ValueError("当前地点、人员、材料或程序条件不支持这项行动。")


def act(d, k, args, ctx):
    d["now"] = ctx.minute
    _check(d, k, args)
    if k == "scene_wait":
        start_job(d, ctx, "scene_wait_done", "在场稍候", 15)
        return
    if k == "travel":
        key = args["location"]
        start_job(
            d, ctx, "arrive", "前往" + LOCATIONS[key]["name"], travel_time(d, key), args
        )
        return
    for mod in _modules():
        if mod.act(d, k, args, ctx):
            return
    raise ValueError("未知行动。")


def complete(d, k, p, ctx):
    d["now"] = ctx.minute
    if d["ended"] or not accepted(d, p):
        return
    from .world_templates import scene_line

    if k == "scene_wait_done":
        ctx.emit(scene_line(d["location"], "wait"), title="在场等待")
        return
    if k == "arrive":
        dest = p["location"]
        old = d["location"]
        d["location"] = dest
        ref = ctx.emit(
            scene_line(old, "leave")
            + "抵达"
            + LOCATIONS[dest]["name"]
            + "。"
            + LOCATIONS[dest]["description"],
            title="行程完成",
        )
        for who in LOCATIONS[dest]["people"]:
            if present(d, who, dest):
                contact(d, who)
        if dest == "L03" and "K09" not in d["cases"]:
            case(d, "K09", "active", ref, CASES["K09"]["description"])
        if dest == "L04" and d["invites"]["L04"] == "婉拒后赴约":
            case(d, "K05", "contested", ref, "出席及先前的拒绝分别有记录。")
            visible_doc(
                d,
                "D05-attend",
                "饭局到场记录",
                "主持人只确认本次已到场，先前回复仍有单独记录。",
                "N12",
                "本次到场",
                ref=ref,
            )
        return
    if k == "window_due":
        submitted = d["flags"].get("reply")
        ctx.emit(
            "办公室汇总了你已递交的意见。"
            if submitted
            else "首轮汇总已经发出，南渠意见列作待补。你仍可继续核实。",
            title="协调窗口结束",
        )
        return
    if k == "promise_due":
        pr = d["promises"].get(p["id"])
        if pr and pr["status"] == "待履约" and pr["version"] == p["version"]:
            pr["status"] = "逾期"
            d["career"]["misses"] += 1
            ref = ctx.emit(
                "答复期限已过：" + pr["title"] + "。当事人可以补办或重议。",
                title="承诺到期",
                refs=(pr["ref"],),
            )
            case(d, "K02", "contested", ref, pr["title"])
        return
    if k == "npc_plan":
        from .communication import send_plan

        send_plan(d, p["npc"], ctx)
        return
    if k == "office_delivery":
        from .communication import deliver_plan

        deliver_plan(d, p, ctx)
        return
    for mod in _modules():
        if mod.complete(d, k, p, ctx):
            return
    raise ValueError("未知到期任务：" + k)


def quarter(d, number, ctx):
    if d["ended"]:
        return
    d["now"] = ctx.minute
    d["quarter"] = number
    f = d["fiscal"]
    f["quarter_used"] = 0
    if (number - 1) % 4 == 0:
        ref = ctx.emit(
            "县级年度预算授权生效，新年度额度 8000 万元，已承诺的既有支出分别留账。",
            title="年度授权",
            actor="N02",
        )
        d["quarterly_budget_events"].append(ref)
        f["year"] += 1
        f["annual_left"] = 8000 * WAN
        d["payroll"]["authorized"] += 12_000_000
    for p in d["projects"].values():
        if p["opened"]:
            p["maintenance_due"] = True
    n = f"N{(number - 2) % 24 + 1:02}"
    complete(d, "npc_plan", {"npc": n}, ctx)
    from . import world_career

    from . import world_maintenance

    world_maintenance.on_quarter(d, ctx)
    world_career.on_quarter(d, number, ctx)
    if d["ended"]:
        return
    known = [
        d["cases"][k]["title"]
        for k in sorted(d["cases"])
        if d["cases"][k]["status"] not in ("resolved", "dormant")
    ]
    title = "十二季任期档案" if number == 13 else f"第 {number - 1} 季档案"
    body = (
        "未结事项："
        + "、".join(known[:6])
        + "。已取得材料 "
        + str(len(d["docs"]))
        + " 份。"
    )
    ref = ctx.emit(body, title=title)
    d["reports"].append(
        {"id": "Q" + str(number - 1), "title": title, "body": body, "refs": [ref]}
    )


def eligible(d, process):
    if d["ended"] or decision_pending(d) or process in d["opportunities"]:
        return False
    return {
        "verification": "D01-detail" not in d["docs"]
        and d["flags"].get("compare", False)
        and "N18" not in d["busy"],
        "repair": any(x["status"] == "逾期" for x in d["promises"].values()),
        "case": d["flags"].get("cooperate", False) or bool(d["notebook"]["copies"]),
        "rework": any(x["phase"] == "拟议" for x in d["projects"].values())
        and d["flags"].get("reply") == "conditional",
    }.get(process, False)


def relevant_load(d, process):
    actor = {"verification": "N18", "repair": "N10", "case": "N03", "rework": "N10"}[
        process
    ]
    waiting = sum(
        1
        for row in d["promises"].values()
        if row["creditor"] == actor and row["status"] == "待履约"
    )
    return int(actor in d["busy"]) + waiting


def location_index(d):
    rows = []
    for key, loc in LOCATIONS.items():
        access = loc["access"]
        allowed = (
            access == "public"
            or (access == "appointment" and d["invites"][key] == "已预约")
            or (
                access == "dinner"
                and d["invites"][key] in ("接受", "婉拒后赴约", "自由赴约")
            )
        )
        rows.append(
            {
                "id": key,
                "name": loc["name"],
                "description": loc["description"],
                "accessible": allowed,
                "access": "公开可前往"
                if access == "public"
                else ("已有预约" if allowed else "须先答复邀请或取得预约"),
            }
        )
    return rows


def present(d, npc, loc):
    return (
        npc in LOCATIONS[loc]["people"]
        and not (npc == "N14" and d["family"]["plan_end"] > d["now"])
        and not (
            npc == "N18" and d["busy"].get("N18", {}).get("kind") == "technician_return"
        )
    )


def opportunity(d, process, ctx):
    if not eligible(d, process):
        return
    options = {
        "verification": ("程向晚留出一个补充核查窗口。", "N18"),
        "repair": ("原收件人愿意再听一次改约方案。", "N10"),
        "case": ("既有协作材料可进入一次后续会谈。", "N03"),
        "rework": ("秘书请你复核附条件意见的范围栏。", "N10"),
    }
    if process == "case":
        # The initiator only uses its own received coordination record and schedule.
        actor_id = "N03" if d["flags"].get("cooperate") else "N19"
        input_refs = list(d["actors"][actor_id]["beliefs"])
        has_receipt = any(not key.startswith("genesis/") for key in input_refs)
        hour = (ctx.minute + 540) % 1440
        distance = max(540 - hour, 0, hour - 1020)
        timing = 1 / (1 + distance / 240)
        workflow = 1.0 if has_receipt else 0.5
        # Discuss a new scope, keep the arrangement, or ask for documentation.
        r = 0.40 * 0.6 + 0.35 * timing + 0.25 * workflow
        g = 0.25 * (0.75 + 2 / 3 + float(has_receipt) + 1.0)
        none = (0.65, min(relevant_load(d, process) / 3, 1.0))
        if (
            ctx.candidate(ctx.scope + "/content", {"none": none, "meeting": (r, g)})
            == "none"
        ):
            return
    text, actor = options[process]
    if process == "case":
        from .proposals import followup

        actor = actor_id
        text = followup(d, ctx, actor, text)
    ref = ctx.emit(text, title="新的联络", actor=actor)
    d["opportunities"][process] = {"title": text, "ref": ref, "actor": actor}


def project(d):
    loc = LOCATIONS[d["location"]]
    c = d["career"]
    f = d["fiscal"]
    fam = d["family"]
    nb = d["notebook"]
    p = {
        "name": d["name"],
        "role": c["title"],
        "start": d["start"],
        "location_id": d["location"],
        "location": loc["name"],
        "age": c["age"],
        "position": POSITIONS[c["rank"]][0],
        "quarter": d["quarter"],
        "fatigue": fam["fatigue"],
        "pressure": fam["pressure"],
        "resilience": fam["resilience"],
        "duties": c["duties"],
    }
    rows = []
    for key, info in PROJECTS.items():
        proj = d["projects"][key]
        rows.append(
            {
                "id": key,
                "name": info["name"],
                "description": info["description"],
                "status": proj["phase"],
                "report": proj["report"],
                "request": info["request"],
                "groups": info["groups"],
                "owner": PEOPLE[info["owner"]]["name"],
                "public_use": proj["opened"],
                "passage": d["passage"]["stage"] if info["opening_passage"] else None,
                "maintenance": proj["maintenance_due"],
            }
        )
    return deepcopy(
        {
            "player": p,
            "opening": d["opening"],
            "location": {
                "id": loc["id"],
                "name": loc["name"],
                "description": loc["description"],
            },
            "people": [
                {
                    "id": i,
                    "name": PEOPLE[i]["name"],
                    "role": d["roles"].get(i, PEOPLE[i]["role"]),
                    "description": PEOPLE[i]["role"],
                    "present": present(d, i, d["location"]),
                }
                for i in d["contacts"]
            ]
            + list(d["successors"].values()),
            "locations": location_index(d),
            "cases": [d["cases"][i] for i in sorted(d["cases"])],
            "projects": rows,
            "documents": sorted(
                d["docs"].values(),
                key=lambda row: (
                    row.get("received_minute", 0),
                    row.get("receipt_order", 0),
                    row["id"],
                ),
            ),
            "commitments": sorted(
                d["promises"].values(), key=lambda row: (row["due"], row["id"])
            ),
            "finances": {
                "annual_remaining": f["annual_left"],
                "quarter_remaining": 2000 * WAN - f["quarter_used"],
                "reserved": f["reserved"],
                "paid": f["paid"],
                "groups_available": 12 - sum(f["groups"].values()),
                "savings": fam["savings"],
            },
            "notebook": {
                "accessible": readable(d),
                "location": nb["location"],
                "entries": nb["entries"] if readable(d) else [],
            },
            "ending": d["ending"],
            "reports": d["reports"],
            "arcs": [
                {"id": key, "title": ARCS[key]["name"], "status": val[-1]["status"]}
                for key, val in sorted(d["arcs"].items())
            ],
            "offers": [
                {
                    key: value
                    for key, value in offer.items()
                    if key
                    in (
                        "id",
                        "name",
                        "version",
                        "description",
                        "terms",
                        "status",
                        "ref",
                        "deadline",
                    )
                }
                for offer in d["offers"]
            ],
            "actions": actions(d),
            "family": {"training": fam["training"], "care": fam["care"]},
            "busy": d["busy"].get("player"),
        }
    )


def validate(d):
    from . import world_regional

    world_regional.validate(d)
    f = d["fiscal"]
    if not (
        0 <= f["quarter_used"] <= 2000 * WAN
        and 0 <= f["annual_left"] <= 8000 * WAN
        and f["paid"] >= 0
        and f["reserved"] >= 0
    ):
        raise ValueError("财政账本超出授权范围。")
    if sum(f["groups"].values()) > 12 or any(n <= 0 for n in f["groups"].values()):
        raise ValueError("班组占用超限。")
    if d["family"]["savings"] < 0:
        raise ValueError("家庭账户透支。")
    if any(not 0 <= p["progress"] <= 100 for p in d["projects"].values()):
        raise ValueError("错误的工程完成量。")
    if d["passage"]["opened"] and not (
        d["passage"]["safe"] and d["passage"].get("approval_ref")
    ):
        raise ValueError("便道缺少批准。")
    if not 0 <= d["payroll"]["paid"] <= d["payroll"]["authorized"]:
        raise ValueError("薪酬来源不足。")
    if d["ended"] != bool(d["ending"]):
        raise ValueError("终局状态不一致。")
