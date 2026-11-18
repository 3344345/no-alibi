"""Access, travel, speech, notebook custody and individual schedules."""

from .catalog import DAY, LOCATIONS, PEOPLE
from .world_common import (
    action,
    arc,
    case,
    contact,
    know,
    promise,
    readable,
    start_job,
    text_field,
    visible_doc,
)


def options(d):
    loc = d["location"]
    a = []
    nb = d["notebook"]
    fam = d["family"]
    flags = d["flags"]
    if loc in ("L01", "L07", "L08") and readable(d):
        a.append(
            action(
                "write_note",
                "写入实体记事本",
                "原文随本子保存，失去持有权后不能再调阅。",
                "即时",
                "记事本",
                fields=[text_field("text", "记录原文", limit=1000)],
            )
        )
        source_docs = sorted(
            (doc for doc in d["docs"].values() if not doc["id"].startswith("NB-")),
            key=lambda doc: doc["id"],
        )
        if source_docs:
            choices = [
                {"label": doc["title"], "value": doc["id"]} for doc in source_docs
            ]
            a.append(
                action(
                    "write_sourced_note",
                    "按材料写入笔记",
                    "把可以出示的具体版本和判断性质一并写入实体本。",
                    "即时",
                    "记事本",
                    fields=[
                        text_field("text", "条目正文", limit=1000),
                        {
                            "name": "document",
                            "label": "对照材料",
                            "type": "select",
                            "options": choices,
                            "default": choices[0]["value"],
                            "required": True,
                        },
                        {
                            "name": "classification",
                            "label": "条目性质",
                            "type": "select",
                            "options": [
                                {"label": v, "value": v}
                                for v in ("引用文件", "个人推测", "记下转述")
                            ],
                            "default": "个人推测",
                            "required": True,
                        },
                    ],
                )
            )
        if nb["location"] == "player":
            a.append(
                action(
                    "leave_note",
                    "把记事本留在这里",
                    "同处一地的人以后可能发现它。",
                    "即时",
                    "记事本",
                )
            )
        else:
            a.append(
                action("take_note", "收回记事本", "恢复随身持有。", "即时", "记事本")
            )
        if nb["entries"]:
            a.append(
                action(
                    "copy_note",
                    "制作一份签收副本",
                    "将当前条目复制为独立文件，由档案室签收。",
                    "本人 20 分钟",
                    "记事本",
                )
            )
            a.append(
                action(
                    "destroy_note",
                    "销毁本人持有的原件",
                    "确认后原件永久失去。已经取得的副本仍存在。",
                    "需要再次确认",
                    "记事本",
                )
            )
    if flags.get("destroy_confirm") and readable(d):
        for choice, label in [("yes", "确认销毁原件"), ("no", "保留原件")]:
            a.append(
                action(
                    "confirm_note",
                    label,
                    "仅对本次在场且可访问的原件有效。",
                    "立即",
                    "记事本",
                    {"choice": choice},
                )
            )
    if d["invites"]["L04"] == "待回复":
        for ch, lab in [
            ("yes", "接受晚餐邀请"),
            ("no", "婉拒邀请"),
            ("later", "先婉拒，之后另行到场"),
            ("free", "自行措辞回复"),
        ]:
            a.append(
                action(
                    "invite",
                    lab,
                    "对邀请人的回复与后来实际出席分开登记。",
                    "即时",
                    "人际往来",
                    {"choice": ch},
                    [text_field("text", "回复内容", "我会尽量前来。")]
                    if ch == "free"
                    else [],
                )
            )
    if loc == "L01":
        for key in ("L05", "L06"):
            if d["invites"][key] == "未预约":
                a.append(
                    action(
                        "appointment",
                        "预约" + LOCATIONS[key]["name"] + "会面",
                        "先通过既有联系人联系主办人，等候明确答复。",
                        "联络排队",
                        "人际往来",
                        {"place": key},
                    )
                )
    if loc in ("L04", "L05", "L06", "L09", "L07"):
        for mode, label in [
            ("limited", "只答应了解程序"),
            ("assure", "口头保证结果"),
            ("decline", "说明无法代办"),
        ]:
            if any(x["location"] == loc and x["mode"] == mode for x in d["statements"]):
                continue
            a.append(
                action(
                    "speak",
                    label,
                    "只有邻座听到原话，后续转述取决于实际送达。",
                    "本人 10 分钟",
                    "谈话",
                    {"mode": mode},
                )
            )
        if d["statements"] and not flags.get("clarified"):
            a.append(
                action(
                    "clarify",
                    "书面澄清原话",
                    "写清楚能办到什么，送达后由听者自行判断。",
                    "起草与消息送达",
                    "谈话",
                )
            )
    if loc in ("L04", "L08", "L06", "L05"):
        who = "N13" if loc == "L08" else "N12"
        for mode, label in [
            ("ask", "问建议及其出处"),
            ("verify", "请求核实旧联系人"),
            ("limited", "记下有条件的引荐"),
        ]:
            if flags.get(who + mode):
                continue
            a.append(
                action(
                    "mentor",
                    label,
                    PEOPLE[who]["name"] + "只说自己看过或听过的材料。",
                    "本人 20 分钟",
                    "前辈会面",
                    {"who": who, "mode": mode},
                )
            )
    if loc in ("L07", "L09") and fam["training"] in ("待回复", "改约待定"):
        for mode, label in [
            ("cover", "承担培训期间的照护"),
            ("share", "协商缩短共同空档"),
            ("decline", "说明工作安排冲突"),
        ]:
            a.append(
                action(
                    "family_plan",
                    label,
                    "沈亦宁保留独立决定；接受照护会占用家庭日程。",
                    "协商需 30 分钟",
                    "家庭",
                    {"mode": mode},
                )
            )
    proposal = d.get("social_proposal")
    if proposal and proposal["status"] == "待答复":
        for mode, label in [("accept", "接受限定范围"), ("decline", "保留原回复")]:
            a.append(
                action(
                    "social_offer",
                    label,
                    proposal["text"],
                    "新提议的窗口与原承诺分别记录",
                    "条件协商",
                    {"mode": mode},
                )
            )
    if loc == "L05":
        if not flags.get("gift"):
            a.append(
                action(
                    "gift",
                    "收下交给你的礼盒",
                    "收受与正式拨款分开记录，物品随持有人转移。",
                    "即时",
                    "物品",
                    {"choice": "take"},
                )
            )
            a.append(
                action(
                    "gift",
                    "当面退还礼盒",
                    "在场交还给吕峻生。",
                    "即时",
                    "物品",
                    {"choice": "refuse"},
                )
            )
        if flags.get("gift") == "持有":
            a.append(
                action(
                    "gift",
                    "补办退还交接",
                    "将实物退还并取得对方签收记录。",
                    "即时",
                    "物品",
                    {"choice": "return"},
                )
            )
    if loc in ("L07", "L08", "L01"):
        a.append(
            action(
                "rest",
                "休息一会儿",
                "安排安静休息，恢复状态。日内韧性恢复有上限。",
                "本人 45 分钟",
                "个人日程",
            )
        )
    for pr in d["promises"].values():
        if pr["status"] in ("待履约", "逾期"):
            for mode, label in [
                ("deliver", "办理这项答复"),
                ("revise", "向当事人申请改期"),
            ]:
                a.append(
                    action(
                        "commitment",
                        label + " · " + pr["title"],
                        "按原约定向收件人送达。口头保证不能代替实际批准。",
                        "办理并候回音",
                        "承诺",
                        {"id": pr["id"], "mode": mode},
                    )
                )
    for proc, entry in d["opportunities"].items():
        a.append(
            action(
                "followup",
                entry["title"],
                "利用本次已有联络窗口。",
                "本人 25 分钟",
                "后续联络",
                {"process": proc},
            )
        )
    return a


def act(d, k, p, ctx):
    flags = d["flags"]
    loc = d["location"]
    nb = d["notebook"]
    if k == "social_offer":
        proposal = d["social_proposal"]
        if p["mode"] == "accept":
            proposal["status"] = "接受"
            row = promise(
                d,
                ctx,
                proposal["scope"],
                proposal["who"],
                proposal["service_minutes"],
                kind="limited",
            )
            proposal["commitment"] = row["id"]
        else:
            proposal["status"] = "拒绝"
            ctx.emit(
                "对方收到拒绝，原有安排照常。",
                title="条件回复",
                refs=(proposal["ref"],),
            )
        return True
    if k == "write_sourced_note":
        doc = d["docs"][p["document"]]
        ref = ctx.emit(
            "实体本新增一条带材料版本的记录。", title="记事本", refs=tuple(doc["refs"])
        )
        nb["entries"].append(
            {
                "text": p["text"].strip(),
                "kind": p["classification"],
                "minute": ctx.minute,
                "ref": ref,
                "source_doc": doc["id"],
            }
        )
        return True
    if k == "write_note":
        ref = ctx.emit("新条目已写入随手记事本。", title="记事本")
        nb["entries"].append(
            {
                "text": p["text"].strip(),
                "kind": "个人记录",
                "minute": ctx.minute,
                "ref": ref,
            }
        )
        return True
    if k in ("leave_note", "take_note"):
        nb["location"] = loc if k == "leave_note" else "player"
        flags.pop("destroy_confirm", None)
        ref = ctx.emit(
            "记事本留在" + LOCATIONS[loc]["name"] + "。"
            if k == "leave_note"
            else "记事本已经收回。",
            title="物品交接",
        )
        if k == "leave_note" and nb["entries"] and loc in ("L01", "L07"):
            ctx.schedule(
                "notice_note",
                {"place": loc, "source": ref},
                60,
                title="例行收拾",
                visible=False,
            )
        return True
    if k == "copy_note":
        start_job(
            d,
            ctx,
            k,
            "制作记事本副本",
            20,
            {"location": loc, "count": len(nb["entries"])},
        )
        return True
    if k == "destroy_note":
        flags["destroy_confirm"] = {
            "at": ctx.minute,
            "location": loc,
            "count": len(nb["entries"]),
        }
        ctx.emit("已登记销毁意图。原件仍在，须在原地确认。", title="确认物品处置")
        return True
    if k == "confirm_note":
        tok = flags.pop("destroy_confirm")
        if p["choice"] == "no":
            ctx.emit("撤回销毁意图，原件保留。", title="物品处置")
            return True
        if tok != {"at": ctx.minute, "location": loc, "count": len(nb["entries"])}:
            raise ValueError("原处置确认已失效。")
        nb["location"] = "destroyed"
        nb["entries"] = []
        ref = ctx.emit("本人持有的原件已经销毁。", title="物品处置")
        case(d, "K14", "active", ref, "原件已不可调取，其他材料须另有取得记录。")
        return True
    if k == "invite":
        choice = p["choice"]
        status = {
            "yes": "接受",
            "no": "婉拒",
            "later": "婉拒后赴约",
            "free": "自由回复",
        }[choice]
        d["invites"]["L04"] = status
        ref = ctx.emit(
            p.get(
                "text",
                {
                    "yes": "我会赴约。",
                    "no": "谢谢，这次不去。",
                    "later": "谢谢，这次先不安排。",
                    "free": "",
                }[choice],
            ),
            title="回复邀请",
        )
        if choice == "free":
            d["invites"]["L04"] = (
                "自由赴约"
                if any(x in p["text"] for x in ("参加", "赴约", "前来", "出席"))
                and not any(x in p["text"] for x in ("不", "拒", "没"))
                else "自由回复"
            )
        expressed = p.get("text", status if choice != "later" else "婉拒")
        know(d, "N12", ref, expressed)
        visible_doc(
            d,
            "INVITE-reply",
            "向主办人的邀请回复",
            expressed,
            "本人",
            "实际送出的文字",
            ref=ref,
        )
        return True
    if k == "appointment":
        key = p["place"]
        d["invites"][key] = "已申请"
        ctx.emit(LOCATIONS[key]["name"] + "会面申请已经送达。", title="会面申请")
        ctx.schedule(
            "appointment_reply",
            p,
            ctx.duration("message_queue", 30, 90),
            title="会面申请答复",
        )
        return True
    if k in (
        "speak",
        "mentor",
        "family_plan",
        "rest",
        "followup",
        "clarify",
        "commitment",
    ):
        label = {
            "speak": "当面答复",
            "mentor": "与前辈交谈",
            "family_plan": "家庭日程协商",
            "rest": "安静休息",
            "followup": "后续联络",
            "clarify": "起草澄清说明",
            "commitment": "办理承诺",
        }[k]
        delay = {
            "speak": 10,
            "mentor": 20,
            "family_plan": 30,
            "rest": 45,
            "followup": 25,
            "clarify": 20,
            "commitment": 30,
        }[k]
        start_job(d, ctx, k, label, delay, {**p, "place": loc})
        return True
    if k == "gift":
        choice = p["choice"]
        flags["gift"] = {"take": "持有", "refuse": "当面拒收", "return": "已退还"}[
            choice
        ]
        wording = {
            "take": "吕峻生交给你的礼盒已经随身持有。",
            "refuse": "礼盒仍由吕峻生持有。",
            "return": "礼盒已退回，双方签收。",
        }[choice]
        ref = ctx.emit(wording, title="礼盒交接")
        know(d, "N17", ref, wording)
        from .world_office import adjust

        adjust(
            d,
            "N17",
            ref,
            shared_exposure=0.1 if choice == "take" else 0.0,
            familiarity=0.02,
        )
        if choice in ("take", "return"):
            visible_doc(
                d,
                "GIFT-" + choice,
                "物品交接签收单",
                wording,
                "N17",
                "本次实物交接",
                ref=ref,
            )
        return True
    return False


def counterproposal(d, ctx, who, episode, ref, subject):
    if d.get("social_proposal", {}).get("status") == "待答复":
        return
    seen = d.setdefault("social_episodes", [])
    if episode in seen:
        return
    seen.append(episode)
    base = 0.4 if who == "N14" else 0.3
    from .negotiation import choose_reply

    if choose_reply(ctx, "social/" + episode, base, other="keep") != "counter":
        return
    delay = max(1, round(180 * ctx.params["new_soft_window"]))
    text = PEOPLE[who]["name"] + "提出换个范围：" + subject + "。"
    ref = ctx.emit(text, title="新的有限反提案", actor=who, refs=(ref,))
    d["social_proposal"] = {
        "id": episode,
        "who": who,
        "scope": subject,
        "status": "待答复",
        "ref": ref,
        "text": text,
        "reply_due": ctx.minute + delay,
        "service_minutes": DAY,
    }
    ctx.schedule("social_expire", {"id": episode}, delay, title="有限反提案的答复时限")


def complete(d, k, p, ctx):
    flags = d["flags"]
    nb = d["notebook"]
    fam = d["family"]
    if k == "social_expire":
        proposal = d.get("social_proposal", {})
        if proposal.get("id") == p["id"] and proposal.get("status") == "待答复":
            proposal["status"] = "过期"
            ctx.emit(
                "有限反提案未获答复，当事人没有因此承担新义务。",
                title="答复期结束",
                refs=(proposal["ref"],),
            )
        return True
    if k == "copy_note":
        if not readable(d):
            return True
        rows = nb["entries"][: p["count"]]
        ref = ctx.emit("副本已制作，本人留存一联并将另一联交付传递。", title="制作副本")
        key = "NB-copy-" + str(len(nb["copies"]) + 1)
        body = "\n".join(f"{e['kind']} · {e['text']}" for e in rows)
        nb["copies"].append(
            {"id": key, "entries": list(rows), "ref": ref, "holder": "传递中"}
        )
        visible_doc(
            d,
            key,
            "记事本副本 · 自存联",
            body,
            "本人",
            "本次复制的条目",
            kind="个人记录副本",
            ref=ref,
        )
        delay = ctx.duration("message_queue", 10 if p["location"] == "L01" else 55, 30)
        ctx.schedule(
            "archive_note_receipt",
            {"copy": key, "ref": ref},
            delay,
            title="档案室签收副本",
        )
        return True
    if k == "archive_note_receipt":
        copy = next(row for row in nb["copies"] if row["id"] == p["copy"])
        copy["holder"] = "N19"
        ref = ctx.emit(
            "档案室取得送达的指定副本，原件的物理状态单独记录。",
            title="副本签收",
            actor="N19",
            refs=(p["ref"],),
        )
        copy["receipt"] = ref
        know(d, "N19", ref, d["docs"][p["copy"]]["body"])
        case(d, "K13", "signal", ref, "档案室取得副本，记录性质尚待核实。")
        return True
    if k in ("notice_note", "read_note"):
        if nb["location"] != p["place"] or not nb["entries"]:
            return True
        who = "N10" if p["place"] == "L01" else "N14"
        from .world import present

        if not present(d, who, p["place"]):
            return True
        if k == "notice_note":
            ref = ctx.emit(
                "在桌上看见记事本。",
                title="物品被发现",
                actor=who,
                visible=False,
                refs=(p["source"],),
            )
            ctx.schedule(
                "read_note", {**p, "source": ref}, 30, title="在场整理", visible=False
            )
            return True
        ref = ctx.emit(
            "在实际可接触的位置看见一页手记。",
            title="阅读记录",
            actor=who,
            visible=False,
            refs=(p["source"],),
        )
        know(d, who, ref, nb["entries"][0]["text"])
        ctx.schedule(
            "note_inquiry",
            {"source": ref, "who": who},
            ctx.duration("message_queue", 10, 40),
            title="关于手记的询问",
        )
        return True
    if k == "note_inquiry":
        ref = ctx.emit(
            PEOPLE[p["who"]]["name"] + "询问桌上手记的来源，说自己看到了一页。",
            title="收到询问",
            actor=p["who"],
            refs=(p["source"],),
        )
        visible_doc(
            d,
            "NB-reader-" + p["who"],
            "实际读者的来函",
            "来信人陈述此前在现场看见一页手记，尚未核对其内容。",
            p["who"],
            "亲历者陈述",
            kind="人物陈述",
            ref=ref,
        )
        case(d, "K13", "contested", ref, "实际读者提出询问。")
        return True
    if k == "invite_end":
        if d["location"] != "L04":
            d["invites"]["L04"] = "结束"
            ctx.emit("本次晚餐已结束。之后可再联系主办人。", title="邀请截止")
        return True
    if k == "appointment_reply":
        key = p["place"]
        who = "N03" if key == "L06" else "N12"
        d["invites"][key] = "已预约"
        ctx.emit(
            PEOPLE[who]["name"] + "回复已登记来访，可以按日程前往。",
            title="会面已确认",
            actor=who,
        )
        contact(d, who)
        return True
    if k == "speak":
        place = p["place"]
        who = "N17" if place in ("L04", "L05") else ("N03" if place == "L06" else "N15")
        mode = p["mode"]
        raw = {
            "limited": "我可以问一下程序；材料齐全后再考虑带到会上。",
            "assure": "我保证能把事情办成。",
            "decline": "我无法替你办理，可以自己向窗口询问。",
        }[mode]
        ref = ctx.emit(raw, title="当面原话")
        know(d, who, ref, raw)
        d["statements"].append(
            {
                "location": place,
                "mode": mode,
                "text": raw,
                "ref": ref,
                "audience": [who],
            }
        )
        if mode != "decline":
            promise(
                d,
                ctx,
                "履行当面保证" if mode == "assure" else "向当事人说明办理程序",
                who,
                2 * DAY,
                kind=mode,
            )
        if mode == "assure":
            ctx.schedule(
                "rely_on_speech",
                {"who": who, "source": ref, "promise": "PR" + str(len(d["promises"]))},
                30,
                title="听者准备自己的安排",
                visible=False,
            )
        if mode == "limited":
            counterproposal(d, ctx, who, place + "/" + mode, ref, "只提交一份程序目录")
        ctx.schedule(
            "relay",
            {"source": ref, "from": who, "to": PEOPLE[who]["contact"], "mode": mode},
            ctx.duration("message_queue", 15, 90),
            title="当事人之间的转述",
            visible=False,
        )
        return True
    if k == "rely_on_speech":
        who = p["who"]
        if p["source"] not in d["actors"][who]["beliefs"] or who in d["busy"]:
            return True
        start_job(
            d, ctx, "reliance_followup", "编排申请资料", 90, p, actor=who, visible=False
        )
        return True
    if k == "reliance_followup":
        who = p["who"]
        ref = ctx.emit(
            PEOPLE[who]["name"] + "说已据你的保证安排人手准备资料，现在等正式答复。",
            title="收到依约安排的回函",
            actor=who,
            refs=(p["source"],),
        )
        know(d, who, ref, "已花费时间准备材料，尚未取得正式批准。")
        visible_doc(
            d,
            "SPEECH-reliance-" + p["promise"],
            "依约准备的回函",
            "对方已排时间准备资料，未得到正式批准。",
            who,
            "本次口头保证的实际后果",
            ref=ref,
        )
        case(d, "K02", "active", ref, "实际听者据口头保证排入准备工作。")
        return True
    if k == "relay":
        a = p["from"]
        b = p["to"]
        body = {
            "limited": "对方愿意推进这件事。",
            "assure": "对方担保最后能办成。",
            "decline": "对方没有接下代办。",
        }[p["mode"]]
        if p["source"] not in d["actors"][a]["beliefs"]:
            return True
        ref = ctx.emit(
            body, title="转述送达", actor=a, visible=False, refs=(p["source"],)
        )
        know(d, b, ref, body)
        ctx.schedule(
            "relay_next",
            {
                "from": b,
                "to": "N11" if b == "N14" else "N03",
                "body": body,
                "source": ref,
            },
            ctx.duration("message_queue", 20, 75),
            title="联系人来函",
        )
        return True
    if k == "relay_next":
        who = p["from"]
        peer = p["to"]
        if p["source"] not in d["actors"][who]["beliefs"]:
            return True
        body = "我收到的转述是：" + p["body"]
        ref = ctx.emit(
            body, title="第二次转述送达", actor=who, visible=False, refs=(p["source"],)
        )
        know(d, peer, ref, body)
        ctx.schedule(
            "relay_reply",
            {"from": peer, "body": body, "source": ref},
            ctx.duration("message_queue", 15, 45),
            title="工作联系人的回信",
        )
        return True
    if k == "relay_reply":
        ref = ctx.emit(
            PEOPLE[p["from"]]["name"]
            + "来问：“我听说，"
            + p["body"]
            + "是这个意思吗？”",
            title="收到转述",
            actor=p["from"],
            refs=(p["source"],),
        )
        visible_doc(
            d,
            "RELAY-" + str(len(d["statements"])) + "-" + p["from"],
            "转述询问信",
            p["body"],
            p["from"],
            "当事人收到的版本",
            kind="人物陈述",
            ref=ref,
        )
        case(d, "K11", "contested", ref, "对方的来函与当面原话可以对照。")
        return True
    if k == "clarify":
        statement = d["statements"][-1]
        ref = ctx.emit(
            "澄清只针对已经说过的话。", title="澄清稿寄出", refs=(statement["ref"],)
        )
        flags["clarified"] = True
        ctx.schedule(
            "clarified",
            {"who": statement["audience"][0], "text": statement["text"], "source": ref},
            ctx.duration("message_queue", 15, 40),
            title="澄清签收",
        )
        return True
    if k == "clarified":
        ref = ctx.emit(
            "收件人签收了关于原话的澄清。",
            title="澄清送达",
            actor=p["who"],
            refs=(p["source"],),
        )
        know(d, p["who"], ref, p["text"])
        visible_doc(
            d,
            "CLARIFY-" + str(len(d["statements"])),
            "书面澄清签收联",
            p["text"],
            p["who"],
            "直接签收范围",
            ref=ref,
        )
        case(d, "K11", "resolved", ref, "直接收件人签收；其他人原有说法仍单独保留。")
        return True
    if k == "mentor":
        who = p["who"]
        mode = p["mode"]
        flags[who + mode] = True
        heard = d["actors"][who]["beliefs"].get(
            d["actors"][who].get("belief_topics", {}).get("channel_update"),
            PEOPLE[who]["claim"],
        )
        body = {
            "ask": heard + " 这是我上次接触时听到的。",
            "verify": heard + " 已向办公渠道发出核实请求。",
            "limited": "这次只做引荐，具体资格仍要问负责单位。",
        }[mode]
        ref = ctx.emit(
            PEOPLE[who]["name"] + "：“" + body + "”", title="前辈答复", actor=who
        )
        visible_doc(
            d,
            "advice-" + who + mode,
            "前辈谈话摘录",
            body,
            who,
            "本次会面",
            kind="人物陈述",
            ref=ref,
        )
        case(d, "K12", "active", ref, body)
        if mode == "limited":
            know(d, who, ref, "本人已提供一次限定引荐。")
            ctx.schedule(
                "favour_request",
                {"who": who, "ref": ref},
                ctx.duration("message_queue", 30, 90),
                title="引荐方的来函",
            )
        if who == "N12":
            arc(
                d,
                "V4-ARC04",
                {"ask": "记下旧信源", "verify": "同意查证", "limited": "有条件引荐"}[
                    mode
                ],
                ref,
            )
        if mode == "verify":
            ctx.schedule(
                "mentor_check",
                {"who": who, "ref": ref},
                ctx.duration("message_queue", 30, 90),
                title="联络渠道核查",
            )
        return True
    if k == "mentor_check":
        body = (
            "目前仍由原联络人接件。"
            if not d.get("mentor_change")
            and not d["career"]["transferred"]
            and not d["career"].get("vacancy_ref")
            else "接件人已经变动，请按新的交接名单联系。"
        )
        ref = ctx.emit(body, title="办公室回函", actor="N10", refs=(p["ref"],))
        visible_doc(
            d,
            "D12-check-" + p["who"],
            "当前联络渠道的核查回函",
            body,
            "N10",
            "岗位交接登记",
            ref=ref,
        )
        know(d, p["who"], ref, body, topic="channel_update")
        case(d, "K12", "resolved", ref, body)
        if p["who"] == "N12":
            arc(d, "V4-ARC04", "引荐渠道已核对", ref)
        return True
    if k == "family_plan":
        if fam["training"] not in ("待回复", "改约待定"):
            ctx.emit("协商过程中原回复期已到，请按新日程安排。", title="家庭日程")
            return True
        mode = p["mode"]
        fam["care"] = {
            "cover": "本人承担照护",
            "share": "分时照护",
            "decline": "工作冲突",
        }[mode]
        ref = ctx.emit(
            "沈亦宁记下你的可用时段：" + fam["care"] + "。她将自行回复培训单位。",
            title="家庭协商",
            actor="N14",
        )
        if mode in ("share", "decline"):
            counterproposal(
                d,
                ctx,
                "N14",
                "family/" + str(fam["training_slot"]) + "/" + mode,
                ref,
                "在培训前送交一份照护时段安排",
            )
        arc(d, "V4-ARC03", "比较实际日程", ref)
        case(d, "K15", "active", ref, fam["care"])
        if mode != "decline":
            delay = max(1, fam["training_slot"] - ctx.minute)
            ctx.schedule(
                "care_visit",
                {"duration": 180 if mode == "cover" else 60, "source": ref},
                delay + 60,
                title="已答应的照护时段",
            )
        return True
    if k == "family_enquire":
        ref = ctx.emit(
            "沈亦宁已向培训单位核对集中授课日期，请家里报出能承担的真实时段。",
            title="培训日期回信",
            actor="N14",
        )
        visible_doc(
            d,
            "FAM-dates",
            "培训日期回信",
            "已核对授课日及回复期，家人尚未承诺具体安排。",
            "N14",
            "实际回复期",
            ref=ref,
        )
        arc(d, "V4-ARC03", "核对共同空档", ref)
        return True
    if k == "family_train":
        support = fam["care"] in ("本人承担照护", "分时照护")
        fam["training"] = "已赴外地培训" if support else "自行选择下一期培训"
        ref = ctx.emit(
            "沈亦宁通知家里：" + fam["training"] + "。", title="培训回复", actor="N14"
        )
        visible_doc(
            d,
            "FAM-reply",
            "配偶签收的培训安排",
            fam["training"],
            "N14",
            "本次本人选择",
            ref=ref,
        )
        arc(d, "V4-ARC03", fam["training"], ref)
        case(d, "K15", "resolved" if support else "dormant", ref, fam["training"])
        if support:
            fam["plan_end"] = ctx.minute + 7 * DAY
            ctx.schedule("family_return", {}, 7 * DAY, title="培训回程")
        return True
    if k == "family_return":
        fam["plan_end"] = 0
        fam["training"] = "完成培训返家"
        ref = ctx.emit(
            "沈亦宁已按行程返家，带回自己的培训结业回执。",
            title="家庭行程",
            actor="N14",
        )
        arc(d, "V4-ARC03", "完成独立职业安排", ref)
        return True
    if k == "care_visit":
        if "player" not in d["busy"] and d["location"] == "L07":
            start_job(d, ctx, "care_done", "照护家庭事务", p["duration"])
            return True
        ref = ctx.emit(
            "约定的照护时段到了，你不在可执行的位置或另有安排。家人另找了时间。",
            title="照护冲突",
            refs=(p["source"],),
        )
        case(d, "K16", "signal", ref, "已约照护与工作安排重叠。")
        d["career"]["misses"] += 1
        return True
    if k == "care_done":
        ctx.emit("已履行约定的照护时段。", title="家庭照护")
        return True
    if k == "rest":
        day = ctx.minute // DAY
        if fam["recovered_day"] != day:
            fam.update(recovered_day=day, recovered=0)
        inc = min(4, 12 - fam["recovered"], 100 - fam["resilience"])
        fam["resilience"] += inc
        fam["recovered"] += inc
        fam["fatigue"] = max(0, fam["fatigue"] - 8)
        fam["pressure"] = max(0, fam["pressure"] - 3)
        ctx.emit("休息用去 45 分钟，疲劳缓解。", title="休息结束")
        return True
    if k == "followup":
        proc = p["process"]
        entry = d["opportunities"].pop(proc, None)
        if not entry:
            return True
        flags["followed_" + proc] = True
        if (
            proc == "verification"
            and "D01-detail" not in d["docs"]
            and "N18" not in d["busy"]
        ):
            start_job(
                d,
                ctx,
                "evidence",
                "核查窗口收件",
                ctx.duration("message_queue", 30, 70),
                actor="N18",
            )
        elif proc == "repair":
            for pr in d["promises"].values():
                if pr["status"] == "逾期":
                    pr.update(
                        status="待履约", due=ctx.minute + DAY, version=pr["version"] + 1
                    )
                    ctx.schedule(
                        "promise_due",
                        {"id": pr["id"], "version": pr["version"]},
                        DAY,
                        title=pr["title"] + " · 重议期限",
                    )
                    break
        ref = ctx.emit(
            "已回访本次联络，处理结果记入本次会谈。",
            title=entry["title"],
            refs=(entry["ref"],),
        )
        if proc == "case":
            arc(d, "V4-ARC05", "合作方回访", ref)
        return True
    if k == "commitment":
        pr = d["promises"][p["id"]]
        if p["mode"] == "deliver" and pr["id"] == "PR1":
            from . import world_office

            return world_office.complete(d, "start_channel", {}, ctx)
        if p["mode"] == "revise":
            if pr["version"] >= 3:
                ctx.emit("收件人不接受再次顺延，原有约定仍有效。", title="改约未获同意")
                return True
            pr["version"] += 1
            pr["due"] = ctx.minute + 2 * DAY
            pr["status"] = "待履约"
            ctx.schedule(
                "promise_due",
                {"id": pr["id"], "version": pr["version"]},
                2 * DAY,
                title=pr["title"] + " · 改期",
            )
            ctx.emit("已取得对方同意，答复期限顺延两天。", title="承诺重议")
            return True
        if pr["type"] == "assure" and not (
            d["passage"]["opened"] or any(x["opened"] for x in d["projects"].values())
        ):
            ctx.emit(
                "结果尚未实际交付，本次只能说明进度，原保证仍待履行。",
                title="承诺待履行",
            )
            return True
        pr["status"] = "已履约"
        ref = ctx.emit(
            "向" + PEOPLE[pr["creditor"]]["name"] + "送达：" + pr["title"] + "。",
            title="承诺履行",
            refs=(pr["ref"],),
        )
        know(d, pr["creditor"], ref, pr["title"] + "的答复已收到。")
        from .world_office import adjust

        adjust(d, pr["creditor"], ref, trust=0.06, dependency=0.025)
        visible_doc(
            d,
            "receipt-" + pr["id"],
            pr["title"] + " · 收件联",
            "收件人已取得本次答复，范围以原约定为限。",
            pr["creditor"],
            "本次约定",
            ref=ref,
        )
        d["career"]["deliveries"] += 1
        case(d, "K02", "resolved", ref, pr["title"])
        return True
    if k == "monthly":
        # An employed role has an issued payroll authorisation separate from the project budget.
        salary = (
            min(1_000_000, d["payroll"]["authorized"] - d["payroll"]["paid"])
            if not d["career"].get("suspended")
            else 0
        )
        d["payroll"]["paid"] += salary
        fam["savings"] += salary
        payment = min(600_000, fam["savings"])
        fam["savings"] -= payment
        fam["arrears"] += 600_000 - payment
        ctx.emit(
            f"岗位收入 {salary // 100} 元，支付家庭基础开支 {payment // 100} 元。",
            title="家庭月账",
        )
        ctx.schedule("monthly", {}, 30 * DAY, title="岗位薪酬与家庭账单")
        return True
    return False
