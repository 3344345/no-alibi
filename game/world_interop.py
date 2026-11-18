"""Cross-system paths use the same facts, tasks and resource book as ordinary play."""

from .catalog import DAY, PEOPLE, PROJECTS
from .world_common import action, arc, case, contact, know, visible_doc


def setup(d):
    delayed = d["variant"]["id"] == "V4-TV01"
    original = 7 * DAY
    revised = original + (21 * DAY if delayed else 0)
    d["field_schedule"] = {
        "planned": original,
        "forecast": revised,
        "delay_days": (revised - original) // DAY,
        "holder": "N08",
        "version": "r2",
        "received_by": ["N08", "N18"],
        "filed": False,
    }
    d["actors"]["N08"]["beliefs"]["genesis/N08/schedule"] = (
        "当前排期比原计划迟三周。" if delayed else "当前排期仍在原窗口内。"
    )
    d["actors"]["N02"]["beliefs"]["genesis/N02/schedule"] = "上次正式报送仍按原窗口。"
    visible_doc(
        d,
        "PLAN-r1",
        "南渠工序排期 · 旧版",
        "原计划在第八天交接。尚无新版送到办公室。",
        "N10",
        "前次批转排期",
        date="上次收文",
    )
    d["department_round"] = {"state": "未召开", "bids": {}, "round": 0}


def init(d, ctx):
    for who in ("N08", "N02"):
        text = d["actors"][who]["beliefs"].pop("genesis/" + who + "/schedule")
        ref = ctx.emit(text, title="排期初始归档", actor=who, visible=False)
        know(d, who, ref, text, topic="initial_schedule")
        if who == "N08":
            d["field_schedule"]["revision_ref"] = ref
            know(d, "N18", ref, text, topic="initial_schedule")
    d["actors"]["N03"]["relations"]["N12"] = {
        "trust": 0.55,
        "familiarity": 0.45,
        "dependency": 0.45,
        "competition": 0.1,
        "shared_exposure": 0.0,
    }


def options(d):
    loc = d["location"]
    f = d["field_schedule"]
    a = []
    flags = d["flags"]
    if loc == "L01":
        if not flags.get("private_check"):
            a.append(
                action(
                    "private_check",
                    "私下核实现场排期",
                    "请程向晚在工地单独谈自己手里的记录。普通联系不等于实际到场。",
                    "保密联络，仍需亲赴工地",
                    "文书查证",
                )
            )
        if "N19" not in f["received_by"] and not flags.get("audit_schedule"):
            a.append(
                action(
                    "audit_schedule",
                    "请档案员独立调取最新排期",
                    "从本办公室交出所持旧版，由档案员另向水务请求原登记版本。",
                    "档案权限及文书送达",
                    "材料复核",
                )
            )
    if (
        loc == "L02"
        and flags.get("private_check") == "待到场"
        and "N18" not in d["busy"]
    ):
        a.append(
            action(
                "private_meeting",
                "与程向晚单独核实",
                "仅核对当事人能出示的排期版本。",
                "本人及技术员 25 分钟",
                "现场核查",
            )
        )
    if loc == "L03" and d["department_round"]["state"] == "未召开":
        a.append(
            action(
                "department_round",
                "征集三部门的本期排程",
                "三部门各自向同一财政池递交申请，由受理顺序和实际预留决定能否执行。",
                "同一汇总时点",
                "预算谈判",
            )
        )
    return a


def act(d, k, p, ctx):
    flags = d["flags"]
    if k == "private_check":
        ref = ctx.emit("已向程向晚本人发送非公开核实请求。", title="单独联系")
        flags["private_check"] = "在途"
        ctx.schedule(
            "private_reply",
            {"ref": ref},
            ctx.duration("message_queue", 20, 60),
            title="技术员答复",
        )
        return True
    if k == "private_meeting":
        from .world_common import start_job

        ref = ctx.emit("现场会面开始，参加人仅为本人和程向晚。", title="单独核实")
        flags["private_check"] = "会面中"
        start_job(d, ctx, "meeting_evidence", "核对现场原始排期", 25, {"ref": ref})
        d["busy"]["N18"] = {
            "id": ref,
            "kind": "witness_meeting",
            "title": "现场核对",
            "due": ctx.minute + 25,
            "visible": False,
        }
        return True
    if k == "audit_schedule":
        flags[k] = "待受理"
        old = d["docs"]["PLAN-r1"]["refs"][0]
        ref = ctx.emit(
            "董薇取得办公室所持排期旧版，另向水务申请调阅签发版本。",
            title="档案申请",
            actor="N19",
            refs=(old,),
        )
        know(d, "N19", ref, d["docs"]["PLAN-r1"]["body"])
        ctx.schedule(
            "audit_delivery",
            {"ref": ref},
            ctx.duration("admin", 30, 90),
            title="档案室向责任方调取排期",
        )
        return True
    if k == "department_round":
        book = d["department_round"]
        book.update(state="等待部门来件", round=book["round"] + 1, bids={})
        ref = ctx.emit(
            "协调会征集本期书面排程。项目代表各自报出所需工作范围。",
            title="部门申请窗口",
        )
        for key, project in PROJECTS.items():
            ctx.schedule(
                "department_bid",
                {"key": key, "ref": ref},
                45,
                title=project["name"] + "提交申请",
                visible=False,
            )
        return True
    return False


def recovery_after_skipped_report(d, ctx):
    if d["field_schedule"]["delay_days"] == 0:
        return
    ctx.schedule("recovery_bid", {}, 90, title="水务内部复核窗口", visible=False)


def settle_round(d, ctx, offer, ref):
    if not d["department_round"]["bids"]:
        return
    for key, bid in d["department_round"]["bids"].items():
        portion = offer["terms"].get(key, {"amount": 0, "groups": 0})
        ctx.schedule(
            "department_replan",
            {
                "key": key,
                "amount": portion["amount"],
                "groups": portion["groups"],
                "source": ref,
                "bid": bid["source"],
            },
            ctx.duration("message_queue", 15, 45),
            title="项目方按实际额度重排",
        )


def schedule_text(d):
    f = d["field_schedule"]
    return f"水务签发的排期为第 {f['forecast'] // DAY + 1} 天交接。原排期为第 {f['planned'] // DAY + 1} 天。"


def complete(d, k, p, ctx):
    f = d["field_schedule"]
    flags = d["flags"]
    if k == "recovery_bid":
        who = "N08"
        ref = ctx.emit(
            "水务根据本人已知的三周工期差提出补救排程，仍要使用原申请的班组。",
            title="部门自主补救",
            actor=who,
            visible=False,
        )
        d["actors"][who]["plans"].append("调整南渠首期工序以补救三周延期")
        know(d, who, ref, "已形成补救排程，未取得额外人手。")
        flags["recovery_ref"] = ref
        return True
    if k == "department_bid":
        key = p["key"]
        info = PROJECTS[key]
        who = info["owner"]
        reason = (
            "补救延期，仍需原有班组。"
            if key == "P01" and flags.get("recovery_ref")
            else info["description"]
        )
        refs = (
            (p["ref"], flags["recovery_ref"])
            if key == "P01" and flags.get("recovery_ref")
            else (p["ref"],)
        )
        ref = ctx.emit(
            info["name"] + "独立申请 " + str(info["groups"]) + " 组。" + reason,
            title="独立排程申请",
            actor=who,
            refs=refs,
        )
        know(d, "N06", ref, reason)
        d["department_round"]["bids"][key] = {
            "source": ref,
            "request": info["request"],
            "groups": info["groups"],
            "applicant": who,
        }
        if len(d["department_round"]["bids"]) == 3:
            d["department_round"]["state"] = "已汇总"
            case(
                d,
                "K09",
                "contested",
                ref,
                "三份独立申请共需十四组，现有十二组，须错峰或缩减。",
            )
        return True
    if k == "department_replan":
        key = p["key"]
        project = PROJECTS[key]
        who = project["owner"]
        reduced = p["amount"] < project["request"] or p["groups"] < project["groups"]
        text = (
            "改列下一窗口，保留未获配任务。"
            if p["amount"] == 0
            else ("压缩到已获配的阶段范围。" if reduced else "按获配范围排入本期。")
        )
        ref = ctx.emit(
            project["name"] + "收到财政确认后，" + text,
            title="部门自主重排",
            actor=who,
            refs=(p["source"], p["bid"]),
        )
        d["actors"][who]["plans"].append(text)
        know(d, who, ref, text)
        return True
    if k == "private_reply":
        available = "N18" not in d["busy"]
        flags["private_check"] = "待到场" if available else "未能赴约"
        ref = ctx.emit(
            "程向晚接受单独核实，请到工地会面。"
            if available
            else "程向晚在执行其他任务，无法赴约。",
            title="非公开联络答复",
            actor="N18",
            refs=(p["ref"],),
        )
        know(d, "N18", ref, "收到本人约见请求。")
        case(
            d, "K06", "active" if available else "dormant", ref, flags["private_check"]
        )
        return True
    if k == "meeting_evidence":
        d["busy"].pop("N18", None)
        flags["private_check"] = "实际到场"
        ref = ctx.emit(
            schedule_text(d), title="现场核实排期", actor="N18", refs=(p["ref"],)
        )
        visible_doc(
            d,
            "PLAN-r2",
            "南渠工序排期 · 签发版",
            schedule_text(d),
            "N08",
            "当前工序登记",
            version="r2",
            ref=ref,
        )
        f["received_by"].append("player")
        know(d, "N18", ref, "两人实际核对了排期。")
        case(d, "K06", "resolved", ref, "技术员实际出示了手里的版本。")
        ctx.schedule(
            "meeting_disclosed",
            {"ref": ref},
            ctx.duration("message_queue", 15, 70),
            title="现场部门核对来访登记",
            visible=False,
        )
        return True
    if k == "meeting_disclosed":
        ref = ctx.emit(
            "程向晚将本人参与的排期核对登记交给本项目负责人。",
            title="范围内登记",
            actor="N08",
            visible=False,
            refs=(p["ref"],),
        )
        know(d, "N08", ref, "技术员本人参与了本次核实，未披露其他私人谈话。")
        return True
    if k == "audit_delivery":
        f["received_by"].append("N19")
        ref = ctx.emit(
            "董薇依档案权限从水务处取得签发版排期。",
            title="档案复核收件",
            actor="N19",
            refs=(p["ref"], f["revision_ref"]),
        )
        know(d, "N19", ref, schedule_text(d))
        flags["audit_schedule"] = "已核验"
        d["investigation"].setdefault("scheduling_evidence", []).append(
            {"version": "PLAN-r2", "ref": ref, "source": "N08"}
        )
        visible_doc(
            d,
            "AUD-schedule",
            "档案室核查回执",
            "已核验水务处的签发版；该原件仍在原档案处。",
            "N19",
            "本次调阅",
            ref=ref,
        )
        return True
    return False
