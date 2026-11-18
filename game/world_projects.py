from .catalog import DAY, PROJECTS, WAN
from .world_common import action, arc, case, contact, know, start_job, visible_doc

# Quantities describe a first-stage allocation, in ten thousand yuan and crew slots.
PLANS = {
    "A": {
        "name": "南渠与医院优先",
        "parts": {"P01": (800, 5), "P02": (500, 3), "P03": (700, 4)},
    },
    "B": {
        "name": "道路优先、医院分区",
        "parts": {"P01": (600, 4), "P02": (900, 5), "P03": (500, 3)},
    },
    "C": {"name": "先办南渠一段，保留余量", "parts": {"P01": (400, 3)}},
}
VARIANTS = (
    (
        20,
        "南渠全项目累计已完成 40 个计量单位。",
        "同日分项台账合计 20；另有 20 单位尚未达到完成条件。",
        "同日全项目",
        "工程量清单",
        20,
        40,
    ),
    (
        40,
        "南渠全项目累计已完成 40 个计量单位。",
        "旧巡查表记 20。此后新验收了 20 单位，最新交接单累计 40。",
        "本周全项目",
        "两期签收单",
        40,
        40,
    ),
    (
        20,
        "西段施工标段已完成其计划量的 40%。",
        "西段占总任务一半。西段自身完成 40%，折算全项目为 20 单位。",
        "仅西段合同范围",
        "分段合同附表",
        40,
        40,
    ),
    (
        20,
        "附图所示西段表面铺装已完成。",
        "照片取自西段近端，同一检查点的背面尚有材料未到；照片不覆盖全段。",
        "一张照片的取景范围",
        "带方位的另一张照片",
        100,
        100,
    ),
)


def setup(d, variant):
    v = VARIANTS[variant]
    d["variant"] = {
        "id": f"V4-TV0{variant + 1}",
        "initial_progress": v[0],
        "scope": v[3],
        "scope_progress": v[5],
        "claim_value": v[6],
        "answer": v[2],
        "evidence": v[4],
    }
    d["projects"] = {}
    for key, p in PROJECTS.items():
        d["projects"][key] = {
            "progress": v[0] if key == "P01" else p["initial"],
            "phase": "拟议",
            "permit": key == "P01",
            "stage_share": 0,
            "paid": 0,
            "checked": False,
            "opened": False,
            "maintenance_due": False,
            "report": v[1]
            if key == "P01"
            else f"项目主管报告：当前进度 {p['initial']} 个计量单位。",
            "work_done": False,
            "approvals": [],
            "stage_number": 1,
            "stage_history": [],
        }
    d["passage"] = {
        "built": True,
        "safe": variant != 3,
        "stage": "待申请",
        "opened": False,
        "check_ref": None,
    }
    d["offers"] = []
    d["fiscal"] = {
        "year": 1,
        "annual_left": 8000 * WAN,
        "quarter_used": 0,
        "reserved": 0,
        "paid": 0,
        "groups": {},
    }
    visible_doc(
        d, "D01-r1", "南渠防涝 · 进度简报", v[1], "N08", v[3], date="第1天 · 来文"
    )
    visible_doc(
        d,
        "D01-ledger",
        "南渠巡查 · 前次摘录",
        "上次巡查只记入已核对的 20 个计量单位，摘录未附完整工程量清单。",
        "N18",
        "前次巡查覆盖范围",
        date="上周 · 巡查",
    )
    if variant == 3:
        visible_doc(
            d,
            "P01-photo-east",
            "西段近端 · 简报所附原图",
            "原图边缘保留西段标桩。镜头朝东，只拍到铺装表面，南侧背面在取景范围外。",
            "N08",
            "西段标桩、朝东近端",
            kind="附件照片",
            date="第1天 · 晨间踏查",
        )
    visible_doc(
        d,
        "D16-r1",
        "西段便道通行请求",
        "临时便道能否开放？围挡仍在，社区需要一份可以转达的答复。",
        "N16",
        "西段便道",
    )


def offer_key(d, plan):
    from .balance import digest

    inputs = {
        "plan": plan,
        "quarter": d["quarter"],
        "annual_left": d["fiscal"]["annual_left"],
        "groups": d["fiscal"]["groups"],
        "parts": {
            key: [v["phase"], v["permit"], v["stage_number"]]
            for key, v in d["projects"].items()
        },
    }
    return digest(inputs)


def options(d):
    a = []
    loc = d["location"]
    docs = d["docs"]
    passage = d["passage"]
    if loc == "L01":
        if not d["flags"].get("compare") and "N11" not in d["busy"]:
            a.append(
                action(
                    "delegate",
                    "委托彭述比对附件",
                    "只授权两份材料的日期、统计范围和版本。你可同时赶去现场。",
                    "彭述约 1 小时",
                    "文书查证",
                )
            )
        if not d["flags"].get("compare"):
            a.append(
                action(
                    "compare",
                    "亲自比对两份材料",
                    "查阅简报和前次摘录，分别标记日期与范围。",
                    "本人 25 分钟",
                    "文书查证",
                )
            )
        if d["flags"].get("compare") and "D01-r2" not in docs:
            a.append(
                action(
                    "revise",
                    "出具带范围说明的修订稿",
                    "把已取得的材料逐项列出，原版继续归档。",
                    "本人 30 分钟",
                    "文书查证",
                )
            )
        if not d["flags"].get("hearing"):
            for mode, label, minutes in [
                ("full", "听完整项目汇报", 45),
                ("short", "听关键段落", 15),
                ("skip", "跳过口头汇报", 0),
            ]:
                a.append(
                    action(
                        "report",
                        label,
                        "完整汇报包含来件来源和下一步。跳过时仍可查看已送达文件。",
                        f"{minutes} 分钟",
                        "文书查证",
                        {"mode": mode},
                    )
                )
        if not d["flags"].get("reply"):
            for mode, label in [
                ("conditional", "提交附条件意见"),
                ("defer", "暂缓答复"),
                ("decline", "拒绝认可现有口径"),
            ]:
                a.append(
                    action(
                        "reply",
                        label,
                        "办公室会登记本次答复的准确措辞，并保留旧来文。",
                        "立即登记",
                        "文书查证",
                        {"mode": mode},
                    )
                )
    if loc == "L02" and "OBS-site" not in docs:
        a.append(
            action(
                "observe",
                "沿西段核对现场",
                "在现有通行范围内亲自观察标桩与围挡。",
                "本人 30 分钟",
                "现场核查",
            )
        )
    if loc in ("L01", "L02") and "N18" not in d["busy"]:
        if "D01-detail" not in docs:
            a.append(
                action(
                    "evidence",
                    "请求第二份独立材料",
                    f"向程向晚索取指定检查点的分项记录或其他角度材料。",
                    "技术员核对及送达",
                    "现场核查",
                )
            )
        if passage["stage"] == "待申请":
            a.append(
                action(
                    "passage",
                    "申请检查临时便道",
                    "由程向晚实际检查，符合条件才进入开放审批。",
                    "技术检查 60 分钟及排队",
                    "项目交付",
                    {"step": "inspect"},
                )
            )
    if (
        passage["stage"] in ("检查通过", "待整改")
        and ("N08" if passage["stage"] == "检查通过" else "N17") not in d["busy"]
        and loc in ("L01", "L02")
    ):
        step = "approve" if passage["stage"] == "检查通过" else "repair"
        a.append(
            action(
                "passage",
                "报请批准开放" if step == "approve" else "安排便道整改",
                "提交检查记录，交给具备责任和权限的执行人。",
                "办理后送达",
                "项目交付",
                {"step": step},
            )
        )
    if loc == "L02" and passage["stage"] == "已批准" and "N17" not in d["busy"]:
        a.append(
            action(
                "passage",
                "协调施工方实际开放",
                "吕峻生安排现场人员移交路段，社区收到通知后可以通行。",
                "执行人员 45 分钟",
                "项目交付",
                {"step": "open"},
            )
        )
    if loc in ("L03", "L01"):
        for key, p in d["projects"].items():
            if not p["permit"] and not p.get("permit_pending"):
                a.append(
                    action(
                        "permit",
                        "申请道路前置会签" if key == "P02" else "提交医院分区运营表",
                        "前置环节由项目主管办理，批准经费本身不能代替。",
                        "工作时段审理",
                        "项目协调",
                        {"project": key},
                    )
                )
    if loc == "L03":
        for key, plan in PLANS.items():
            if any(r.get("decision_key") == offer_key(d, key) for r in d["offers"]):
                continue
            if any(d["projects"][pid]["phase"] != "拟议" for pid in plan["parts"]):
                continue
            if any(x["status"] in ("待答复", "待接受") for x in d["offers"]):
                break
            allocation = "；".join(
                f"{PROJECTS[pid]['name']} {amount} 万元／{groups} 组"
                for pid, (amount, groups) in plan["parts"].items()
            )
            a.append(
                action(
                    "propose",
                    f"提交方案 · {plan['name']}",
                    allocation,
                    "等待财政核对，不立即预留",
                    "预算谈判",
                    {"plan": key},
                )
            )
        for row in d["offers"]:
            if row["status"] == "待接受":
                for choice, label in [
                    ("accept", "确认本版条款"),
                    ("withdraw", "撤回这次协调"),
                ]:
                    a.append(
                        action(
                            "offer",
                            label,
                            row["description"],
                            "按本版范围办理",
                            "预算谈判",
                            {"offer": row["id"], "choice": choice},
                        )
                    )
        if not d["flags"].get("cooperate"):
            a.append(
                action(
                    "cooperate",
                    "与蒋绍衡联署道路协调意见",
                    "分担道路会签与资源责任。岗位空缺时仍可能成为竞争者。",
                    "双方 45 分钟",
                    "跨部门协作",
                )
            )
    for key, p in d["projects"].items():
        if p["phase"] == "预留待进场" and loc == "L03":
            a.append(
                action(
                    "cancel_reservation",
                    "撤销尚未进场的预留",
                    PROJECTS[key]["name"] + "返还未用年度额度，释放相应工作组。",
                    "即时",
                    "预算谈判",
                    {"project": key},
                )
            )
        if p["phase"] == "完工待检" and loc in ("L02", "L03"):
            a.append(
                action(
                    "stage_check",
                    "申请阶段验收",
                    PROJECTS[key]["deliverable"] + "需要技术核验和主管批准。",
                    "技术检查",
                    "项目交付",
                    {"project": key},
                )
            )
        if (
            p["opened"]
            and p["phase"] == "阶段开放"
            and p["progress"] < 100
            and loc == "L03"
        ):
            a.append(
                action(
                    "new_phase",
                    "拟订下一阶段 · " + PROJECTS[key]["name"],
                    "另设阶段编号与资源申请。已开放路段与先前责任记录继续保留。",
                    "即时立项草案",
                    "项目交付",
                    {"project": key},
                )
            )
        if p["maintenance_due"] and loc == "L03":
            a.append(
                action(
                    "maintain",
                    "安排设施维护",
                    PROJECTS[key]["name"] + "需要重新占用一组人手和维护经费。",
                    "30 万元，1 组",
                    "项目交付",
                    {"project": key},
                )
            )
    return a


def act(d, k, args, ctx):
    if k in ("delegate", "compare", "revise", "observe", "evidence", "cooperate"):
        if k == "delegate":
            actor, minutes = "N11", ctx.duration("admin", 30, 45)
        elif k == "evidence":
            actor, minutes = "N18", ctx.duration("message_queue", 30, 70)
        else:
            actor, minutes = (
                "player",
                {"compare": 25, "revise": 30, "observe": 30, "cooperate": 45}[k],
            )
        title = {
            "delegate": "联络员材料比对",
            "compare": "比对材料",
            "revise": "编制修订稿",
            "observe": "西段现场踏查",
            "evidence": "请求独立材料",
            "cooperate": "道路协调联署",
        }[k]
        start_job(d, ctx, k, title, minutes, args, actor)
        return True
    if k == "report":
        d["flags"]["hearing"] = args["mode"]
        if args["mode"] == "skip":
            from .world_interop import recovery_after_skipped_report

            recovery_after_skipped_report(d, ctx)
            ctx.emit("口头汇报已跳过，已收文件仍可查阅。", title="汇报安排")
        else:
            start_job(
                d, ctx, k, "听取项目汇报", 45 if args["mode"] == "full" else 15, args
            )
        return True
    if k == "reply":
        mode = args["mode"]
        d["flags"]["reply"] = mode
        text = {
            "conditional": "仅确认收文。工程范围和便道开放条件待现场核对。",
            "defer": "暂缓表态，请保留现有版本并于下一工作时段提醒。",
            "decline": "现有材料不足以确认整项工程量。",
        }[mode]
        ref = ctx.emit(text, title="答复已登记")
        case(d, "K01", "contested" if mode == "decline" else "active", ref, text)
        if mode == "defer":
            ctx.schedule(
                "response_reminder",
                {},
                ctx.duration("admin", 30, 160),
                title="暂缓回复的催办提醒",
            )
        return True
    if k == "passage":
        step = args["step"]
        actor = {"inspect": "N18", "repair": "N17", "approve": "N08", "open": "N17"}[
            step
        ]
        if step == "repair":
            f = d["fiscal"]
            if (
                f["annual_left"] < 20 * WAN
                or f["quarter_used"] + 20 * WAN > 2000 * WAN
                or sum(f["groups"].values()) >= 12
            ):
                raise ValueError("整改需要 20 万元和 1 组空闲人员。")
            f["annual_left"] -= 20 * WAN
            f["quarter_used"] += 20 * WAN
            f["paid"] += 20 * WAN
            f["groups"]["passage"] = 1
        d["passage"]["stage"] = {
            "inspect": "检查中",
            "approve": "审批中",
            "repair": "整改中",
            "open": "交付中",
        }[step]
        if step in ("inspect", "approve"):
            floor, extra = {"inspect": (60, 30), "approve": (20, 80)}[step]
            minutes = ctx.duration("admin", floor, extra)
        else:
            minutes = 120 if step == "repair" else 45
        start_job(d, ctx, "passage_stage", d["passage"]["stage"], minutes, args, actor)
        return True
    if k == "permit":
        key = args["project"]
        d["projects"][key]["permit_pending"] = True
        ctx.emit(PROJECTS[key]["name"] + "前置材料已提交。", title="项目受理")
        ctx.schedule(
            "permit_done",
            args,
            ctx.duration("admin", 60, 150, working=True),
            title="前置手续审理",
        )
        return True
    if k == "propose":
        plan = PLANS[args["plan"]]
        oid = f"OF-{len(d['offers']) + 1}"
        terms = {
            p: {"amount": n * WAN, "groups": g} for p, (n, g) in plan["parts"].items()
        }
        description = "；".join(
            f"{PROJECTS[p]['name']} {t['amount'] // WAN} 万元／{t['groups']} 组"
            for p, t in terms.items()
        )
        ref = ctx.emit(description, title=plan["name"] + " · 首次提案")
        know(d, "N06", ref, description)
        arc(d, "V4-ARC02", "已收到范围明确的分期提案", ref)
        d["offers"].append(
            {
                "id": oid,
                "decision_key": offer_key(d, args["plan"]),
                "name": plan["name"],
                "description": description,
                "terms": terms,
                "status": "待答复",
                "version": 1,
                "ref": ref,
            }
        )
        ctx.schedule(
            "offer_review",
            {"offer": oid},
            ctx.duration("admin", 30, 100),
            title="许慎川答复协调方案",
        )
        return True
    if k == "offer":
        row = next(x for x in d["offers"] if x["id"] == args["offer"])
        f = d["fiscal"]
        if args["choice"] == "withdraw":
            row["status"] = "撤回"
            ctx.emit("撤回协调方案；没有款项因此支付。", title="预算协调")
            return True
        terms = row["terms"]
        amount = sum(v["amount"] for v in terms.values())
        groups = sum(v["groups"] for v in terms.values())
        if (
            amount > f["annual_left"]
            or amount + f["quarter_used"] > 2000 * WAN
            or groups + sum(f["groups"].values()) > 12
        ):
            raise ValueError("当前年度额度、季度上限或人手不足，可撤回重议。")
        if any(d["projects"][p]["phase"] != "拟议" for p in terms):
            raise ValueError("已有其他方案占用该项目，请重新协调。")
        missing = [PROJECTS[p]["name"] for p in terms if not d["projects"][p]["permit"]]
        if missing:
            raise ValueError("尚待前置手续：" + "、".join(missing))
        f["annual_left"] -= amount
        f["reserved"] += amount
        f["quarter_used"] += amount
        for p, t in terms.items():
            f["groups"][p] = t["groups"]
            d["projects"][p].update(
                phase="预留待进场",
                allocation=t["amount"],
                stage_share=t["amount"] / PROJECTS[p]["request"],
                offer=row["id"],
                reserve_quarter=d["quarter"],
                reserve_year=f["year"],
            )
            ctx.schedule(
                "mobilize",
                {"project": p, "offer": row["id"]},
                60,
                title=PROJECTS[p]["name"] + "进场",
            )
        row["status"] = "已接受"
        ref = ctx.emit(
            row["description"], title="财政预留与班组时段已确认", refs=(row["ref"],)
        )
        case(d, "K09", "active", ref, row["description"])
        visible_doc(
            d,
            "BUD-" + row["id"],
            "财政预留确认单",
            row["description"],
            "N06",
            "本次预算与班组",
            ref=ref,
        )
        from .world_interop import settle_round

        settle_round(d, ctx, row, ref)
        arc(d, "V4-ARC02", "阶段分配已签收", ref)
        return True
    if k == "cancel_reservation":
        p = d["projects"][args["project"]]
        f = d["fiscal"]
        amt = p["allocation"]
        if p["reserve_year"] == f["year"]:
            f["annual_left"] += amt
        f["reserved"] -= amt
        if p["reserve_quarter"] == d["quarter"]:
            f["quarter_used"] -= amt
        f["groups"].pop(args["project"])
        p.update(phase="拟议", allocation=0)
        ctx.emit("未进场的资金和班组已释放。", title=PROJECTS[args["project"]]["name"])
        return True
    if k == "stage_check":
        p = d["projects"][args["project"]]
        p["phase"] = "阶段核验中"
        ctx.schedule("project_check", args, 90, title="阶段实际检查")
        ctx.emit("工程完成量已进入检查日程。", title="申请验收")
        return True
    if k == "new_phase":
        key = args["project"]
        proj = d["projects"][key]
        proj["stage_history"].append(
            {
                "id": f"{key}-stage-{proj['stage_number']}",
                "work_ref": proj["work_ref"],
                "approvals": list(proj["approvals"]),
                "paid": proj["allocation"],
                "opened": True,
            }
        )
        proj.update(
            stage_number=proj["stage_number"] + 1,
            phase="拟议",
            work_done=False,
            checked=False,
            approvals=[],
            stage_share=0,
        )
        ref = ctx.emit(
            f"已另立第 {proj['stage_number']} 阶段草案，原阶段通行继续有效。",
            title=PROJECTS[key]["name"],
        )
        case(
            d,
            {"P01": "K03", "P02": "K08", "P03": "K04"}[key],
            "active",
            ref,
            "新阶段草案触发旧事项复核。",
        )
        return True
    if k == "maintain":
        f = d["fiscal"]
        key = args["project"]
        if (
            f["annual_left"] < 30 * WAN
            or f["quarter_used"] + 30 * WAN > 2000 * WAN
            or sum(f["groups"].values()) >= 12
        ):
            raise ValueError("维护需要季度资金与一组空闲人员。")
        f["annual_left"] -= 30 * WAN
        f["quarter_used"] += 30 * WAN
        f["paid"] += 30 * WAN
        f["groups"]["m" + key] = 1
        d["projects"][key]["maintenance_due"] = False
        ctx.schedule("maintenance_done", args, 120, title="设施维护交接")
        ctx.emit("主管已拨付维护费 30 万元并排入班组。", title="维护登记")
        return True
    return False


def complete(d, k, p, ctx):
    def report(key, title, body, actor, scope, kind="文件声称"):
        r = ctx.emit(body, title=title, actor=actor)
        visible_doc(d, key, title, body, actor, scope, kind=kind, ref=r)
        return r

    if k in ("delegate", "compare"):
        body = "前次巡查和本次来文不是同一份统计表。要核实数字，还需按日期、标段和计量单位调取独立记录。"
        ref = report(
            "D01-index",
            "两份材料的日期与范围",
            body,
            "N11" if k == "delegate" else "本人",
            "两份已送达版本",
        )
        d["flags"]["compare"] = True
        case(d, "K01", "active", ref, "日期、范围已注明，等待独立材料。")
        return True
    if k == "revise":
        body = "本稿只引用已收材料。" + (
            d["docs"]["D01-detail"]["body"]
            if "D01-detail" in d["docs"]
            else "无法据此确认累计完成量，建议保留核查。"
        )
        ref = report(
            "D01-r2", "南渠防涝 · 有限核查修订稿", body, "本人", "送达材料范围"
        )
        d["docs"]["D01-r2"]["version"] = "r2"
        case(
            d,
            "K01",
            "resolved" if "D01-detail" in d["docs"] else "contested",
            ref,
            body,
        )
        d["career"]["deliveries"] += 1
        return True
    if k == "report":
        mode = p["mode"]
        body = "梁澈说，简报由项目组汇总，社区来件另列。"
        if mode == "full":
            body += " 程向晚可以按标桩、日期、照片方向逐项提供自己的原始记录。"
        ref = report(
            "D01-brief", "办公室口头汇报摘录", body, "N08", "本次口头汇报", "人物陈述"
        )
        if mode == "full":
            contact(d, "N18")
        return True
    if k == "observe":
        body = "你在西段标桩处看见便道路面与两端围挡。站在这里看不到整个南渠，能否开放仍须检查。"
        ref = report(
            "OBS-site",
            "西段标桩 · 现场观察",
            body,
            "本人",
            "仅本人到达的位置",
            "本人观察",
        )
        case(d, "K03", "active", ref, body)
        contact(d, "N18")
        return True
    if k == "evidence":
        v = d["variant"]
        ref = report("D01-detail", v["evidence"], v["answer"], "N18", v["scope"])
        case(d, "K06", "resolved", ref, "程向晚交来了自己持有的记录。")
        arc(d, "V4-ARC01", "核定独立记录", ref)
        contact(d, "N18")
        return True
    if k == "cooperate":
        ref = ctx.emit(
            "道路组接手会签跟进，你协助汇总资源。两项责任分别写入纪要。",
            title="联署意见",
        )
        d["flags"]["cooperate"] = True
        know(d, "N03", ref, "双方已联署道路会签分工。")
        ctx.schedule(
            "favour_request",
            {"who": "N03", "ref": ref},
            ctx.duration("message_queue", 30, 90),
            title="协作方的来函",
        )
        visible_doc(
            d,
            "D08-division",
            "道路协作责任分工",
            "道路组办理会签，县协调办汇总资源，未形成岗位安排。",
            "N03",
            "双方联署",
            ref=ref,
        )
        arc(d, "V4-ARC05", "两方实际分工", ref)
        case(d, "K08", "active", ref, "双方在道路会签上分担工作。")
        return True
    if k == "response_reminder":
        ref = ctx.emit("周成钧来问上次暂缓的南渠口径可否回复。", title="办公室催办")
        d["flags"].pop("reply", None)
        case(d, "K02", "active", ref, "暂缓事项已到新的回复时点。")
        return True
    if k == "passage_stage":
        passage = d["passage"]
        step = p["step"]
        if step == "inspect":
            passed = passage["safe"] and passage["built"]
            passage["stage"] = "检查通过" if passed else "待整改"
            body = (
                "西段通行条件经现场检查可以提交审批。"
                if passed
                else "检查发现西段护栏尚待收尾；需要班组整改并重新检查。"
            )
            ref = report(
                f"P01-inspect-{len(passage.get('checks', [])) + 1}",
                "临时便道检查记录",
                body,
                "N18",
                "西段便道",
                "检查记录",
            )
            passage["check_ref"] = ref
            passage.setdefault("checks", []).append(ref)
            arc(d, "V4-ARC01", "完成范围内检查", ref)
        elif step == "repair":
            passage.update(safe=True, stage="待申请")
            d["fiscal"]["groups"].pop("passage", None)
            ref = ctx.emit(
                "班组完成护栏整改，需由技术员重新检查。", title="整改完成", actor="N17"
            )
        elif step == "approve":
            if not passage["safe"] or not passage["check_ref"]:
                raise ValueError("缺乏合格检查记录。")
            passage["stage"] = "已批准"
            ref = ctx.emit(
                "水务主管依据本次检查记录批准西段开放，现场仍待执行。",
                title="取得批准",
                actor="N08",
                refs=(passage["check_ref"],),
            )
            passage["approval_ref"] = ref
        else:
            if not passage.get("approval_ref"):
                raise ValueError("缺乏主管批准。")
            passage.update(stage="已开放", opened=True)
            ref = ctx.emit(
                "施工方实际开放了西段便道。社区收到了通行通知，此后办公室到工地的行程缩短 20 分钟。",
                title="西段开始通行",
                actor="N17",
                refs=(passage["approval_ref"],),
            )
            from . import world_maintenance

            world_maintenance.opened(d, ctx, ref)
            d["career"]["deliveries"] += 1
        case(
            d,
            "K03",
            "resolved" if passage["opened"] else "active",
            ref,
            passage["stage"],
        )
        return True
    if k == "permit_done":
        key = p["project"]
        proj = d["projects"][key]
        proj.update(permit=True, permit_pending=False)
        ref = report(
            key + "-permit",
            "前置手续完成 · " + PROJECTS[key]["name"],
            "经责任方核验，分区或会签前置已完成。本件未授予资金。",
            PROJECTS[key]["owner"],
            "首期工序",
        )
        if key == "P03":
            case(d, "K04", "active", ref, "分区运营计划已签收。")
        return True
    if k == "offer_review":
        row = next(x for x in d["offers"] if x["id"] == p["offer"])
        actor = "N06"
        from .negotiation import choose_reply

        if (
            choose_reply(ctx, "fiscal/conditions/" + row["decision_key"], 0.35)
            == "counter"
        ):
            last = next(reversed(row["terms"]))
            t = row["terms"][last]
            t["amount"] -= 50 * WAN
            row["description"] += (
                "。财政反案：" + PROJECTS[last]["name"] + "再缩减 50 万元的工作范围。"
            )
            row["version"] += 1
        row["status"] = "待接受"
        ref = ctx.emit(
            row["description"],
            title=f"协调意见第 {row['version']} 版",
            actor=actor,
            refs=(row["ref"],),
        )
        row["ref"] = ref
        arc(d, "V4-ARC02", "形成可核对的条件方案", ref)
        delay = round(2 * DAY * ctx.params["new_soft_window"])
        row["deadline"] = ctx.minute + delay
        ctx.schedule("offer_expire", {"offer": row["id"]}, delay, title="方案答复期限")
        return True
    if k == "offer_expire":
        row = next(x for x in d["offers"] if x["id"] == p["offer"])
        if row["status"] == "待接受":
            row["status"] = "过期"
            ref = ctx.emit("协调意见到期，没有自动分配资金。", title="协调窗口结束")
            arc(d, "V4-ARC02", "暂缓分配", ref)
        return True
    if k in (
        "mobilize",
        "construction_done",
        "project_check",
        "project_approve",
        "project_open",
        "maintenance_done",
    ):
        key = p["project"]
        proj = d["projects"][key]
        f = d["fiscal"]
        title = PROJECTS[key]["name"]
        if k == "mobilize":
            if proj["phase"] != "预留待进场" or proj["offer"] != p["offer"]:
                return True
            amt = proj["allocation"]
            proj["phase"] = "施工中"
            f["reserved"] -= amt
            f["paid"] += amt
            proj["paid"] += amt
            ctx.emit("资金转为实际支付，已分配班组进场。", title=title)
            ctx.schedule(
                "construction_done",
                p,
                (4 + len(f["groups"])) * DAY,
                title=title + "工序完成",
            )
        elif k == "construction_done":
            if proj["phase"] != "施工中":
                return True
            gain = round((100 - proj["progress"]) * proj["stage_share"])
            proj["progress"] = min(100, proj["progress"] + gain)
            proj.update(phase="完工待检", work_done=True)
            f["groups"].pop(key)
            ref = report(
                f"{key}-stage-{proj['stage_number']}-r1",
                title + " · 工程计量单",
                f"本次已完成 {gain} 个计量单位。实际开放仍须检查、批准及现场交接。",
                PROJECTS[key]["owner"],
                "本次批准的阶段",
            )
            proj["work_ref"] = ref
            arc(d, "V4-ARC02", "已支付并交付计量记录", ref)
        elif k == "project_check":
            proj.update(phase="待主管批准", checked=True)
            ref = ctx.emit(
                "技术员核验本阶段范围，检查记录现已送审。",
                title=title,
                actor="N18",
                refs=(proj["work_ref"],),
            )
            proj["approvals"].append(ref)
            ctx.schedule(
                "project_approve",
                p,
                ctx.duration("admin", 30, 90),
                title=title + "主管核定",
            )
        elif k == "project_approve":
            proj["phase"] = "已批准待开放"
            ref = ctx.emit(
                "主管批准本阶段设施投入使用。",
                title=title,
                actor=PROJECTS[key]["owner"],
                refs=(proj["approvals"][-1],),
            )
            proj["approvals"].append(ref)
            ctx.schedule("project_open", p, 60, title=title + "现场交接")
        elif k == "project_open":
            proj.update(opened=True, phase="阶段开放")
            d["career"]["deliveries"] += 1
            ref = ctx.emit(
                PROJECTS[key]["deliverable"] + "完成交接并投入使用。",
                title=title,
                actor="N17",
                refs=(proj["approvals"][-1],),
            )
            case(
                d,
                {"P01": "K03", "P02": "K08", "P03": "K04"}[key],
                "resolved",
                ref,
                "本阶段设施已经实际交付。",
            )
        else:
            f["groups"].pop("m" + key, None)
            ctx.emit("设施已完成例行维护，班组释放。", title=title)
        return True
    return False
