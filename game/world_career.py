"""Institutional decisions deduced from submitted records and capacity."""

from . import world_institutions as institutions
from .catalog import DAY, ENDINGS, PEOPLE, POSITIONS, STARTS
from .world_common import (
    action,
    arc,
    case,
    contact,
    end_career,
    know,
    start_job,
    visible_doc,
)


def hearing_options():
    return [
        action("hearing", title, detail, "答复后恢复日程", "程序答复", {"mode": mode})
        for mode, title, detail in (
            ("attend", "参加听取意见", "提交在场陈述，核对当前已经调取的材料。"),
            ("written", "递交书面陈述", "仅对已经取得的记录说明范围。"),
            ("waive", "放弃本次陈述", "程序按已有材料继续。"),
        )
    ]


def options(d):
    c = d["career"]
    inv = d["investigation"]
    a = []
    place = d["location"]
    if place != "L01":
        if place == "L07" and c.get("care_required") and not c["handover"]:
            a.append(
                action(
                    "career_exit",
                    "申请照护退出",
                    "备案已有照护需要，交接当前任务。",
                    "岗位交接",
                    "生涯",
                    {"reason": "care"},
                )
            )
        return a
    if not c["handover"]:
        a.extend(
            [
                action(
                    "career_exit",
                    "申请主动离任",
                    "向组织部门递交申请，安排交接后结束本段生涯。",
                    "正式办理",
                    "生涯",
                    {"reason": "leave"},
                ),
                action(
                    "career_exit",
                    "申请横向调任",
                    "完成交接后可以继续任职，旧承诺与文件仍有效。",
                    "正式办理",
                    "生涯",
                    {"reason": "transfer"},
                ),
            ]
        )
        if c.get("care_required"):
            a.append(
                action(
                    "career_exit",
                    "申请照护退出",
                    "提交有来源的家庭照护或健康安排。",
                    "正式办理",
                    "生涯",
                    {"reason": "care"},
                )
            )
        if c.get("duties_since") and d["quarter"] - c["duties_since"] >= 2:
            a.append(
                action(
                    "career_exit",
                    "结束当前边缘岗位生涯",
                    "职责减少已延续至少两季，选择办理阶段交接。",
                    "正式办理",
                    "生涯",
                    {"reason": "marginal"},
                )
            )
    if c["transferred"]:
        a.append(
            action(
                "stage_end",
                "以本次调任收束生涯",
                "保留已提交的交接和调任文件。",
                "结束本阶段",
                "生涯",
                {"id": "END04"},
            )
        )
    if c["vacancy"] and not c["applied"]:
        for route, title in [
            ("self", "提交岗位申请"),
            ("peer", "推荐合作同僚"),
            ("wait", "请求保留观察"),
        ]:
            a.append(
                action(
                    "nominate",
                    title,
                    "资格、正式空缺、考察记录与任命主体分别核验。",
                    "正式考察排队",
                    "组织人事",
                    {"mode": route},
                )
            )
    if (
        c["rank"] >= 2
        and len(d["regional"][str(c["rank"])]["received"]) == 2
        and not c.get("cross_record")
    ):
        a.append(
            action(
                "cross_review",
                "办理跨辖区项目汇总",
                "查阅邻县或邻市已送材料，提交对共用资源的协调意见。",
                "责任人 60 分钟",
                "跨辖区",
                {},
            )
        )
    if inv["status"] in ("无程序", "已归档") and (
        d["notebook"]["copies"] or any(i.startswith("GIFT-") for i in d["docs"])
    ):
        for item in [x["id"] for x in d["notebook"]["copies"]] + [
            i for i in d["docs"] if i.startswith("GIFT-")
        ]:
            if item in inv["acquired"]:
                continue
            a.append(
                action(
                    "refer",
                    "请档案人员核对 · " + d["docs"][item]["title"],
                    "把可出示的指定材料正式递交。笔记推测单独归类。",
                    "材料受理",
                    "材料复核",
                    {"document": item},
                )
            )
    if inv["status"] == "核验中" and not inv.get("requested"):
        for opt, label in [
            ("origin", "申请核对来源"),
            ("context", "附上范围说明"),
            ("close", "请求按现有材料结案"),
        ]:
            a.append(
                action(
                    "review",
                    label,
                    "核对取得链与可用独立材料。能否立案由有权机构判断。",
                    "书面送达",
                    "材料复核",
                    {"mode": opt},
                )
            )
    if inv["status"] == "已作认定":
        for mode, label in [
            ("continue", "继续办理可履行事项"),
            ("file", "收束本次调查程序"),
        ]:
            a.append(
                action(
                    "finding",
                    label,
                    "按已送达程序结论及真实岗位状态处理。",
                    "立即",
                    "材料复核",
                    {"mode": mode},
                )
            )
        if c.get("suspended"):
            a.append(
                action(
                    "finding",
                    "办理处分后的岗位退出",
                    "正式处分和岗位后果均已生效。",
                    "完成交接",
                    "材料复核",
                    {"mode": "exit"},
                )
            )
    return a


def act(d, k, p, ctx):
    c = d["career"]
    inv = d["investigation"]
    if k == "career_exit":
        reason = p["reason"]
        c["handover"] = reason
        ref = ctx.emit("组织部门收到了申请，未结事项列入交接单。", title="申请已送达")
        ctx.schedule(
            "handover",
            {"reason": reason, "ref": ref},
            ctx.duration("admin", 120, 240, working=True),
            title="岗位交接确认",
        )
        return True
    if k == "stage_end":
        end_career(
            d,
            ctx,
            "END04",
            "已选择以调任后的交接记录收束本段生涯。",
            (c["transfer_ref"],),
        )
        return True
    if k == "nominate":
        mode = p["mode"]
        ref = ctx.emit(
            {
                "self": "已提交个人资格材料。",
                "peer": "已正式推荐合作同僚。",
                "wait": "请求继续保留观察。",
            }[mode],
            title="岗位空缺答复",
        )
        c["applied"] = True
        arc(d, "V4-ARC06", "受理候选材料", ref)
        ctx.schedule(
            "appointment_review",
            {"vacancy": c["vacancy"], "mode": mode, "ref": ref},
            ctx.duration("admin", 120, 180, working=True),
            title="组织考察意见",
        )
        return True
    if k == "cross_review":
        start_job(d, ctx, k, "跨辖区备案与协调", 60)
        return True
    if k == "refer":
        key = p["document"]
        doc = d["docs"][key]
        ref = ctx.emit(
            "申请核对指定材料，已取得签收。",
            title=doc["title"],
            refs=tuple(doc["refs"]),
        )
        inv["status"] = "待受理"
        ctx.schedule(
            "acquire",
            {"id": key, "ref": ref},
            ctx.duration("admin", 30, 90),
            title="档案室办理调取",
        )
        return True
    if k == "review":
        ref = ctx.emit("材料复核申请已递交。", title="核查程序")
        inv["requested"] = True
        ctx.schedule(
            "review_done",
            {"mode": p["mode"], "ref": ref},
            ctx.duration("admin", 60, 100),
            title="材料核查答复",
        )
        return True
    if k == "hearing":
        inv["hearing"] = "已答复"
        ref = ctx.emit(
            {
                "attend": "已当面核对取得清单。",
                "written": "书面范围说明已纳入案卷。",
                "waive": "已登记放弃本次陈述。",
            }[p["mode"]],
            title="听取意见",
        )
        ctx.schedule(
            "finding_done",
            {"ref": ref, "mode": p["mode"]},
            ctx.duration("admin", 60, 90),
            title="机构认定送达",
        )
        return True
    if k == "finding":
        mode = p["mode"]
        last = inv["findings"][-1]["ref"]
        if mode == "continue":
            inv["status"] = "已归档"
            ctx.emit(
                "此次程序归档，仍可履行当前获授权的事项。",
                title="程序归档",
                refs=(last,),
            )
            return True
        if mode == "exit" and c.get("suspended"):
            c["handover"] = "discipline"
            ctx.schedule(
                "handover",
                {"reason": "discipline", "ref": last},
                60,
                title="处分后的岗位交接",
            )
            ctx.emit("已依据正式岗位决定开始交接。", title="岗位后果", refs=(last,))
            return True
        end_career(
            d, ctx, "END06", "程序已完成，采用的材料、认定及本人陈述随卷留存。", (last,)
        )
        return True
    return False


def complete(d, k, p, ctx):
    c = d["career"]
    inv = d["investigation"]
    if k == "handover":
        reason = p["reason"]
        if c["handover"] != reason:
            return True
        c["handover"] = None
        ref = ctx.emit(
            "接收人签收了未结承诺、已归档材料和岗位责任清单。",
            title="交接完成",
            refs=(p["ref"],),
        )
        case(d, "K16", "resolved", ref, "责任单由接收方签收。")
        if reason == "transfer":
            c["transferred"] = True
            c["transfer_ref"] = ref
            visible_doc(
                d,
                "HR-transfer-" + str(d["quarter"]),
                "调任交接回执",
                "接收方签收未结责任。旧案继续保留。",
                "N04",
                "本次调任",
                ref=ref,
            )
            c["title"] = "异地" + POSITIONS[c["rank"]][1]
            c["since"] = d["quarter"]
            ctx.emit(
                "调任后可继续办理，亦可在生涯页结束本段。",
                title="调任生效",
                refs=(ref,),
            )
            return True
        key = {
            "leave": "END02",
            "care": "END07",
            "marginal": "END03",
            "retire": "END01",
            "discipline": "END05",
        }[reason]
        c["positions"][POSITIONS[c["rank"]][0]] = None
        c["retired"] = reason == "retire"
        end_career(
            d,
            ctx,
            key,
            ENDINGS[key]["name"] + "手续已完成，个人档案保留原有记录。",
            (ref,),
        )
        return True
    if k == "cross_review":
        rank = c["rank"]
        who = POSITIONS[min(5, rank + 1)][3]
        contact(d, who)
        ref = ctx.emit(
            "已核对本辖区与另一辖区的申请。公共额度不变，标记了需上级协调的重叠工期。",
            title="跨辖区协调回执",
            actor=who,
            refs=tuple(d["regional"][str(rank)]["received"]),
        )
        c["cross_record"] = ref
        c["deliveries"] += 1
        visible_doc(
            d,
            "INTER-" + str(rank),
            "辖区协调回执",
            "共同资源的时段冲突已随汇总上报。",
            who,
            "本次报送的两地摘要",
            ref=ref,
        )
        return True
    if k == "vacancy_close":
        if c["vacancy"] != p["vacancy"] or c["applied"]:
            return True
        ref = ctx.emit(
            "原征询期限届满，组织部门征求其他已有资格者的意见。",
            title="空缺办理",
            actor=p["authority"],
        )
        c["applied"] = True
        ctx.schedule(
            "appointment_review",
            {"vacancy": c["vacancy"], "mode": "peer", "ref": ref},
            60,
            title="其他候选人考察",
        )
        return True
    if k == "appointment_review":
        if c["vacancy"] != p["vacancy"]:
            return True
        idx = c["rank"] + 1
        pos = POSITIONS[idx]
        who = pos[3]
        mode = p["mode"]
        if mode == "wait":
            c["applied"] = False
            ctx.emit("已保留观察意见，空缺仍按原期限办理。", title="人事考察")
            return True
        qualifies = d["quarter"] - c["since"] >= pos[2] and c["deliveries"] >= 2
        if idx >= 2:
            qualifies = qualifies and d["flags"].get("cooperate", False)
        if idx >= 3:
            qualifies = qualifies and bool(c.get("cross_record"))
        body = institutions.authority(d, pos[0])
        if not body:
            c["applied"] = False
            ctx.emit("任命主体暂未取得有效代理授权，此项考察待定。", title="组织程序")
            return True
        alternative = institutions.alternative(d, idx, d["quarter"])
        selected = "player" if qualifies and mode == "self" else alternative
        rival = alternative == "N03" and d["flags"].get("cooperate", False)
        reason = (
            "本人符合任期、交付及岗位核验条件。"
            if selected == "player"
            else "正式推荐或资格复核后，由另一位有任职记录的候选人进入交接。"
        )
        ref = ctx.emit(reason, title="考察完成", actor=who, refs=(p["ref"],))
        arc(d, "V4-ARC06", "形成考察意见", ref)
        if rival:
            arc(d, "V4-ARC05", "进入岗位比较", ref)
        ctx.schedule(
            "appoint",
            {
                "idx": idx,
                "selected": selected,
                "rival": rival,
                "body": body,
                "ref": ref,
                "vacancy": p["vacancy"],
            },
            ctx.duration("admin", 45, 60),
            title="岗位任命交接",
        )
        return True
    if k == "appoint":
        if c["vacancy"] != p["vacancy"]:
            return True
        idx = p["idx"]
        pos = POSITIONS[idx]
        selected = p["selected"]
        prev = POSITIONS[c["rank"]][0]
        if c["positions"][pos[0]] is not None:
            raise ValueError("岗位已由其他人占任。")
        if institutions.authority(d, pos[0]) != p["body"]:
            c["applied"] = False
            ctx.emit("签发前任命授权已变化，原意见不能直接生效。", title="岗位程序")
            return True
        selected = institutions.appoint_person(d, selected, idx, p["ref"], ctx)
        c["positions"][pos[0]] = selected
        ref = ctx.emit(
            institutions.display(d, selected) + "经有效程序接任" + pos[1] + "。",
            title="任命及交接",
            actor=pos[3],
            refs=(p["ref"],),
        )
        if selected == "player":
            c["positions"][prev] = None
            c.update(rank=idx, title=pos[1], since=d["quarter"], cross_record=None)
            contact(d, pos[3])
            from . import world_regional

            world_regional.start(d, idx, ctx, ref)
        else:
            # A known office holder changes roles without inheriting their predecessor's beliefs.
            d["roles"][selected] = pos[1]
            know(d, selected, ref, "已签收本岗位的正式交接材料。")
        c.update(
            vacancy=None,
            applied=False,
            vacate_quarter=d["quarter"] + max(4, 8 if idx >= 2 else 4),
        )
        visible_doc(
            d,
            "POS-" + str(d["quarter"]),
            "任用交接清单",
            institutions.display(d, selected) + "已按正式决定接任。",
            pos[3],
            "本次岗位",
            ref=ref,
        )
        case(d, "K10", "resolved", ref, "任命主体作出决定并完成交接。")
        arc(
            d, "V4-ARC06", "本人接任" if selected == "player" else "其他候选人接任", ref
        )
        if p["rival"]:
            arc(d, "V4-ARC05", "协作者获任" if selected == "N03" else "本人获任", ref)
        return True
    if k == "acquire":
        key = p["id"]
        inv["acquired"].append(key)
        inv.update(status="核验中", requested=False)
        ref = ctx.emit(
            "档案人员按签收联取得了指定材料。材料中的陈述仍须核实。",
            title="材料已入卷",
            actor="N19",
            refs=(p["ref"],),
        )
        know(d, "N19", ref, d["docs"][key]["body"])
        inv["intake_ref"] = ref
        return True
    if k == "review_done":
        gifted = "GIFT-take" in inv["acquired"]
        if p["mode"] == "context":
            ref = ctx.emit(
                "范围说明已附卷，原始材料保留。", title="案卷补充", refs=(p["ref"],)
            )
            inv["requested"] = False
            inv["context"] = ref
            return True
        if not gifted:
            cited = []
            for copy in d["notebook"]["copies"]:
                if copy["id"] not in inv["acquired"]:
                    continue
                for row in copy["entries"]:
                    doc_id = row.get("source_doc")
                    if doc_id in d["docs"]:
                        cited.append(doc_id)
            if cited and p["mode"] == "origin":
                inv["status"] = "补充取证中"
                ctx.schedule(
                    "verify_note_source",
                    {"ids": sorted(set(cited)), "ref": inv["intake_ref"]},
                    ctx.duration("message_queue", 30, 90),
                    title="调取笔记列明的独立来源",
                )
                return True
            inv["status"] = "已归档"
            inv["requested"] = False
            ref = ctx.emit(
                "取得的笔记反映个人记录或推测，现有材料不足以作出岗位处理。",
                title="材料核查归档",
                actor="N05",
                refs=(p["ref"], inv["intake_ref"]),
            )
            case(d, "K13", "resolved", ref, "现有主张未获独立证明。")
            return True
        inv["status"] = "已启动程序"
        inv["requested"] = False
        ref = ctx.emit(
            "签收记录形成可核查线索，机构依程序开案，另向交付方核实。",
            title="核查程序启动",
            actor="N05",
            refs=(inv["intake_ref"],),
        )
        ctx.schedule(
            "witness",
            {"ref": ref},
            ctx.duration("message_queue", 30, 100),
            title="向交付方调取签收记录",
        )
        return True
    if k == "verify_note_source":
        sources = [d["docs"][key] for key in p["ids"] if key in d["docs"]]
        refs = [ref for doc in sources for ref in doc["refs"]]
        ref = ctx.emit(
            "档案室取得原文作了比对。能证实文书确有这些出处，个人判断仍单独保留。",
            title="部分采用来源",
            actor="N19",
            refs=(p["ref"], *refs),
        )
        inv["status"] = "已归档"
        inv["requested"] = False
        inv["acquired"].extend(
            doc["id"] for doc in sources if doc["id"] not in inv["acquired"]
        )
        for doc in sources:
            obtained = ctx.emit(
                "取得指定版本：" + doc["id"],
                title="独立材料入卷",
                actor="N19",
                visible=False,
                refs=(ref, *doc["refs"]),
            )
            know(d, "N19", obtained, doc["body"])
        visible_doc(
            d,
            "NB-ver-" + str(len(inv["acquired"])),
            "笔记出处核查回函",
            "材料的日期和版本已有独立来源；其中的个人推测不构成认定。",
            "N19",
            "此次实际取得的文书",
            ref=ref,
        )
        case(d, "K13", "resolved", ref, "来源部分获独立印证，主张和认定分别记录。")
        return True
    if k == "witness":
        evidence = next(
            (t for t, v in d["actors"]["N17"]["beliefs"].items() if "随身持有" in v),
            None,
        )
        if not evidence:
            inv["status"] = "已归档"
            ctx.emit("交付方未提供能够核实的签收记录。", title="核查归档")
            return True
        ref = ctx.emit(
            "交付方核对了交接时间与签收。",
            title="取得另一方陈述",
            actor="N17",
            refs=(p["ref"], evidence),
        )
        inv["witness_ref"] = ref
        for event, claim in d["actors"]["N17"]["beliefs"].items():
            if "礼盒已退回" in claim:
                inv["return_witness"] = ctx.emit(
                    "交付方同时提交了退还签收的回执。",
                    title="追加取得退回记录",
                    actor="N17",
                    refs=(event, ref),
                )
                if "GIFT-return" not in inv["acquired"]:
                    inv["acquired"].append("GIFT-return")
                break
        ctx.schedule(
            "hearing_due", {"ref": ref}, 120, title="听取本人意见", decision=True
        )
        return True
    if k == "hearing_due":
        inv["hearing"] = "需答复"
        ctx.emit(
            "已到听取意见的约定时段。可到场、提交书面陈述或明确放弃。",
            title="待本人答复",
            refs=(p["ref"],),
        )
        return True
    if k == "finding_done":
        returned = "GIFT-return" in inv["acquired"]
        body = "据签收和双方陈述，认定曾收下礼盒。" + (
            "退回记录已调取，按补办登记处理。"
            if returned
            else "按岗位合同暂停涉此项目的履职，另办岗位交接。"
        )
        refs = [inv["witness_ref"], inv["intake_ref"], p["ref"]]
        if returned:
            refs.append(inv["return_witness"])
        ref = ctx.emit(body, title="书面处理决定", actor="N05", refs=tuple(refs))
        inv["status"] = "已作认定"
        inv["findings"].append({"ref": ref, "text": body})
        if not returned:
            c.update(suspended=True, duties="已暂停相关项目职责")
        visible_doc(
            d,
            "FIND-" + str(len(inv["findings"])),
            "程序处理决定",
            body,
            "N05",
            "本次核对的礼盒交接",
            kind="制度认定",
            ref=ref,
        )
        return True
    if k == "medical":
        if c.get("illness") != "已接到病情通知":
            return True
        # A fictional progression of an already established condition; no violent or self-directed action.
        c["illness"] = "已取得重病变化通知"
        ref = ctx.emit(
            "医疗机构就既有严重疾病送达病情变化通知，个人公务停止。", title="住院交接"
        )
        c["care_required"] = True
        c["suspended"] = True
        if c.get("medical_course") == "不可逆病程":
            ctx.schedule(
                "vital_record", {"ref": ref}, 3 * DAY, title="医院更新病程记录"
            )
        return True
    if k == "vital_record":
        if c.get("illness") != "已取得重病变化通知":
            return True
        c["illness"] = "死亡记录已送达"
        ref = ctx.emit(
            "医疗机构就此前的严重疾病出具了死亡记录。",
            title="病程终止",
            refs=(p["ref"],),
        )
        end_career(
            d,
            ctx,
            "END08",
            "个人行动结束。此前已经提交的项目和履职材料由接收人保管。",
            (ref,),
        )
        return True
    return False


def on_quarter(d, number, ctx):
    c = d["career"]
    p = STARTS[d["start"]]
    c["age"] = p["age"] + (number - 1) // 4
    if c["age"] >= 60 and not c["handover"] and not c.get("suspended"):
        c["handover"] = "retire"
        ref = ctx.emit(
            "本世界任职年龄窗口已满，组织部门安排正式退休交接。", title="退休安排"
        )
        ctx.schedule(
            "handover", {"reason": "retire", "ref": ref}, 120, title="退休岗位交接"
        )
        return
    if (
        c["rank"] + 1 < len(POSITIONS)
        and number >= c["vacate_quarter"]
        and not c["vacancy"]
    ):
        idx = c["rank"] + 1
        pos = POSITIONS[idx]
        former = c["positions"][pos[0]]
        if former is not None:
            c["positions"][pos[0]] = None
            c["departed"] = former
            c["vacancy"] = pos[0]
            c["applied"] = False
            ref = ctx.emit(
                pos[1] + "原持有人已完成任期交接。组织部门现正式征询候选意见。",
                title="岗位出现空缺",
                actor=pos[3],
            )
            c["vacancy_ref"] = ref
            visible_doc(
                d,
                "D10-office-" + str(number),
                "岗位征询材料",
                pos[1] + "已形成实际空缺，等待考察。",
                pos[3],
                "征询期限",
                ref=ref,
            )
            case(d, "K10", "active", ref, "已有空缺，等待有效考察。")
            case(d, "K07", "active", ref, "原联系职责随岗位变动。")
            arc(d, "V4-ARC06", "接到正式空缺通知", ref)
            contact(d, pos[3])
            ctx.schedule(
                "vacancy_close",
                {"vacancy": pos[0], "authority": pos[3]},
                7 * DAY,
                title="空缺候选征询期限",
            )
    if c["misses"] >= 2 and c["duties"] == "正常" and c["deliveries"] == 0:
        c["duties"] = "核心材料转交同事"
        c["duties_since"] = number
        ref = ctx.emit(
            "连续失约后，办公室将核心材料分派给其他联络人。",
            title="职责调整",
            actor="N10",
        )
        case(d, "K16", "active", ref, c["duties"])
    if number == c["health_window"]:
        c["care_required"] = True
        ref = ctx.emit(
            "家庭收到一份长期照护安排，需要重新确定日程。",
            title="家庭照护来件",
            actor="N14",
        )
        visible_doc(
            d,
            "CARE-plan",
            "家庭长期照护安排",
            "家庭已收到照护日程，办理任职交接需另行申请。",
            "N14",
            "家庭收到的安排",
            ref=ref,
        )
        case(d, "K16", "active", ref, "收到长期照护安排。")
        if c["health_profile"]["requires_followup"]:
            c["illness"] = "已接到病情通知"
            c["medical_course"] = (
                "不可逆病程" if c["health_profile"]["irreversible"] else "持续照护"
            )
            ctx.emit(
                "此前的疾病随访已进入正式住院安排，医院约定复查。",
                title="既有病程的随访通知",
            )
            ctx.schedule("medical", {}, 5 * DAY, title="医院复查")
