"""Functional-stage maintenance and later review of the original delivery record."""

from .catalog import QUARTER, WAN
from .world_projects import passage_project
from .world_common import action, case, know, visible_doc


def opened(d, ctx, ref):
    segment = d["passage"]
    segment.update(
        open_ref=ref,
        opened_quarter=d["quarter"],
        maintenance_due=False,
        maintenance_receipts=[],
        maintenance_busy=False,
    )
    visible_doc(
        d,
        passage_project()["id"] + "-opening",
        "西段临时通路交接单",
        "技术检查、主管批准、执行方交接分别有据；仅西段开始开放。",
        "N17",
        "临时西段",
        ref=ref,
    )
    ctx.schedule(
        "legacy_review_open", {"ref": ref}, 3 * QUARTER, title="三季度后的西段档案复核"
    )


def on_quarter(d, ctx):
    segment = d["passage"]
    if segment["opened"] and not segment.get("maintenance_busy"):
        segment["maintenance_due"] = True


def options(d):
    a = []
    seg = d["passage"]
    loc = d["location"]
    if (
        seg.get("maintenance_due")
        and not seg.get("maintenance_busy")
        and loc in ("L03", "L02")
    ):
        a.append(
            action(
                "service_passage",
                "安排西段便道维护",
                "专项预留一个工作组，查验已开放设施并留存本周期维护回执。",
                "20 万元／1 组／120 分钟",
                "项目交付",
            )
        )
    review = d.get("legacy_review", {})
    if review.get("status") == "待说明" and loc == "L01":
        for mode, label in [
            ("file", "补交手头维护回执"),
            ("witness", "寻找当时的检查员"),
            ("scope", "说明当年意见的范围"),
        ]:
            if mode == "file" and not seg["maintenance_receipts"]:
                continue
            a.append(
                action(
                    "legacy_review",
                    label,
                    "机构将本次实际取得的材料与原交接记录比对，不以怀疑代替认定。",
                    "档案受理与核查",
                    "旧案复核",
                    {"mode": mode},
                )
            )
    return a


def act(d, k, p, ctx):
    seg = d["passage"]
    if k == "service_passage":
        f = d["fiscal"]
        amount = 20 * WAN
        if (
            amount > f["annual_left"]
            or amount + f["quarter_used"] > 2000 * WAN
            or sum(f["groups"].values()) >= 12
        ):
            raise ValueError("当期资金或维护班组不足。")
        f["annual_left"] -= amount
        f["quarter_used"] += amount
        f["paid"] += amount
        f["groups"]["segment-service"] = 1
        seg.update(maintenance_busy=True, maintenance_due=False)
        ref = ctx.emit("已实际拨付西段维护经费并占用一组人手。", title="西段维护进场")
        ctx.schedule(
            "segment_serviced",
            {"ref": ref, "quarter": d["quarter"]},
            120,
            title="便道维护回执",
        )
        return True
    if k == "legacy_review":
        review = d["legacy_review"]
        review["status"] = "受理中"
        mode = p["mode"]
        refs = [review["intake"]]
        if mode == "file":
            refs += seg["maintenance_receipts"]
        elif mode == "scope":
            refs.append(seg["open_ref"])
        ref = ctx.emit(
            "已送交请求："
            + {
                "file": "查阅维护收件联",
                "witness": "申请询问原检查员",
                "scope": "核查意见适用范围",
            }[mode],
            title="旧案复核请求",
            refs=tuple(refs),
        )
        ctx.schedule(
            "legacy_result",
            {"ref": ref, "mode": mode, "refs": refs[1:]},
            ctx.duration("admin", 60 if mode == "witness" else 30, 90),
            title="旧案复核书面答复",
        )
        return True
    return False


def complete(d, k, p, ctx):
    seg = d["passage"]
    if k == "segment_serviced":
        d["fiscal"]["groups"].pop("segment-service")
        seg["maintenance_busy"] = False
        ref = ctx.emit(
            "班组完成西段巡查和维护，工作组已归还。",
            title="西段维护签收",
            actor="N17",
            refs=(p["ref"],),
        )
        seg["maintenance_receipts"].append(ref)
        visible_doc(
            d,
            passage_project()["id"] + "-maint-" + str(p["quarter"]),
            "西段维护回执 · 第" + str(p["quarter"]) + "季",
            "本周期已经实际巡查并交还工作组。",
            "N17",
            "西段已开放范围",
            ref=ref,
        )
        return True
    if k == "legacy_review_open":
        ref = ctx.emit(
            "档案人员调阅了三季前的原交接单，询问当时开放范围和其后维护记录。",
            title="旧案卷重新调阅",
            actor="N19",
            refs=(p["ref"],),
        )
        d["legacy_review"] = {
            "status": "待说明",
            "intake": ref,
            "acquired": [p["ref"]],
            "claim": "后续维护的来源尚待取得。",
        }
        # Only a copy already obtained by the archivist can join this review.
        # An unrelated notebook or a private original supplies no evidence here.
        project = passage_project()["id"]
        for copy in d["notebook"]["copies"]:
            related = any(
                e.get("source_doc", "").startswith((project + "-opening", project + "-maint-"))
                for e in copy["entries"]
            )
            if copy["holder"] != "N19" or not related:
                continue
            received = copy["receipt"]
            d["legacy_review"]["acquired"].append(received)
            linked = ctx.emit(
                "档案室把已经签收的有关摘录附入复核卷，原始交接和维护材料仍须独立核查。",
                title="旧卷材料关联",
                actor="N19",
                refs=(ref, received),
            )
            case(
                d,
                "K13",
                "active",
                linked,
                "带原件出处的笔记副本已入旧卷，不单独证明维护事实。",
            )
            if d["notebook"]["location"] == "destroyed":
                case(
                    d,
                    "K14",
                    "active",
                    linked,
                    "原件已失去，档案室此前实际取得的副本仍可核。",
                )
        case(d, passage_project()["stage_case"], "active", ref, "原卷被正式调阅，需核对维护责任。")
        return True
    if k == "legacy_result":
        review = d["legacy_review"]
        acquired = review["acquired"]
        acquired.extend(x for x in p["refs"] if x not in acquired)
        mode = p["mode"]
        if mode == "witness":
            if "N18" in d["busy"]:
                review["status"] = "待说明"
                ctx.emit(
                    "原检查员另有任务，未取得新陈述。可改用书面材料。",
                    title="核查待补",
                    refs=(p["ref"],),
                )
                return True
            test = ctx.emit(
                "程向晚查阅自己原签记录，确认检查范围止于西段。",
                title="取得当事人陈述",
                actor="N18",
                refs=(seg["check_ref"],),
            )
            acquired.append(test)
        if mode == "file":
            text = "已取得实际维护回执，相应周期的维护获得佐证，按已核实范围归档。"
            result = "已有维护证据归档"
        elif mode == "witness":
            text = "原检查员证实开放段范围。以后各季的维护仍须独立核实，列作待补事项。"
            result = "开放范围获佐证"
        else:
            text = "原交接单只支持西段当时的开放，机构发出补齐后续维护材料的要求。"
            result = "补件整改"
        ref = ctx.emit(
            "档案室已将实际取得的材料和比对意见送交复核负责人。",
            title="复核卷转交",
            actor="N19",
            refs=(p["ref"], *acquired),
        )
        review["status"] = "待机构签收"
        ctx.schedule(
            "legacy_signoff",
            {"ref": ref, "mode": mode, "text": text, "result": result},
            ctx.duration("message_queue", 15, 25),
            title="复核负责人签收意见",
        )
        return True
    if k == "legacy_signoff":
        review = d["legacy_review"]
        text = p["text"]
        ref = ctx.emit(
            text, title="复核意见", actor="N05", refs=(p["ref"], *review["acquired"])
        )
        know(d, "N05", ref, text)
        review.update(status=p["result"], resolution_ref=ref)
        visible_doc(
            d,
            "LEGACY-result",
            "旧案卷复核意见",
            text,
            "N05",
            "独立取得的原卷及补件",
            kind="制度认定",
            ref=ref,
        )
        case(d, passage_project()["stage_case"], "resolved" if p["mode"] == "file" else "contested", ref, text)
        return True
    return False
